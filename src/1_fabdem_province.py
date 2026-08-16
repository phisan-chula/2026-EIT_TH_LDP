#!/usr/bin/env python3
"""
FABDEM province clipping and contour mapping.

The workflow uses:
- pandas.DataFrame for province lists and summaries;
- geopandas.GeoDataFrame for GADM polygons and contour lines;
- rasterio for clipping and GeoTIFF output;
- GDAL ContourGenerateEx for scalable contour generation;
- matplotlib for a four-panel PDF report.

Example
-------
python fabdem_province_contours.py \
    --gadm /home/phisan/GeoData/GADM/gadm41_THA.gpkg \
    --province TH.CM \
    --interval 50 \
    --overwrite
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.backends.backend_pdf import PdfPages
from osgeo import gdal, ogr
from rasterio.enums import Resampling
from rasterio.mask import mask


gdal.UseExceptions()
ogr.UseExceptions()


DEFAULT_FABDEM = Path(
    "/home/phisan/GeoData/FABDEM_TH/FABDEM_Thailand.vrt"
)

DEFAULT_GADM_CANDIDATES = (
    Path("./OUTPUT_PROV/gadm41_THA.gpkg"),
)


# =====================================================================
# Configuration and result models
# =====================================================================

@dataclass(frozen=True)
class WorkflowConfig:
    fabdem: Path
    gadm: Path
    province: str
    interval: float = 100.0
    contour_base: float = 0.0
    output_dir: Path = Path("./OUTPUT_FABDEM")
    gadm_layer: Optional[str] = None
    overwrite: bool = False
    all_touched: bool = False
    max_plot_dimension: int = 1800
    max_plot_contours: int = 12_000
    pdf_dpi: int = 200

    def validate(self) -> None:
        if not self.fabdem.exists():
            raise FileNotFoundError(
                f"FABDEM raster/VRT not found: {self.fabdem}"
            )
        if not self.gadm.exists():
            raise FileNotFoundError(
                f"GADM dataset not found: {self.gadm}"
            )
        if not self.province.strip():
            raise ValueError("A HASC_1 province code is required.")
        if self.interval <= 0:
            raise ValueError("Contour interval must be greater than zero.")
        if self.max_plot_dimension < 300:
            raise ValueError("--max-plot-dimension must be at least 300.")
        if self.max_plot_contours < 100:
            raise ValueError("--max-plot-contours must be at least 100.")
        if self.pdf_dpi < 72:
            raise ValueError("--pdf-dpi must be at least 72.")


@dataclass(frozen=True)
class OutputPaths:
    boundary_gpkg: Path
    clipped_dem: Path
    contours_gpkg: Path
    report_pdf: Path
    summary_csv: Path
    summary_json: Path


@dataclass(frozen=True)
class RasterStatistics:
    minimum_m: float
    maximum_m: float
    mean_m: float
    standard_deviation_m: float
    valid_cell_count: int


@dataclass(frozen=True)
class WorkflowResult:
    province_code: str
    province_name: str
    gadm_layer: str
    contour_count: int
    raster_statistics: RasterStatistics
    outputs: OutputPaths


# =====================================================================
# Small utilities
# =====================================================================

class FilePolicy:
    """Centralise output-directory creation and overwrite handling."""

    @staticmethod
    def prepare(path: Path, overwrite: bool) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            return

        if not overwrite:
            raise FileExistsError(
                f"Output already exists: {path}. Use --overwrite."
            )

        if path.is_dir():
            raise IsADirectoryError(
                f"Expected a file but found a directory: {path}"
            )

        path.unlink()


class GeoIO:
    """GeoPandas I/O with a pyogrio-first strategy."""

    @staticmethod
    def read(
        path: Path,
        layer: Optional[str] = None,
        rows: Optional[int] = None,
    ) -> gpd.GeoDataFrame:
        kwargs: dict = {}

        if layer:
            kwargs["layer"] = layer
        if rows is not None:
            kwargs["rows"] = rows

        try:
            return gpd.read_file(
                path,
                engine="pyogrio",
                **kwargs,
            )
        except Exception:
            return gpd.read_file(path, **kwargs)

    @staticmethod
    def write(
        frame: gpd.GeoDataFrame,
        path: Path,
        layer: str,
        overwrite: bool,
    ) -> None:
        FilePolicy.prepare(path, overwrite)

        try:
            frame.to_file(
                path,
                layer=layer,
                driver="GPKG",
                index=False,
                engine="pyogrio",
            )
        except Exception:
            frame.to_file(
                path,
                layer=layer,
                driver="GPKG",
                index=False,
            )


# =====================================================================
# GADM repository
# =====================================================================

class GADMProvinceRepository:
    """Read GADM ADM1 provinces as GeoDataFrames."""

    REQUIRED_CODE_FIELD = "HASC_1"
    NAME_FIELD = "NAME_1"

    def __init__(
        self,
        gadm_path: Path,
        requested_layer: Optional[str] = None,
    ) -> None:
        self.gadm_path = Path(gadm_path)
        self.layer_name = self._resolve_layer(requested_layer)

    def _available_layers(self) -> list[str]:
        if self.gadm_path.suffix.lower() != ".gpkg":
            return [self.gadm_path.stem]

        try:
            import pyogrio

            layer_array = pyogrio.list_layers(self.gadm_path)
            return [str(value) for value in layer_array[:, 0]]
        except Exception:
            try:
                import fiona

                return list(fiona.listlayers(self.gadm_path))
            except Exception as error:
                raise RuntimeError(
                    "Cannot inspect GeoPackage layers. "
                    "Install pyogrio or fiona."
                ) from error

    def _layer_columns(self, layer_name: Optional[str]) -> set[str]:
        preview = GeoIO.read(
            self.gadm_path,
            layer=layer_name,
            rows=1,
        )
        return set(preview.columns)

    def _resolve_layer(
        self,
        requested_layer: Optional[str],
    ) -> Optional[str]:
        if self.gadm_path.suffix.lower() != ".gpkg":
            columns = self._layer_columns(None)
            if self.REQUIRED_CODE_FIELD not in columns:
                raise ValueError(
                    f"{self.gadm_path} does not contain "
                    f"{self.REQUIRED_CODE_FIELD}."
                )
            return None

        layers = self._available_layers()

        if requested_layer:
            if requested_layer not in layers:
                raise ValueError(
                    f"GADM layer '{requested_layer}' was not found. "
                    f"Available layers: {layers}"
                )
            columns = self._layer_columns(requested_layer)
            if self.REQUIRED_CODE_FIELD not in columns:
                raise ValueError(
                    f"Layer '{requested_layer}' does not contain "
                    f"{self.REQUIRED_CODE_FIELD}."
                )
            return requested_layer

        candidates: list[str] = []

        for layer_name in layers:
            try:
                columns = self._layer_columns(layer_name)
            except Exception:
                continue

            if self.REQUIRED_CODE_FIELD in columns:
                candidates.append(layer_name)

        if not candidates:
            raise ValueError(
                f"No layer containing {self.REQUIRED_CODE_FIELD} "
                f"was found in {self.gadm_path}."
            )

        preferred = [
            name
            for name in candidates
            if "ADM_1" in name.upper()
            or "ADM1" in name.upper()
            or name.upper().endswith("_1")
        ]
        return preferred[0] if preferred else candidates[0]

    def read_all(self) -> gpd.GeoDataFrame:
        frame = GeoIO.read(
            self.gadm_path,
            layer=self.layer_name,
        )

        if self.REQUIRED_CODE_FIELD not in frame.columns:
            raise ValueError(
                f"GADM layer does not contain {self.REQUIRED_CODE_FIELD}."
            )
        if frame.crs is None:
            raise ValueError("The GADM layer has no CRS.")

        frame = frame.copy()
        frame[self.REQUIRED_CODE_FIELD] = (
            frame[self.REQUIRED_CODE_FIELD]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        if self.NAME_FIELD not in frame.columns:
            frame[self.NAME_FIELD] = frame[self.REQUIRED_CODE_FIELD]
        else:
            frame[self.NAME_FIELD] = (
                frame[self.NAME_FIELD]
                .fillna(frame[self.REQUIRED_CODE_FIELD])
                .astype(str)
                .str.strip()
            )

        return frame

    def province_table(self) -> pd.DataFrame:
        frame = self.read_all()

        table = (
            frame[
                [
                    self.REQUIRED_CODE_FIELD,
                    self.NAME_FIELD,
                ]
            ]
            .drop_duplicates()
            .query(f"{self.REQUIRED_CODE_FIELD} != ''")
            .sort_values(self.REQUIRED_CODE_FIELD)
            .reset_index(drop=True)
        )

        return pd.DataFrame(table)

    def select(self, province_code: str) -> gpd.GeoDataFrame:
        wanted = province_code.strip().upper()
        frame = self.read_all()

        selected = frame[
            frame[self.REQUIRED_CODE_FIELD]
            .str.upper()
            .eq(wanted)
        ][
            [
                self.REQUIRED_CODE_FIELD,
                self.NAME_FIELD,
                "geometry",
            ]
        ].copy()

        if selected.empty:
            examples = (
                self.province_table()[self.REQUIRED_CODE_FIELD]
                .head(20)
                .tolist()
            )
            raise KeyError(
                f"HASC_1 '{province_code}' was not found. "
                f"Example codes: {examples}"
            )

        selected = selected[
            selected.geometry.notna()
            & ~selected.geometry.is_empty
        ].copy()

        if selected.empty:
            raise ValueError(
                f"Province '{province_code}' has no valid geometry."
            )

        # Merge all polygon parts for the selected province.
        selected = selected.dissolve(
            by=[
                self.REQUIRED_CODE_FIELD,
                self.NAME_FIELD,
            ],
            as_index=False,
        )

        return gpd.GeoDataFrame(
            selected,
            geometry="geometry",
            crs=frame.crs,
        )


# =====================================================================
# Raster clipping
# =====================================================================

class FABDEMClipper:
    """Clip the input DEM using a province GeoDataFrame."""

    OUTPUT_NODATA = -9999.0

    def clip(
        self,
        source_path: Path,
        province_gdf: gpd.GeoDataFrame,
        output_path: Path,
        overwrite: bool,
        all_touched: bool,
    ) -> gpd.GeoDataFrame:
        FilePolicy.prepare(output_path, overwrite)

        with rasterio.open(source_path) as source:
            if source.crs is None:
                raise ValueError(
                    f"FABDEM has no CRS: {source_path}"
                )
            if source.count < 1:
                raise ValueError(
                    f"FABDEM has no raster band: {source_path}"
                )

            province_in_raster_crs = province_gdf.to_crs(source.crs)

            geometries = [
                geometry.__geo_interface__
                for geometry in province_in_raster_crs.geometry
                if geometry is not None and not geometry.is_empty
            ]

            if not geometries:
                raise ValueError(
                    "No valid province geometry is available for clipping."
                )

            clipped, clipped_transform = mask(
                source,
                geometries,
                crop=True,
                all_touched=all_touched,
                nodata=self.OUTPUT_NODATA,
                filled=True,
                indexes=1,
            )

            if clipped.ndim != 2:
                raise RuntimeError(
                    f"Expected a two-dimensional DEM; got {clipped.shape}."
                )

            profile = source.profile.copy()
            profile.update(
                driver="GTiff",
                count=1,
                dtype="float32",
                width=clipped.shape[1],
                height=clipped.shape[0],
                transform=clipped_transform,
                nodata=self.OUTPUT_NODATA,
                compress="deflate",
                predictor=3,
                tiled=True,
                BIGTIFF="IF_SAFER",
            )

            clipped = clipped.astype(np.float32)

        with rasterio.open(
            output_path,
            "w",
            **profile,
        ) as destination:
            destination.write(clipped, 1)

        return province_in_raster_crs


# =====================================================================
# Contour generation
# =====================================================================

class GDALContourGeoDataFrameGenerator:
    """
    Generate full-resolution contours with GDAL ContourGenerateEx,
    then return them as a GeoDataFrame.

    This avoids the legacy gdal.ContourGenerate positional-signature
    problem that can raise: "not a sequence".
    """

    TEMP_LAYER_NAME = "contours"

    @staticmethod
    def _create_temporary_contour_dataset(
        dem_path: Path,
        temporary_gpkg: Path,
        interval: float,
        base: float,
    ) -> None:
        raster = gdal.Open(str(dem_path), gdal.GA_ReadOnly)
        if raster is None:
            raise RuntimeError(f"GDAL cannot open DEM: {dem_path}")

        vector = None

        try:
            band = raster.GetRasterBand(1)
            if band is None:
                raise RuntimeError("DEM band 1 is unavailable.")

            driver = ogr.GetDriverByName("GPKG")
            if driver is None:
                raise RuntimeError(
                    "The GDAL GeoPackage driver is unavailable."
                )

            vector = driver.CreateDataSource(str(temporary_gpkg))
            if vector is None:
                raise RuntimeError(
                    f"Cannot create temporary GeoPackage: {temporary_gpkg}"
                )

            spatial_reference = None
            projection = raster.GetProjection()

            if projection:
                from osgeo import osr

                spatial_reference = osr.SpatialReference()
                spatial_reference.ImportFromWkt(projection)
                spatial_reference.SetAxisMappingStrategy(
                    osr.OAMS_TRADITIONAL_GIS_ORDER
                )

            layer = vector.CreateLayer(
                GDALContourGeoDataFrameGenerator.TEMP_LAYER_NAME,
                srs=spatial_reference,
                geom_type=ogr.wkbLineString,
            )
            if layer is None:
                raise RuntimeError("Cannot create the contour layer.")

            id_field = ogr.FieldDefn("ID", ogr.OFTInteger64)
            elevation_field = ogr.FieldDefn("ELEV_M", ogr.OFTReal)
            elevation_field.SetWidth(16)
            elevation_field.SetPrecision(3)

            if layer.CreateField(id_field) != ogr.OGRERR_NONE:
                raise RuntimeError("Cannot create contour ID field.")
            if layer.CreateField(elevation_field) != ogr.OGRERR_NONE:
                raise RuntimeError(
                    "Cannot create contour elevation field."
                )

            nodata = band.GetNoDataValue()

            options = [
                f"LEVEL_INTERVAL={float(interval):.15g}",
                f"LEVEL_BASE={float(base):.15g}",
                "ID_FIELD=0",
                "ELEV_FIELD=1",
            ]

            if nodata is not None:
                options.append(f"NODATA={float(nodata):.15g}")

            result = gdal.ContourGenerateEx(
                band,
                layer,
                options=options,
            )

            if result != gdal.CE_None:
                raise RuntimeError(
                    "gdal.ContourGenerateEx failed with "
                    f"error code {result}."
                )

            layer.SyncToDisk()
        finally:
            vector = None
            raster = None

    def generate(
        self,
        dem_path: Path,
        province_gdf: gpd.GeoDataFrame,
        output_path: Path,
        interval: float,
        base: float,
        overwrite: bool,
    ) -> gpd.GeoDataFrame:
        FilePolicy.prepare(output_path, overwrite)

        with tempfile.TemporaryDirectory(
            prefix="fabdem_contours_"
        ) as temporary_directory:
            temporary_gpkg = (
                Path(temporary_directory) / "raw_contours.gpkg"
            )

            self._create_temporary_contour_dataset(
                dem_path,
                temporary_gpkg,
                interval,
                base,
            )

            contours = GeoIO.read(
                temporary_gpkg,
                layer=self.TEMP_LAYER_NAME,
            )

        if contours.crs is None:
            with rasterio.open(dem_path) as source:
                contours = contours.set_crs(source.crs)

        province_code = str(
            province_gdf.iloc[0]["HASC_1"]
        )
        province_name = str(
            province_gdf.iloc[0]["NAME_1"]
        )

        contours = contours.copy()
        contours["HASC_1"] = province_code
        contours["NAME_1"] = province_name
        contours["INTERVAL_M"] = float(interval)

        ordered_columns = [
            "ID",
            "ELEV_M",
            "HASC_1",
            "NAME_1",
            "INTERVAL_M",
            "geometry",
        ]

        contours = gpd.GeoDataFrame(
            contours[ordered_columns],
            geometry="geometry",
            crs=contours.crs,
        )

        GeoIO.write(
            contours,
            output_path,
            layer="contours",
            overwrite=False,
        )

        return contours


# =====================================================================
# Raster statistics
# =====================================================================

class RasterStatisticsReader:
    @staticmethod
    def read(dem_path: Path) -> RasterStatistics:
        with rasterio.open(dem_path) as source:
            elevation = source.read(1, masked=True)

        elevation = np.ma.masked_invalid(elevation)
        values = elevation.compressed()

        if values.size == 0:
            raise ValueError(
                "The clipped FABDEM contains no valid elevation cells."
            )

        return RasterStatistics(
            minimum_m=float(values.min()),
            maximum_m=float(values.max()),
            mean_m=float(values.mean()),
            standard_deviation_m=float(values.std()),
            valid_cell_count=int(values.size),
        )


# =====================================================================
# PDF report
# =====================================================================

class ProvincePDFReport:
    """Create a single-page PDF with four subplots."""

    def __init__(
        self,
        max_plot_dimension: int,
        max_plot_contours: int,
        pdf_dpi: int,
    ) -> None:
        self.max_plot_dimension = max_plot_dimension
        self.max_plot_contours = max_plot_contours
        self.pdf_dpi = pdf_dpi

    def _read_plot_dem(
        self,
        dem_path: Path,
    ) -> tuple[
        np.ma.MaskedArray,
        tuple[float, float, float, float],
        rasterio.crs.CRS,
    ]:
        with rasterio.open(dem_path) as source:
            scale = min(
                1.0,
                self.max_plot_dimension
                / max(source.width, source.height),
            )
            output_width = max(
                2,
                int(round(source.width * scale)),
            )
            output_height = max(
                2,
                int(round(source.height * scale)),
            )

            elevation = source.read(
                1,
                out_shape=(output_height, output_width),
                resampling=Resampling.bilinear,
                masked=True,
            )

            bounds = source.bounds
            extent = (
                bounds.left,
                bounds.right,
                bounds.bottom,
                bounds.top,
            )

            return (
                np.ma.masked_invalid(elevation),
                extent,
                source.crs,
            )

    @staticmethod
    def _hillshade(
        elevation: np.ma.MaskedArray,
        extent: tuple[float, float, float, float],
        crs,
        azimuth_degrees: float = 315.0,
        altitude_degrees: float = 45.0,
    ) -> np.ma.MaskedArray:
        xmin, xmax, ymin, ymax = extent
        rows, columns = elevation.shape

        x_resolution = abs(
            (xmax - xmin) / max(columns, 1)
        )
        y_resolution = abs(
            (ymax - ymin) / max(rows, 1)
        )

        if crs and crs.is_geographic:
            centre_latitude = (ymin + ymax) / 2.0
            x_resolution *= (
                111_320.0
                * math.cos(math.radians(centre_latitude))
            )
            y_resolution *= 110_574.0

        valid = elevation.compressed()
        fill_value = (
            float(np.median(valid))
            if valid.size
            else 0.0
        )
        z = elevation.filled(fill_value).astype(float)

        dz_dy, dz_dx = np.gradient(
            z,
            max(y_resolution, 1e-9),
            max(x_resolution, 1e-9),
        )

        slope = np.pi / 2.0 - np.arctan(
            np.hypot(dz_dx, dz_dy)
        )
        aspect = np.arctan2(-dz_dx, dz_dy)

        azimuth = math.radians(azimuth_degrees)
        altitude = math.radians(altitude_degrees)

        shade = (
            math.sin(altitude) * np.sin(slope)
            + math.cos(altitude)
            * np.cos(slope)
            * np.cos(azimuth - aspect)
        )

        shade = (
            shade - np.nanmin(shade)
        ) / (
            np.nanmax(shade)
            - np.nanmin(shade)
            + 1e-12
        )

        return np.ma.array(
            shade,
            mask=np.ma.getmaskarray(elevation),
        )

    def _contours_for_plot(
        self,
        contours: gpd.GeoDataFrame,
    ) -> gpd.GeoDataFrame:
        if len(contours) <= self.max_plot_contours:
            return contours

        indexes = np.linspace(
            0,
            len(contours) - 1,
            self.max_plot_contours,
            dtype=int,
        )
        return contours.iloc[indexes].copy()

    @staticmethod
    def _format_map_axis(axis: plt.Axes) -> None:
        axis.set_aspect("equal", adjustable="box")
        axis.grid(True, linewidth=0.3, alpha=0.35)
        axis.tick_params(labelsize=8)
        axis.set_xlabel("X / Longitude")
        axis.set_ylabel("Y / Latitude")

    def write(
        self,
        dem_path: Path,
        province_gdf: gpd.GeoDataFrame,
        contours_gdf: gpd.GeoDataFrame,
        statistics: RasterStatistics,
        interval: float,
        output_path: Path,
        overwrite: bool,
    ) -> None:
        FilePolicy.prepare(output_path, overwrite)

        elevation, extent, raster_crs = self._read_plot_dem(
            dem_path
        )

        province_plot = province_gdf.to_crs(raster_crs)
        contours_plot = self._contours_for_plot(
            contours_gdf.to_crs(raster_crs)
        )
        hillshade = self._hillshade(
            elevation,
            extent,
            raster_crs,
        )

        province_code = str(
            province_gdf.iloc[0]["HASC_1"]
        )
        province_name = str(
            province_gdf.iloc[0]["NAME_1"]
        )

        figure, axes = plt.subplots(
            2,
            2,
            figsize=(16.5, 11.7),
            constrained_layout=True,
        )

        figure.suptitle(
            (
                f"FABDEM elevation and contours — "
                f"{province_name} ({province_code})"
            ),
            fontsize=18,
            fontweight="bold",
        )

        # Panel A: clipped DEM
        axis = axes[0, 0]
        dem_image = axis.imshow(
            elevation,
            extent=extent,
            origin="upper",
            cmap="terrain",
            interpolation="nearest",
        )
        province_plot.boundary.plot(
            ax=axis,
            color="black",
            linewidth=1.1,
        )
        axis.set_title("A. Province-clipped FABDEM")
        self._format_map_axis(axis)

        colour_bar = figure.colorbar(
            dem_image,
            ax=axis,
            shrink=0.82,
            pad=0.02,
        )
        colour_bar.set_label("Elevation (m)")

        # Panel B: hillshade
        axis = axes[0, 1]
        axis.imshow(
            hillshade,
            extent=extent,
            origin="upper",
            cmap="gray",
            vmin=0,
            vmax=1,
            interpolation="nearest",
        )
        province_plot.boundary.plot(
            ax=axis,
            color="black",
            linewidth=1.1,
        )
        axis.set_title(
            "B. Analytical hillshade "
            "(azimuth 315°, altitude 45°)"
        )
        self._format_map_axis(axis)

        # Panel C: contour GeoDataFrame
        axis = axes[1, 0]
        axis.imshow(
            elevation,
            extent=extent,
            origin="upper",
            cmap="terrain",
            alpha=0.67,
            interpolation="nearest",
        )

        if not contours_plot.empty:
            contours_plot.plot(
                ax=axis,
                color="black",
                linewidth=0.42,
            )

        province_plot.boundary.plot(
            ax=axis,
            color="black",
            linewidth=1.2,
        )
        axis.set_title(
            f"C. Contours — interval {interval:g} m"
        )
        self._format_map_axis(axis)

        # Panel D: histogram and statistics
        axis = axes[1, 1]
        values = elevation.compressed()

        axis.hist(
            values,
            bins=40,
            edgecolor="black",
            linewidth=0.35,
        )
        axis.axvline(
            statistics.mean_m,
            linestyle="--",
            linewidth=1.4,
            label=f"Mean = {statistics.mean_m:.1f} m",
        )
        axis.set_title("D. Elevation distribution and summary")
        axis.set_xlabel("Elevation (m)")
        axis.set_ylabel("Plot-sample pixel count")
        axis.grid(
            True,
            axis="y",
            linewidth=0.3,
            alpha=0.35,
        )
        axis.legend(loc="upper right")

        summary_text = (
            f"Province: {province_name}\n"
            f"HASC_1: {province_code}\n"
            f"Minimum: {statistics.minimum_m:.2f} m\n"
            f"Maximum: {statistics.maximum_m:.2f} m\n"
            f"Mean: {statistics.mean_m:.2f} m\n"
            f"Standard deviation: "
            f"{statistics.standard_deviation_m:.2f} m\n"
            f"Contour interval: {interval:g} m\n"
            f"Contour features: {len(contours_gdf):,}"
        )

        axis.text(
            0.98,
            0.96,
            summary_text,
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=10,
            bbox={
                "boxstyle": "round,pad=0.5",
                "facecolor": "white",
                "alpha": 0.88,
                "edgecolor": "0.45",
            },
        )

        metadata = {
            "Title": (
                f"FABDEM contours — "
                f"{province_name} ({province_code})"
            ),
            "Author": "FABDEM Province Contour Workflow",
            "Subject": (
                "FABDEM clipped by a GADM HASC_1 province "
                "and converted to vector contours"
            ),
            "Keywords": (
                "FABDEM, GADM, GeoDataFrame, HASC_1, contours"
            ),
        }

        with PdfPages(
            output_path,
            metadata=metadata,
        ) as pdf:
            pdf.savefig(
                figure,
                dpi=self.pdf_dpi,
                bbox_inches="tight",
            )

        plt.close(figure)


# =====================================================================
# Workflow orchestration
# =====================================================================

class FABDEMProvinceWorkflow:
    """Orchestrate the complete processing workflow."""

    def __init__(self, config: WorkflowConfig) -> None:
        config.validate()

        self.config = config
        self.repository = GADMProvinceRepository(
            config.gadm,
            config.gadm_layer,
        )
        self.clipper = FABDEMClipper()
        self.contour_generator = (
            GDALContourGeoDataFrameGenerator()
        )
        self.statistics_reader = RasterStatisticsReader()
        self.pdf_report = ProvincePDFReport(
            max_plot_dimension=config.max_plot_dimension,
            max_plot_contours=config.max_plot_contours,
            pdf_dpi=config.pdf_dpi,
        )

    @staticmethod
    def _safe_code(code: str) -> str:
        """Convert a logical HASC code to a safe filesystem code.
        Example: 'TH.CM' -> 'TH_CM'
        """
        return code.strip().upper().replace(".", "_")

    def _output_paths(
        self,
        province_code: str,
    ) -> OutputPaths:
        code = self._safe_code(province_code)

        output_dir = (self.config.output_dir / code).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        interval_text = (
            f"{self.config.interval:g}"
            .replace(".", "p")
        )

        return OutputPaths(
            boundary_gpkg=output_dir / f"{code}_boundary.gpkg",
            clipped_dem=output_dir / f"{code}_fabdem.tif",
            contours_gpkg=(
                output_dir
                / f"{code}_contours_{interval_text}m.gpkg"
            ),
            report_pdf=(
                output_dir / f"{code}_fabdem_contours.pdf"
            ),
            summary_csv=output_dir / f"{code}_summary.csv",
            summary_json=output_dir / f"{code}_summary.json",
        )

    def run(self) -> WorkflowResult:
        print(
            f"[1/5] Read GADM and select "
            f"HASC_1={self.config.province}"
        )
        province_gdf = self.repository.select(
            self.config.province
        )

        province_code = str(
            province_gdf.iloc[0]["HASC_1"]
        )
        province_name = str(
            province_gdf.iloc[0]["NAME_1"]
        )
        outputs = self._output_paths(province_code)

        print("[2/5] Save province and clip FABDEM")
        GeoIO.write(
            province_gdf,
            outputs.boundary_gpkg,
            layer="province",
            overwrite=self.config.overwrite,
        )
        province_raster_crs = self.clipper.clip(
            self.config.fabdem,
            province_gdf,
            outputs.clipped_dem,
            overwrite=self.config.overwrite,
            all_touched=self.config.all_touched,
        )

        print(
            f"[3/5] Generate contours every "
            f"{self.config.interval:g} m "
            f"with GDAL {gdal.VersionInfo('RELEASE_NAME')}"
        )
        contours_gdf = self.contour_generator.generate(
            dem_path=outputs.clipped_dem,
            province_gdf=province_raster_crs,
            output_path=outputs.contours_gpkg,
            interval=self.config.interval,
            base=self.config.contour_base,
            overwrite=self.config.overwrite,
        )

        print("[4/5] Calculate statistics and write PDF")
        statistics = self.statistics_reader.read(
            outputs.clipped_dem
        )
        self.pdf_report.write(
            dem_path=outputs.clipped_dem,
            province_gdf=province_raster_crs,
            contours_gdf=contours_gdf,
            statistics=statistics,
            interval=self.config.interval,
            output_path=outputs.report_pdf,
            overwrite=self.config.overwrite,
        )

        print("[5/5] Write DataFrame summaries")
        result = WorkflowResult(
            province_code=province_code,
            province_name=province_name,
            gadm_layer=(
                self.repository.layer_name
                or self.config.gadm.stem
            ),
            contour_count=len(contours_gdf),
            raster_statistics=statistics,
            outputs=outputs,
        )
        self._write_summary(result)

        return result

    def _summary_dataframe(
        self,
        result: WorkflowResult,
    ) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "HASC_1": result.province_code,
                    "NAME_1": result.province_name,
                    "gadm_layer": result.gadm_layer,
                    "contour_interval_m": self.config.interval,
                    "contour_base_m": self.config.contour_base,
                    "minimum_elevation_m": (
                        result.raster_statistics.minimum_m
                    ),
                    "maximum_elevation_m": (
                        result.raster_statistics.maximum_m
                    ),
                    "mean_elevation_m": (
                        result.raster_statistics.mean_m
                    ),
                    "standard_deviation_m": (
                        result.raster_statistics
                        .standard_deviation_m
                    ),
                    "valid_dem_cell_count": (
                        result.raster_statistics.valid_cell_count
                    ),
                    "contour_feature_count": (
                        result.contour_count
                    ),
                    "boundary_gpkg": str(
                        result.outputs.boundary_gpkg
                    ),
                    "clipped_dem": str(
                        result.outputs.clipped_dem
                    ),
                    "contours_gpkg": str(
                        result.outputs.contours_gpkg
                    ),
                    "report_pdf": str(
                        result.outputs.report_pdf
                    ),
                }
            ]
        )

    def _write_summary(
        self,
        result: WorkflowResult,
    ) -> None:
        summary_df = self._summary_dataframe(result)

        FilePolicy.prepare(
            result.outputs.summary_csv,
            self.config.overwrite,
        )
        summary_df.to_csv(
            result.outputs.summary_csv,
            index=False,
        )

        FilePolicy.prepare(
            result.outputs.summary_json,
            self.config.overwrite,
        )
        result.outputs.summary_json.write_text(
            json.dumps(
                {
                    "configuration": {
                        **asdict(self.config),
                        "fabdem": str(self.config.fabdem),
                        "gadm": str(self.config.gadm),
                        "output_dir": str(
                            self.config.output_dir
                        ),
                    },
                    "result": {
                        "province_code": result.province_code,
                        "province_name": result.province_name,
                        "gadm_layer": result.gadm_layer,
                        "contour_count": result.contour_count,
                        "raster_statistics": asdict(
                            result.raster_statistics
                        ),
                        "outputs": {
                            key: str(value)
                            for key, value in asdict(
                                result.outputs
                            ).items()
                        },
                    },
                },
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )


# =====================================================================
# Command-line interface
# =====================================================================

def resolve_gadm_path(
    requested_path: Optional[str],
) -> Path:
    if requested_path:
        return Path(requested_path).expanduser()

    for candidate in DEFAULT_GADM_CANDIDATES:
        if candidate.exists():
            return candidate

    checked = "\n".join(
        f"  - {candidate}"
        for candidate in DEFAULT_GADM_CANDIDATES
    )
    raise FileNotFoundError(
        "No default GADM dataset was found. "
        "Supply --gadm PATH.\n"
        f"Checked:\n{checked}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            "Select a GADM ADM1 province by HASC_1, clip FABDEM, "
            "generate contours, and write GeoPackage, GeoTIFF, "
            "DataFrame summaries, and a four-panel PDF."
        ),
    )

    parser.add_argument(
        "-p",
        "--province",
        help="GADM HASC_1 code, for example TH.CM.",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=100.0,
        help="Contour interval in metres.",
    )
    parser.add_argument(
        "--base",
        type=float,
        default=0.0,
        help="Contour base elevation in metres.",
    )
    parser.add_argument(
        "--fabdem",
        default=str(DEFAULT_FABDEM),
        help="FABDEM raster or VRT path.",
    )
    parser.add_argument(
        "--gadm",
        help="GADM GeoPackage or shapefile path.",
    )
    parser.add_argument(
        "--gadm-layer",
        help=(
            "GADM ADM1 layer name. When omitted, the layer "
            "containing HASC_1 is detected automatically."
        ),
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="./OUTPUT_FABDEM",
        help="Output directory.",
    )
    parser.add_argument(
        "--list-provinces",
        action="store_true",
        help="Print the HASC_1 and NAME_1 DataFrame, then exit.",
    )
    parser.add_argument(
        "--all-touched",
        action="store_true",
        help="Include every DEM cell touched by the province polygon.",
    )
    parser.add_argument(
        "--max-plot-dimension",
        type=int,
        default=1800,
        help="Maximum raster width or height embedded in the PDF.",
    )
    parser.add_argument(
        "--max-plot-contours",
        type=int,
        default=12_000,
        help="Maximum contour features drawn in the PDF.",
    )
    parser.add_argument(
        "--pdf-dpi",
        type=int,
        default=200,
        help="PDF raster resolution.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing output files.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        gadm_path = resolve_gadm_path(args.gadm)
        repository = GADMProvinceRepository(
            gadm_path,
            args.gadm_layer,
        )

        if args.list_provinces:
            province_df = repository.province_table()
            print(province_df.to_string(index=False))
            print(f"\nTotal provinces: {len(province_df)}")
            return 0

        if not args.province:
            parser.error(
                "-p/--province is required unless "
                "--list-provinces is used."
            )

        config = WorkflowConfig(
            fabdem=Path(args.fabdem).expanduser(),
            gadm=gadm_path,
            province=args.province,
            interval=args.interval,
            contour_base=args.base,
            output_dir=Path(args.output_dir).expanduser(),
            gadm_layer=args.gadm_layer,
            overwrite=args.overwrite,
            all_touched=args.all_touched,
            max_plot_dimension=args.max_plot_dimension,
            max_plot_contours=args.max_plot_contours,
            pdf_dpi=args.pdf_dpi,
        )

        result = FABDEMProvinceWorkflow(config).run()

        print("\nCompleted successfully.")
        print(
            pd.DataFrame(
                [
                    {
                        "HASC_1": result.province_code,
                        "NAME_1": result.province_name,
                        "contours": result.contour_count,
                        "PDF": result.outputs.report_pdf,
                    }
                ]
            ).to_string(index=False)
        )
        return 0

    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
