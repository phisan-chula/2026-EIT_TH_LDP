#!/usr/bin/env python3
"""
Generate a sample point grid for a given GADM province with unique Geohashes,
and extract MSL (Elevation) and Population (POP2025) values.

Main workflow
-------------
1. Read GADM ADM1 as a GeoDataFrame.
2. Determine the UTM EPSG code using pyproj.
3. Reproject the province to UTM and align to grid size.
4. Generate points bounding the province and clip them.
5. Calculate an adequate-precision Geohash for each point.
6. Extract MSL elevation from OUTPUT_FABDEM.
7. Extract Population from OUTPUT_POP2025 (Summed over the grid cell).
8. Save to OUTPUT_SAMPL/{FILE_CODE}/{FILE_CODE}_SAMPL.gpkg (in EPSG:4326),
   where FILE_CODE converts dots in HASC_1 to underscores (TH.KK -> TH_KK).
9. Compare Total POP2025 with DOPA Registration Population.
"""

from __future__ import annotations

import argparse
import itertools
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
from shapely.geometry import Point, box
from rasterio.mask import mask
from rasterio.io import MemoryFile
from rasterio.warp import calculate_default_transform, reproject, Resampling


DEFAULT_OUTPUT_DIR = Path("./OUTPUT_SAMPL")
DEFAULT_DIR_FABDEM = Path("./OUTPUT_FABDEM")
DEFAULT_DIR_POP2025 = Path("./OUTPUT_POP2025")
DEFAULT_DOPA_CSV = Path("./DATA/stat_c68_utf8.csv")

DEFAULT_GADM_CANDIDATES = (
    Path("./OUTPUT_PROV/gadm41_THA.gpkg"),
)


# =====================================================================
# Models
# =====================================================================

@dataclass(frozen=True)
class WorkflowConfig:
    gadm: Path
    province: str
    grid_size: float = 1000.0
    output_dir: Path = DEFAULT_OUTPUT_DIR
    dir_fabdem: Path = DEFAULT_DIR_FABDEM
    dir_pop2025: Path = DEFAULT_DIR_POP2025
    dopa_csv: Path = DEFAULT_DOPA_CSV
    gadm_layer: Optional[str] = None
    overwrite: bool = False

    def validate(self) -> None:
        if not self.gadm.exists():
            raise FileNotFoundError(f"GADM dataset not found: {self.gadm}")
        if not self.province.strip():
            raise ValueError("A HASC_1 province code is required.")
        if self.grid_size <= 0:
            raise ValueError("--grid must be greater than zero.")


@dataclass(frozen=True)
class OutputPaths:
    sampl_gpkg: Path
    dem_tif: Path
    pop_tif: Path


@dataclass(frozen=True)
class WorkflowResult:
    province_code: str
    province_name: str
    epsg_code: int
    grid_size: float
    geohash_precision: int
    point_count: int
    outputs: OutputPaths
    pop2025_sum: float
    dopa_pop: float
    pop_diff: float


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
            raise FileExistsError(f"Output already exists: {path}. Use --overwrite.")

        if path.is_dir():
            raise IsADirectoryError(f"Expected a file but found a directory: {path}")

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
            return gpd.read_file(path, engine="pyogrio", **kwargs)
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
        print(f" -> [WRITE] Saving Vector File: {path} (Layer: '{layer}')")

        try:
            frame.to_file(path, layer=layer, driver="GPKG", index=False, engine="pyogrio")
        except Exception:
            frame.to_file(path, layer=layer, driver="GPKG", index=False)


# =====================================================================
# Raster Extraction Engine
# =====================================================================

class RasterExtractor:
    """Extract values from a raster dataset at given GeoDataFrame point locations."""

    @staticmethod
    def extract(
        points_gdf: gpd.GeoDataFrame, 
        raster_path: Path, 
        column_name: str,
        nodata_fill: float = np.nan
    ) -> gpd.GeoDataFrame:
        
        if not raster_path.exists():
            print(f" -> [READ ERROR] Raster not found at {raster_path}. Filling with {nodata_fill}.")
            points_gdf[column_name] = nodata_fill
            return points_gdf

        print(f" -> [READ] Opening Raster File: {raster_path}")
        with rasterio.open(raster_path) as src:
            if src.crs is None:
                raise ValueError(f"Raster has no CRS: {raster_path}")
                
            points_proj = points_gdf.to_crs(src.crs)
            coords = [(geom.x, geom.y) for geom in points_proj.geometry]
            sampled_generator = src.sample(coords)
            sampled_values = np.fromiter(
                (val[0] for val in sampled_generator), 
                dtype=np.float64, 
                count=len(coords)
            )
            
            nodata = src.nodata
            if nodata is not None:
                sampled_values = np.where(
                    np.isclose(sampled_values, nodata, equal_nan=True), 
                    nodata_fill, 
                    sampled_values
                )
            
            points_gdf[column_name] = sampled_values
            
        return points_gdf

    @staticmethod
    def extract_sum(
        points_gdf: gpd.GeoDataFrame, 
        raster_path: Path, 
        column_name: str,
        grid_size: float,
        nodata_fill: float = 0.0
    ) -> gpd.GeoDataFrame:
        """Sums the raster values within a square grid cell centered on each point."""
        
        if not raster_path.exists():
            print(f" -> [READ ERROR] Raster not found at {raster_path}. Filling with {nodata_fill}.")
            points_gdf[column_name] = nodata_fill
            return points_gdf

        print(f" -> [READ] Opening Raster File for Area Sum: {raster_path}")
        
        # points_gdf is in UTM (meters). Create square bounding boxes in meters first.
        half_grid = grid_size / 2.0
        squares_geom = points_gdf.geometry.apply(
            lambda geom: box(geom.x - half_grid, geom.y - half_grid, geom.x + half_grid, geom.y + half_grid)
        )

        with rasterio.open(raster_path) as src:
            if src.crs is None:
                raise ValueError(f"Raster has no CRS: {raster_path}")
                
            dst_crs = points_gdf.crs
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds
            )
            
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            with MemoryFile() as memfile:
                with memfile.open(**kwargs) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=transform,
                            dst_crs=dst_crs,
                            resampling=Resampling.nearest
                        )
                    
                    sampled_sums = []
                    nodata = dst.nodata
                    
                    for square in squares_geom:
                        try:
                            out_image, _ = mask(dst, [square], crop=True, all_touched=False)
                            if nodata is not None:
                                valid_data = out_image[out_image != nodata]
                            else:
                                valid_data = out_image
                                
                            valid_data = valid_data[~np.isnan(valid_data)]
                            
                            if valid_data.size > 0:
                                sampled_sums.append(np.sum(valid_data))
                            else:
                                sampled_sums.append(nodata_fill)
                        except ValueError:
                            sampled_sums.append(nodata_fill)
            
            points_gdf[column_name] = sampled_sums
        #import pdb ;pdb.set_trace()
        return points_gdf


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
            import fiona
            return list(fiona.listlayers(self.gadm_path))

    def _columns(self, layer_name: Optional[str]) -> set[str]:
        frame = GeoIO.read(self.gadm_path, layer=layer_name, rows=1)
        return set(frame.columns)

    def _resolve_layer(self, requested_layer: Optional[str]) -> Optional[str]:
        if self.gadm_path.suffix.lower() != ".gpkg":
            return None
        layers = self._available_layers()
        if requested_layer:
            if requested_layer not in layers:
                raise ValueError(f"Layer '{requested_layer}' not found.")
            return requested_layer
        candidates = [name for name in layers if self.CODE_FIELD in self._columns(name)]
        if not candidates:
            raise ValueError(f"No layer containing {self.CODE_FIELD} found.")
        preferred = [name for name in candidates if "ADM_1" in name.upper() or "ADM1" in name.upper() or name.upper().endswith("_1")]
        return preferred[0] if preferred else candidates[0]

    def read_all(self) -> gpd.GeoDataFrame:
        frame = GeoIO.read(self.gadm_path, layer=self.layer_name)
        if self.CODE_FIELD not in frame.columns:
            raise ValueError(f"GADM layer does not contain {self.CODE_FIELD}.")
        frame = frame.copy()
        frame[self.CODE_FIELD] = frame[self.CODE_FIELD].fillna("").astype(str).str.strip()
        frame[self.NAME_FIELD] = frame.get(self.NAME_FIELD, frame[self.CODE_FIELD]).fillna(frame[self.CODE_FIELD]).astype(str).str.strip()
        return frame

    def province_table(self) -> pd.DataFrame:
        frame = self.read_all()
        return pd.DataFrame(
            frame[[self.CODE_FIELD, self.NAME_FIELD]]
            .drop_duplicates()
            .query(f"{self.CODE_FIELD} != ''")
            .sort_values(self.CODE_FIELD)
            .reset_index(drop=True)
        )

    def select(self, province_code: str) -> gpd.GeoDataFrame:
        print(f" -> [READ] Loading Vector Dataset: {self.gadm_path} (Layer: '{self.layer_name}')")
        wanted = province_code.strip().upper()
        frame = self.read_all()
        selected = frame[frame[self.CODE_FIELD].str.upper().eq(wanted)].copy()
        if selected.empty:
            raise KeyError(f"HASC_1 '{province_code}' was not found.")
        selected = selected[selected.geometry.notna() & ~selected.geometry.is_empty].copy()
        
        dissolve_cols = [self.CODE_FIELD, self.NAME_FIELD]
        if "ISO_1" in selected.columns:
            dissolve_cols.append("ISO_1")
            
        selected = selected.dissolve(by=dissolve_cols, as_index=False)
        return gpd.GeoDataFrame(selected, geometry="geometry", crs=frame.crs)


# =====================================================================
# Grid & Geohash Generator
# =====================================================================

class SampleGridGenerator:
    """Generate UTM sample points bounded and clipped by the province."""

    @staticmethod
    def get_utm_epsg(lat: float, lon: float) -> int:
        utm_crs_list = query_utm_crs_info(datum_name="WGS 84", area_of_interest=AreaOfInterest(lon, lat, lon, lat))
        if not utm_crs_list:
            raise ValueError(f"Could not determine UTM CRS for lat={lat}, lon={lon}")
        return int(utm_crs_list[0].code)

    @staticmethod
    def calculate_geohash_precision(grid_size: float) -> int:
        if grid_size >= 1000: return 7
        if grid_size >= 100:  return 8
        if grid_size >= 10:   return 9
        if grid_size > 1.2:   return 10
        return 11

    @staticmethod
    def encode_geohash(latitude: float, longitude: float, precision: int) -> str:
        base32 = '0123456789bcdefghjkmnpqrstuvwxyz'
        lat_interval = [-90.0, 90.0]
        lon_interval = [-180.0, 180.0]
        geohash = []
        bits = [16, 8, 4, 2, 1]
        bit = 0
        ch = 0
        even = True
        
        while len(geohash) < precision:
            if even:
                mid = (lon_interval[0] + lon_interval[1]) / 2.0
                if longitude > mid:
                    ch |= bits[bit]
                    lon_interval[0] = mid
                else:
                    lon_interval[1] = mid
            else:
                mid = (lat_interval[0] + lat_interval[1]) / 2.0
                if latitude > mid:
                    ch |= bits[bit]
                    lat_interval[0] = mid
                else:
                    lat_interval[1] = mid
            even = not even
            if bit < 4:
                bit += 1
            else:
                geohash.append(base32[ch])
                bit = 0
                ch = 0
        return "".join(geohash)

    def generate(self, province_gdf: gpd.GeoDataFrame, grid_size: float) -> tuple[gpd.GeoDataFrame, int, int]:
        province_4326 = province_gdf.to_crs(epsg=4326)
        minx, miny, maxx, maxy = province_4326.total_bounds
        centroid_lon, centroid_lat = (minx + maxx) / 2.0, (miny + maxy) / 2.0
        
        epsg_code = self.get_utm_epsg(lat=centroid_lat, lon=centroid_lon)
        utm_crs = f"EPSG:{epsg_code}"
        print(f" -> Auto-detected {utm_crs} for province.")

        province_utm = province_gdf.to_crs(utm_crs)
        centroid_utm = province_utm.geometry.centroid.iloc[0]
        cx, cy = centroid_utm.x, centroid_utm.y
        
        aligned_cx, aligned_cy = round(cx / grid_size) * grid_size, round(cy / grid_size) * grid_size
        minx, miny, maxx, maxy = province_utm.total_bounds
        
        x_steps_left, x_steps_right = math.ceil((aligned_cx - minx) / grid_size), math.ceil((maxx - aligned_cx) / grid_size)
        y_steps_down, y_steps_up = math.ceil((aligned_cy - miny) / grid_size), math.ceil((maxy - aligned_cy) / grid_size)
        
        x_coords = [aligned_cx + (i * grid_size) for i in range(-x_steps_left, x_steps_right + 1)]
        y_coords = [aligned_cy + (i * grid_size) for i in range(-y_steps_down, y_steps_up + 1)]
        print(f" -> Generated {len(x_coords) * len(y_coords):,} bounding box points.")
        
        points = [Point(x, y) for x, y in itertools.product(x_coords, y_coords)]
        points_gdf = gpd.GeoDataFrame(geometry=points, crs=utm_crs)
        
        print(" -> Clipping points to province boundary...")
        clipped_points = points_gdf.clip(province_utm).copy()
        clipped_points["HASC_1"] = province_utm.iloc[0]["HASC_1"]
        clipped_points["NAME_1"] = province_utm.iloc[0]["NAME_1"]
        clipped_points["GRID_M"] = float(grid_size)
        
        precision = self.calculate_geohash_precision(grid_size)
        print(f" -> Computing {precision}-digit Geohashes...")
        
        points_4326_clipped = clipped_points.to_crs(epsg=4326)
        geohashes = points_4326_clipped.geometry.apply(
            lambda geom: self.encode_geohash(geom.y, geom.x, precision=precision)
        )
        clipped_points["sampl_point"] = geohashes
        clipped_points = clipped_points[["sampl_point", "HASC_1", "NAME_1", "GRID_M", "geometry"]].reset_index(drop=True)

        return clipped_points, epsg_code, precision


# =====================================================================
# Workflow
# =====================================================================

class SampleGenerationWorkflow:
    def __init__(self, config: WorkflowConfig) -> None:
        config.validate()
        self.config = config
        self.repository = GADMProvinceRepository(config.gadm, config.gadm_layer)
        self.generator = SampleGridGenerator()
        self.extractor = RasterExtractor()

    @staticmethod
    def _safe_code(code: str) -> str:
        """Convert a logical HASC code to a safe filesystem code.

        Example: ``TH.KK`` -> ``TH_KK``. The dotted HASC_1 value is still
        retained inside the GeoPackage attributes and used for GADM lookup.
        """
        return code.strip().upper().replace(".", "_")

    def _output_paths(self, province_code: str) -> OutputPaths:
        code = self._safe_code(province_code)
        output_dir = (self.config.output_dir / code).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        return OutputPaths(
            sampl_gpkg=output_dir / f"{code}_SAMPL.gpkg",
            dem_tif=self.config.dir_fabdem / code / f"{code}_fabdem.tif",
            pop_tif=self.config.dir_pop2025 / code / f"{code}_population_2025_100m.tif",
        )

    def run(self) -> WorkflowResult:
        print(f"[1/4] Select GADM province HASC_1={self.config.province}")
        province_gdf = self.repository.select(self.config.province)

        province_code = str(province_gdf.iloc[0]["HASC_1"])
        province_name = str(province_gdf.iloc[0]["NAME_1"])
        outputs = self._output_paths(province_code)

        print(f"[2/4] Generate {self.config.grid_size}m grid points")
        points_gdf, epsg_code, precision = self.generator.generate(
            province_gdf=province_gdf,
            grid_size=self.config.grid_size,
        )

        print(f"[3/4] Extracting Raster Values (FABDEM MSL & POP2025)...")
        points_gdf["sampl_epsg"] = epsg_code
        
        points_gdf = self.extractor.extract(
            points_gdf=points_gdf, 
            raster_path=outputs.dem_tif, 
            column_name="MSL",
            nodata_fill=-9999.0 
        )
        points_gdf["MSL"] = points_gdf["MSL"].astype(int)

        points_gdf = self.extractor.extract_sum(
            points_gdf=points_gdf, 
            raster_path=outputs.pop_tif, 
            column_name="POP",
            grid_size=self.config.grid_size,
            nodata_fill=0.0
        )
        points_gdf["POP"] = points_gdf["POP"].astype(float).round(4)

        points_gdf["sampl_UTM"] = points_gdf.geometry.to_wkt()

        cols = ["sampl_point", "HASC_1", "NAME_1", "GRID_M", "sampl_epsg", "sampl_UTM", "MSL", "POP", "geometry"]
        points_gdf = points_gdf[cols]

        print(f" -> Converting geometries to Lng/Lat (EPSG:4326)...")
        points_gdf = points_gdf.to_crs(epsg=4326)

        print(f"[4/4] Save GeoPackage Data...")
        GeoIO.write(frame=points_gdf, path=outputs.sampl_gpkg, layer="samples", overwrite=self.config.overwrite)

        # ---------------------------------------------------------
        # Compare POP2025 vs DOPA_RegistPop
        # ---------------------------------------------------------
        total_pop2025 = points_gdf["POP"].sum()
        dopa_pop = 0.0
        diff_pop = 0.0
        
        print("\n[5/5] Comparing POP2025 with DOPA Registration Population...")
        if self.config.dopa_csv.exists() and "ISO_1" in province_gdf.columns:
            try:
                iso_1 = str(province_gdf.iloc[0]["ISO_1"])
                dopa_code = str(int(iso_1.split("-")[1]))
                
                df_dopa = pd.read_csv(self.config.dopa_csv, dtype=str)
                df_dopa["รหัสจังหวัด"] = df_dopa["รหัสจังหวัด"].str.strip()
                df_dopa["รหัสสำนักทะเบียน"] = df_dopa["รหัสสำนักทะเบียน"].str.strip()
                
                row = df_dopa[(df_dopa["รหัสจังหวัด"] == dopa_code) & (df_dopa["รหัสสำนักทะเบียน"] == '0')]
                
                if not row.empty:
                    dopa_str = row.iloc[0]["จำนวนประชากรทั้งหมด"].replace(",", "")
                    dopa_pop = float(dopa_str)
                    diff_pop = total_pop2025 - dopa_pop
                else:
                    print(f" -> Warning: Could not find DOPA data for province code {dopa_code}.")
            except Exception as e:
                print(f" -> Warning: Failed to process DOPA CSV comparison: {e}")
        else:
            if not self.config.dopa_csv.exists():
                print(f" -> Warning: {self.config.dopa_csv.name} not found.")
            else:
                print(f" -> Warning: 'ISO_1' column missing in GADM dataset. Cannot link to DOPA.")

        return WorkflowResult(
            province_code=province_code,
            province_name=province_name,
            epsg_code=4326,
            grid_size=self.config.grid_size,
            geohash_precision=precision,
            point_count=len(points_gdf),
            outputs=outputs,
            pop2025_sum=total_pop2025,
            dopa_pop=dopa_pop,
            pop_diff=diff_pop
        )


# =====================================================================
# CLI
# =====================================================================

def resolve_gadm_path(requested_path: Optional[str]) -> Path:
    if requested_path:
        return Path(requested_path).expanduser()
    for candidate in DEFAULT_GADM_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No default GADM dataset was found. Use --gadm PATH.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Generate UTM grid sample points and extract raster values.",
    )

    parser.add_argument("-p", "--province", help="GADM HASC_1 code, e.g., TH.CM.")
    parser.add_argument("-g", "--grid", type=float, default=1000.0, help="Grid size in metres.")
    parser.add_argument("--gadm", help="GADM GeoPackage or shapefile.")
    parser.add_argument("--gadm-layer", help="GADM layer name.")
    parser.add_argument("--dir-fabdem", type=Path, default=DEFAULT_DIR_FABDEM, help="Base dir for FABDEM outputs.")
    parser.add_argument("--dir-pop", type=Path, default=DEFAULT_DIR_POP2025, help="Base dir for POP2025 outputs.")
    parser.add_argument("--dopa-csv", type=Path, default=DEFAULT_DOPA_CSV, help="Path to stat_c68_utf8.csv")
    
    parser.add_argument("--list-provinces", action="store_true", help="Print provinces and exit.")
    parser.add_argument("--overwrite", default=True, action=argparse.BooleanOptionalAction, help="Replace existing output files.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        gadm_path = resolve_gadm_path(args.gadm)
        repository = GADMProvinceRepository(gadm_path, args.gadm_layer)

        if args.list_provinces:
            print(repository.province_table().to_string(index=False))
            return 0

        if not args.province:
            parser.error("-p/--province is required.")

        config = WorkflowConfig(
            gadm=gadm_path,
            province=args.province,
            grid_size=args.grid,
            output_dir=DEFAULT_OUTPUT_DIR,
            dir_fabdem=args.dir_fabdem.expanduser(),
            dir_pop2025=args.dir_pop.expanduser(),
            dopa_csv=args.dopa_csv,
            gadm_layer=args.gadm_layer,
            overwrite=args.overwrite,
        )

        result = SampleGenerationWorkflow(config).run()

        print("\nCompleted successfully.")
        
        # Display the output table with the new population columns included
        print(
            pd.DataFrame(
                [
                    {
                        "HASC_1": result.province_code,
                        "Grid (m)": result.grid_size,
                        "CRS": f"EPSG:{result.epsg_code}",
                        "Samples": result.point_count,
                        "Output": result.outputs.sampl_gpkg.name,
                        "POP2025": f"{result.pop2025_sum:,.0f}",
                        "DOPA_Pop": f"{result.dopa_pop:,.0f}",
                        "Diff": f"{result.pop_diff:,.0f}"
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
