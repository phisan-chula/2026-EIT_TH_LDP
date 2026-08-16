#!/usr/bin/env python3
"""
Clip the Thailand 2025 population grid by a GADM ADM1 province.

Default population raster
-------------------------
DATA/tha_pop_2025_CN_100m_R2025A_v1.tif

Default output directory
------------------------
POP2025/

Main workflow
-------------
1. Read GADM ADM1 as a GeoDataFrame.
2. Select a province by HASC_1 with -p/--province.
3. Reproject the province polygon to the raster CRS.
4. Cut out the population grid without resampling.
5. Save the clipped GeoTIFF, boundary GeoPackage, PDF map,
   summary CSV, and summary JSON.

No contour generation is performed.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
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
from rasterio.enums import Resampling
from rasterio.mask import mask


DEFAULT_POPULATION_GRID = Path(
    "DATA/tha_pop_2025_CN_100m_R2025A_v1.tif"
)

DEFAULT_OUTPUT_DIR = Path("OUTPUT_POP2025")

DEFAULT_GADM_CANDIDATES = (
    Path("./OUTPUT_PROV/gadm41_THA.gpkg"),
)


# =====================================================================
# Models
# =====================================================================

@dataclass(frozen=True)
class WorkflowConfig:
    population_grid: Path
    gadm: Path
    province: str
    output_dir: Path = DEFAULT_OUTPUT_DIR
    gadm_layer: Optional[str] = None
    overwrite: bool = False
    all_touched: bool = False
    write_pdf: bool = True
    max_plot_dimension: int = 1800
    pdf_dpi: int = 200

    def validate(self) -> None:
        if not self.population_grid.exists():
            raise FileNotFoundError(
                "Population grid not found: "
                f"{self.population_grid}"
            )
        if not self.gadm.exists():
            raise FileNotFoundError(
                f"GADM dataset not found: {self.gadm}"
            )
        if not self.province.strip():
            raise ValueError("A HASC_1 province code is required.")
        if self.max_plot_dimension < 300:
            raise ValueError(
                "--max-plot-dimension must be at least 300."
            )
        if self.pdf_dpi < 72:
            raise ValueError("--pdf-dpi must be at least 72.")


@dataclass(frozen=True)
class OutputPaths:
    boundary_gpkg: Path
    clipped_grid: Path
    report_pdf: Path
    summary_csv: Path
    summary_json: Path


@dataclass(frozen=True)
class PopulationStatistics:
    total_population: float
    valid_cell_count: int
    occupied_cell_count: int
    zero_cell_count: int
    minimum_cell_value: float
    maximum_cell_value: float
    mean_cell_value: float
    median_cell_value: float
    standard_deviation: float
    raster_width: int
    raster_height: int
    pixel_size_x: float
    pixel_size_y: float
    raster_crs: str


@dataclass(frozen=True)
class WorkflowResult:
    province_code: str
    province_name: str
    gadm_layer: str
    statistics: PopulationStatistics
    outputs: OutputPaths


# =====================================================================
# File and vector I/O
# =====================================================================

class FilePolicy:
    @staticmethod
    def prepare(path: Path, overwrite: bool) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            return

        if not overwrite:
            raise FileExistsError(
                f"Output already exists: {path}. "
                "Use --overwrite."
            )

        if path.is_dir():
            raise IsADirectoryError(
                f"Expected a file but found a directory: {path}"
            )

        path.unlink()


class GeoIO:
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
# GADM province repository
# =====================================================================

class GADMProvinceRepository:
    CODE_FIELD = "HASC_1"
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

            layers = pyogrio.list_layers(self.gadm_path)
            return [str(name) for name in layers[:, 0]]
        except Exception:
            try:
                import fiona

                return list(fiona.listlayers(self.gadm_path))
            except Exception as error:
                raise RuntimeError(
                    "Cannot inspect GeoPackage layers. "
                    "Install pyogrio or fiona."
                ) from error

    def _columns(self, layer_name: Optional[str]) -> set[str]:
        frame = GeoIO.read(
            self.gadm_path,
            layer=layer_name,
            rows=1,
        )
        return set(frame.columns)

    def _resolve_layer(
        self,
        requested_layer: Optional[str],
    ) -> Optional[str]:
        if self.gadm_path.suffix.lower() != ".gpkg":
            if self.CODE_FIELD not in self._columns(None):
                raise ValueError(
                    f"{self.gadm_path} does not contain "
                    f"{self.CODE_FIELD}."
                )
            return None

        layers = self._available_layers()

        if requested_layer:
            if requested_layer not in layers:
                raise ValueError(
                    f"Layer '{requested_layer}' not found. "
                    f"Available layers: {layers}"
                )
            if self.CODE_FIELD not in self._columns(
                requested_layer
            ):
                raise ValueError(
                    f"Layer '{requested_layer}' does not contain "
                    f"{self.CODE_FIELD}."
                )
            return requested_layer

        candidates: list[str] = []

        for layer_name in layers:
            try:
                columns = self._columns(layer_name)
            except Exception:
                continue

            if self.CODE_FIELD in columns:
                candidates.append(layer_name)

        if not candidates:
            raise ValueError(
                f"No layer containing {self.CODE_FIELD} "
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

        if self.CODE_FIELD not in frame.columns:
            raise ValueError(
                f"GADM layer does not contain {self.CODE_FIELD}."
            )
        if frame.crs is None:
            raise ValueError("The GADM layer has no CRS.")

        frame = frame.copy()
        frame[self.CODE_FIELD] = (
            frame[self.CODE_FIELD]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        if self.NAME_FIELD not in frame.columns:
            frame[self.NAME_FIELD] = frame[self.CODE_FIELD]
        else:
            frame[self.NAME_FIELD] = (
                frame[self.NAME_FIELD]
                .fillna(frame[self.CODE_FIELD])
                .astype(str)
                .str.strip()
            )

        return frame

    def province_table(self) -> pd.DataFrame:
        frame = self.read_all()

        return pd.DataFrame(
            frame[
                [
                    self.CODE_FIELD,
                    self.NAME_FIELD,
                ]
            ]
            .drop_duplicates()
            .query(f"{self.CODE_FIELD} != ''")
            .sort_values(self.CODE_FIELD)
            .reset_index(drop=True)
        )

    def select(self, province_code: str) -> gpd.GeoDataFrame:
        wanted = province_code.strip().upper()
        frame = self.read_all()

        selected = frame[
            frame[self.CODE_FIELD]
            .str.upper()
            .eq(wanted)
        ][
            [
                self.CODE_FIELD,
                self.NAME_FIELD,
                "geometry",
            ]
        ].copy()

        if selected.empty:
            examples = (
                self.province_table()[self.CODE_FIELD]
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

        selected = selected.dissolve(
            by=[self.CODE_FIELD, self.NAME_FIELD],
            as_index=False,
        )

        return gpd.GeoDataFrame(
            selected,
            geometry="geometry",
            crs=frame.crs,
        )


# =====================================================================
# Population raster clipping
# =====================================================================

class PopulationGridClipper:
    """
    Clip the source population grid without resampling.

    Pixel values are copied directly from the source raster. This is
    important when cell values represent population counts.
    """

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
                    f"Population grid has no CRS: {source_path}"
                )
            if source.count < 1:
                raise ValueError(
                    f"Population grid has no raster band: "
                    f"{source_path}"
                )

            province_raster_crs = province_gdf.to_crs(
                source.crs
            )

            geometries = [
                geometry.__geo_interface__
                for geometry in province_raster_crs.geometry
                if geometry is not None and not geometry.is_empty
            ]

            if not geometries:
                raise ValueError(
                    "No valid province geometry is available "
                    "for clipping."
                )

            source_nodata = source.nodata
            output_nodata = (
                source_nodata
                if source_nodata is not None
                else self._default_nodata(source.dtypes[0])
            )

            clipped, clipped_transform = mask(
                source,
                geometries,
                crop=True,
                all_touched=all_touched,
                nodata=output_nodata,
                filled=True,
                indexes=1,
            )

            if clipped.ndim != 2:
                raise RuntimeError(
                    f"Expected a two-dimensional grid; "
                    f"got {clipped.shape}."
                )

            profile = source.profile.copy()
            profile.update(
                driver="GTiff",
                count=1,
                width=clipped.shape[1],
                height=clipped.shape[0],
                transform=clipped_transform,
                nodata=output_nodata,
                compress="deflate",
                predictor=(
                    3
                    if np.issubdtype(
                        np.dtype(source.dtypes[0]),
                        np.floating,
                    )
                    else 2
                ),
                tiled=True,
                BIGTIFF="IF_SAFER",
            )

        with rasterio.open(
            output_path,
            "w",
            **profile,
        ) as destination:
            destination.write(clipped, 1)

        return province_raster_crs

    @staticmethod
    def _default_nodata(dtype_name: str):
        dtype = np.dtype(dtype_name)

        if np.issubdtype(dtype, np.floating):
            return -9999.0
        if np.issubdtype(dtype, np.signedinteger):
            return np.iinfo(dtype).min
        if np.issubdtype(dtype, np.unsignedinteger):
            return np.iinfo(dtype).max

        raise TypeError(
            f"Unsupported raster dtype for nodata: {dtype_name}"
        )


# =====================================================================
# Statistics
# =====================================================================

class PopulationStatisticsReader:
    @staticmethod
    def read(
        clipped_grid: Path,
    ) -> PopulationStatistics:
        with rasterio.open(clipped_grid) as source:
            values = source.read(1, masked=True)
            transform = source.transform
            crs = source.crs
            width = source.width
            height = source.height

        values = np.ma.masked_invalid(values)
        valid = values.compressed().astype(np.float64)

        if valid.size == 0:
            raise ValueError(
                "The clipped population grid has no valid cells."
            )

        # Population grids occasionally contain tiny negative values
        # due to processing. They are not included in the population sum.
        population_values = np.where(valid > 0, valid, 0.0)

        occupied = int(np.count_nonzero(population_values > 0))
        zero_count = int(valid.size - occupied)

        return PopulationStatistics(
            total_population=float(population_values.sum()),
            valid_cell_count=int(valid.size),
            occupied_cell_count=occupied,
            zero_cell_count=zero_count,
            minimum_cell_value=float(valid.min()),
            maximum_cell_value=float(valid.max()),
            mean_cell_value=float(valid.mean()),
            median_cell_value=float(np.median(valid)),
            standard_deviation=float(valid.std()),
            raster_width=int(width),
            raster_height=int(height),
            pixel_size_x=float(abs(transform.a)),
            pixel_size_y=float(abs(transform.e)),
            raster_crs=str(crs),
        )


# =====================================================================
# PDF report
# =====================================================================

class PopulationGridPDFReport:
    """
    Create a PDF containing population-grid maps and statistics.

    No contour layer is created or plotted.
    """

    def __init__(
        self,
        max_plot_dimension: int,
        pdf_dpi: int,
    ) -> None:
        self.max_plot_dimension = max_plot_dimension
        self.pdf_dpi = pdf_dpi

    def _read_plot_grid(
        self,
        grid_path: Path,
    ) -> tuple[
        np.ma.MaskedArray,
        tuple[float, float, float, float],
        rasterio.crs.CRS,
    ]:
        with rasterio.open(grid_path) as source:
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

            # Nearest-neighbour resampling is used only for display.
            # The saved GeoTIFF remains unchanged.
            grid = source.read(
                1,
                out_shape=(output_height, output_width),
                resampling=Resampling.nearest,
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
                np.ma.masked_invalid(grid),
                extent,
                source.crs,
            )

    @staticmethod
    def _format_map_axis(axis: plt.Axes) -> None:
        axis.set_aspect("equal", adjustable="box")
        axis.grid(True, linewidth=0.3, alpha=0.35)
        axis.tick_params(labelsize=8)
        axis.set_xlabel("X / Longitude")
        axis.set_ylabel("Y / Latitude")

    def write(
        self,
        clipped_grid: Path,
        province_gdf: gpd.GeoDataFrame,
        statistics: PopulationStatistics,
        output_path: Path,
        overwrite: bool,
    ) -> None:
        FilePolicy.prepare(output_path, overwrite)

        grid, extent, raster_crs = self._read_plot_grid(
            clipped_grid
        )
        province_plot = province_gdf.to_crs(raster_crs)

        province_code = str(
            province_gdf.iloc[0]["HASC_1"]
        )
        province_name = str(
            province_gdf.iloc[0]["NAME_1"]
        )

        positive = np.ma.masked_less_equal(grid, 0)
        log_grid = np.ma.array(
            np.log1p(positive.filled(0.0)),
                mask=np.ma.getmaskarray(positive),
            )

        figure, axes = plt.subplots(
            2,
            2,
            figsize=(16.5, 11.7),
            constrained_layout=True,
        )

        figure.suptitle(
            (
                f"Thailand population grid 2025 — "
                f"{province_name} ({province_code})"
            ),
            fontsize=18,
            fontweight="bold",
        )

        # A. Original population grid
        axis = axes[0, 0]
        image = axis.imshow(
            positive,
            extent=extent,
            origin="upper",
            cmap="viridis",
            interpolation="nearest",
        )
        province_plot.boundary.plot(
            ax=axis,
            color="black",
            linewidth=1.1,
        )
        axis.set_title("A. Population grid — original cell values")
        self._format_map_axis(axis)

        colour_bar = figure.colorbar(
            image,
            ax=axis,
            shrink=0.82,
            pad=0.02,
        )
        colour_bar.set_label("Population per grid cell")

        # B. Logarithmic display
        axis = axes[0, 1]
        log_image = axis.imshow(
            log_grid,
            extent=extent,
            origin="upper",
            cmap="viridis",
            interpolation="nearest",
        )
        province_plot.boundary.plot(
            ax=axis,
            color="black",
            linewidth=1.1,
        )
        axis.set_title("B. Population grid — log(1 + population)")
        self._format_map_axis(axis)

        log_colour_bar = figure.colorbar(
            log_image,
            ax=axis,
            shrink=0.82,
            pad=0.02,
        )
        log_colour_bar.set_label("log(1 + population)")

        # C. Distribution of occupied cells
        axis = axes[1, 0]
        positive_values = positive.compressed().astype(float)

        if positive_values.size:
            min_val = positive_values.min()
            max_val = positive_values.max()
            log_bins = np.logspace(np.log10(min_val), np.log10(max_val), 50)
            
            axis.hist(
                positive_values,
                bins=log_bins,
                edgecolor="black",
                linewidth=0.3,
            )
            axis.set_xscale("log")
            
            # Formatter removed here to allow default math symbols (10^x)
            axis.tick_params(axis='x', rotation=45)

        axis.set_title(
            "C. Distribution of populated grid cells"
        )
        axis.set_xlabel(
            "Population per occupied cell — logarithmic axis"
        )
        axis.set_ylabel("Cell count")
        axis.grid(
            True,
            axis="y",
            linewidth=0.3,
            alpha=0.35,
        )

        # D. Summary
        axis = axes[1, 1]
        axis.axis("off")

        summary_text = (
            f"Province: {province_name}\n"
            f"HASC_1: {province_code}\n\n"
            f"Estimated population sum:\n"
            f"{statistics.total_population:,.0f}\n\n"
            f"Valid cells: "
            f"{statistics.valid_cell_count:,}\n"
            f"Occupied cells: "
            f"{statistics.occupied_cell_count:,}\n"
            f"Zero cells: "
            f"{statistics.zero_cell_count:,}\n\n"
            f"Maximum cell value: "
            f"{statistics.maximum_cell_value:,.2f}\n"
            f"Mean cell value: "
            f"{statistics.mean_cell_value:,.4f}\n"
            f"Median cell value: "
            f"{statistics.median_cell_value:,.4f}\n\n"
            f"Raster size: "
            f"{statistics.raster_width:,} × "
            f"{statistics.raster_height:,} cells\n"
            f"Pixel size: "
            f"{statistics.pixel_size_x:g} × "
            f"{statistics.pixel_size_y:g}\n"
            f"CRS: {statistics.raster_crs}"
        )

        axis.text(
            0.05,
            0.95,
            summary_text,
            transform=axis.transAxes,
            ha="left",
            va="top",
            fontsize=12,
            bbox={
                "boxstyle": "round,pad=0.7",
                "facecolor": "white",
                "edgecolor": "0.45",
            },
        )

        metadata = {
            "Title": (
                f"Population grid 2025 — "
                f"{province_name} ({province_code})"
            ),
            "Author": "Population Grid Province Workflow",
            "Subject": (
                "Thailand 2025 population grid clipped "
                "by a GADM HASC_1 province"
            ),
            "Keywords": (
                "population grid, GADM, GeoDataFrame, HASC_1"
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
# Workflow
# =====================================================================

class PopulationProvinceWorkflow:
    def __init__(self, config: WorkflowConfig) -> None:
        config.validate()

        self.config = config
        self.repository = GADMProvinceRepository(
            config.gadm,
            config.gadm_layer,
        )
        self.clipper = PopulationGridClipper()
        self.statistics_reader = PopulationStatisticsReader()
        self.pdf_report = PopulationGridPDFReport(
            config.max_plot_dimension,
            config.pdf_dpi,
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
        
        # Append the HASC_1 code directory to the base output directory
        output_dir = (self.config.output_dir / code).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        return OutputPaths(
            boundary_gpkg=(
                output_dir / f"{code}_boundary.gpkg"
            ),
            clipped_grid=(
                output_dir
                / f"{code}_population_2025_100m.tif"
            ),
            report_pdf=(
                output_dir
                / f"{code}_population_2025_100m.pdf"
            ),
            summary_csv=(
                output_dir
                / f"{code}_population_2025_summary.csv"
            ),
            summary_json=(
                output_dir
                / f"{code}_population_2025_summary.json"
            ),
        )

    def run(self) -> WorkflowResult:
        print(
            f"[1/4] Select GADM province "
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

        print("[2/4] Save boundary and cut population grid")
        GeoIO.write(
            province_gdf,
            outputs.boundary_gpkg,
            layer="province",
            overwrite=self.config.overwrite,
        )

        province_raster_crs = self.clipper.clip(
            source_path=self.config.population_grid,
            province_gdf=province_gdf,
            output_path=outputs.clipped_grid,
            overwrite=self.config.overwrite,
            all_touched=self.config.all_touched,
        )

        print("[3/4] Calculate population-grid statistics")
        statistics = self.statistics_reader.read(
            outputs.clipped_grid
        )

        if self.config.write_pdf:
            print("[4/4] Write population-grid PDF and summaries")
            self.pdf_report.write(
                clipped_grid=outputs.clipped_grid,
                province_gdf=province_raster_crs,
                statistics=statistics,
                output_path=outputs.report_pdf,
                overwrite=self.config.overwrite,
            )
        else:
            print("[4/4] Write summaries; PDF disabled")

        result = WorkflowResult(
            province_code=province_code,
            province_name=province_name,
            gadm_layer=(
                self.repository.layer_name
                or self.config.gadm.stem
            ),
            statistics=statistics,
            outputs=outputs,
        )

        self._write_summaries(result)
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
                    "total_population": (
                        result.statistics.total_population
                    ),
                    "valid_cell_count": (
                        result.statistics.valid_cell_count
                    ),
                    "occupied_cell_count": (
                        result.statistics.occupied_cell_count
                    ),
                    "zero_cell_count": (
                        result.statistics.zero_cell_count
                    ),
                    "minimum_cell_value": (
                        result.statistics.minimum_cell_value
                    ),
                    "maximum_cell_value": (
                        result.statistics.maximum_cell_value
                    ),
                    "mean_cell_value": (
                        result.statistics.mean_cell_value
                    ),
                    "median_cell_value": (
                        result.statistics.median_cell_value
                    ),
                    "standard_deviation": (
                        result.statistics.standard_deviation
                    ),
                    "raster_width": (
                        result.statistics.raster_width
                    ),
                    "raster_height": (
                        result.statistics.raster_height
                    ),
                    "pixel_size_x": (
                        result.statistics.pixel_size_x
                    ),
                    "pixel_size_y": (
                        result.statistics.pixel_size_y
                    ),
                    "raster_crs": (
                        result.statistics.raster_crs
                    ),
                    "boundary_gpkg": str(
                        result.outputs.boundary_gpkg
                    ),
                    "clipped_grid": str(
                        result.outputs.clipped_grid
                    ),
                    "report_pdf": (
                        str(result.outputs.report_pdf)
                        if self.config.write_pdf
                        else ""
                    ),
                }
            ]
        )

    def _write_summaries(
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
                        "population_grid": str(
                            self.config.population_grid
                        ),
                        "gadm": str(self.config.gadm),
                        "output_dir": str(
                            self.config.output_dir
                        ),
                    },
                    "result": {
                        "province_code": result.province_code,
                        "province_name": result.province_name,
                        "gadm_layer": result.gadm_layer,
                        "statistics": asdict(
                            result.statistics
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
# CLI
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
            "Select a GADM ADM1 province by HASC_1 and cut out "
            "the Thailand 2025 population raster. No contours "
            "are generated."
        ),
    )

    parser.add_argument(
        "-p",
        "--province",
        help="GADM HASC_1 code, for example TH.CM.",
    )
    parser.add_argument(
        "--population-grid",
        default=str(DEFAULT_POPULATION_GRID),
        help="Thailand 2025 population-grid GeoTIFF.",
    )
    parser.add_argument(
        "--gadm",
        help="GADM GeoPackage or shapefile.",
    )
    parser.add_argument(
        "--gadm-layer",
        help=(
            "ADM1 layer name. When omitted, the layer "
            "containing HASC_1 is detected automatically."
        ),
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
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
        help=(
            "Include every raster cell touched by the boundary. "
            "This may increase the population sum near edges."
        ),
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Do not create the population-grid PDF.",
    )
    parser.add_argument(
        "--max-plot-dimension",
        type=int,
        default=1800,
        help="Maximum raster width or height used in the PDF.",
    )
    parser.add_argument(
        "--pdf-dpi",
        type=int,
        default=200,
        help="PDF image resolution.",
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
            population_grid=Path(
                args.population_grid
            ).expanduser(),
            gadm=gadm_path,
            province=args.province,
            output_dir=Path(
                args.output_dir
            ).expanduser(),
            gadm_layer=args.gadm_layer,
            overwrite=args.overwrite,
            all_touched=args.all_touched,
            write_pdf=not args.no_pdf,
            max_plot_dimension=args.max_plot_dimension,
            pdf_dpi=args.pdf_dpi,
        )

        result = PopulationProvinceWorkflow(
            config
        ).run()

        print("\nCompleted successfully.")
        print(
            pd.DataFrame(
                [
                    {
                        "HASC_1": result.province_code,
                        "NAME_1": result.province_name,
                        "population_sum": (
                            result.statistics.total_population
                        ),
                        "grid": result.outputs.clipped_grid,
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
