#!/usr/bin/env python3
"""
Refactored Object-Oriented Province Simplification Pipeline 
Merged with Unified BiSplitter/TriSplitter Spatial Splitting Logic
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from shapely.geometry import Polygon, LineString
from shapely.ops import split
from typing import Sequence

# Suppress UserWarning about calculating area/centroid using a geographic CRS
warnings.filterwarnings("ignore", category=UserWarning)


# ==============================================================
# UNIFIED SPATIAL SPLITTER (Merged from TriSplitter.py)
# ==============================================================
class PolygonSpatialSplitter:
    """
    Split polygon using parallel/similar-direction LineStrings.

    Supported SPLIT_CODE:
        NS  : North -> South                 (1 cutter)
        WE  : West  -> East                  (1 cutter)
        NCS : North -> Central -> South      (2 cutters)
        WCE : West  -> Central -> East       (2 cutters)
    """

    VALID_SPLIT_CODES = {
        "NS",
        "WE",
        "NCS",
        "WCE",
    }

    def __init__(
        self,
        polygon: Polygon,
        cutters: Sequence[LineString],
        split_code: str,
    ):
        self.polygon = polygon
        self.cutters = list(cutters)
        self.split_code = split_code.upper()

        self.pieces = []
        self.result = {}

        self._validate()

    def _validate(self):
        if not isinstance(self.polygon, Polygon):
            raise TypeError("polygon must be Polygon")

        if self.split_code not in self.VALID_SPLIT_CODES:
            raise ValueError(
                f"Unsupported SPLIT_CODE={self.split_code!r}. "
                f"Supported: {sorted(self.VALID_SPLIT_CODES)}"
            )

        if len(self.cutters) + 1 != len(self.split_code):
            raise ValueError(
                f"{len(self.cutters)} cutters produce "
                f"{len(self.cutters) + 1} zones, "
                f"but SPLIT_CODE has {len(self.split_code)} characters"
            )

        for i, cutter in enumerate(self.cutters):
            if not isinstance(cutter, LineString):
                raise TypeError(f"cutter[{i}] must be LineString")
            if cutter.is_empty:
                raise ValueError(f"cutter[{i}] is empty")

    def split(self):
        pieces = [self.polygon]

        # Split sequentially
        for cutter in self.cutters:
            new_pieces = []
            for poly in pieces:
                if not cutter.intersects(poly):
                    new_pieces.append(poly)
                    continue

                result = split(poly, cutter)
                for geom in result.geoms:
                    if isinstance(geom, Polygon) and not geom.is_empty:
                        new_pieces.append(geom)

            pieces = new_pieces

        expected = len(self.split_code)
        if len(pieces) != expected:
            raise RuntimeError(
                f"Expected {expected} polygons, "
                f"but got {len(pieces)}"
            )

        # Geographic sorting
        pieces = self._spatial_sort(pieces)
        self.pieces = pieces
        self.result = dict(zip(self.split_code, pieces))

        return self.result

    def _spatial_sort(self, polygons):
        """
        Geographic sorting according to SPLIT_CODE.
        NCS / NS: high Y -> low Y
        WCE / WE: low X -> high X
        """
        if self.split_code in ("NCS", "NS"):
            # North -> South
            return sorted(
                polygons,
                key=lambda p: p.representative_point().y,
                reverse=True,
            )
        elif self.split_code in ("WCE", "WE"):
            # West -> East
            return sorted(
                polygons,
                key=lambda p: p.representative_point().x,
            )
        raise ValueError(f"Unknown SPLIT_CODE: {self.split_code}")


# ==============================================================
# MAIN PIPELINE 
# ==============================================================
class ProvinceSimplifier:
    
    SUFFIX_MAP = {
        'N': ('_N', ' North'),
        'S': ('_S', ' South'),
        'W': ('_W', ' West'),
        'E': ('_E', ' East'),
        'C': ('_C', ' Central')
    }

    def __init__(self, input_gpkg: str | Path, divider_gpkg: str | Path, output_dir: str | Path):
        self.input_gpkg = Path(input_gpkg)
        self.divider_gpkg = Path(divider_gpkg)
        self.output_dir = Path(output_dir)
        self.output_gpkg = self.output_dir / "gadm41_THA.gpkg"
        self.output_csv = self.output_dir / "gadm41_THA.csv"
        self.output_toml = self.output_dir / "PROV_LDP.toml"
        
        self.gdf = None
        self.divider_gdf = None
        self.largest_polys = None
        self.poly_counts = None
        self.total_areas = None

    @staticmethod
    def _dd_to_ddmm(dd: float) -> str:
        """Convert decimal degrees to DDD:MM string format."""
        dd = abs(dd)
        degrees = int(dd)
        minutes = int(round((dd - degrees) * 60))
        if minutes == 60:
            degrees += 1
            minutes = 0
        return f"{degrees}:{minutes:02d}"

    def _get_cm_cp(self, row) -> str:
        """Determine CM (TM) or CP (LCC) from the centroid."""
        centroid = row.geometry.centroid
        if row['LDP'] == 'TM':
            return self._dd_to_ddmm(centroid.x)  # Longitude
        else:
            return self._dd_to_ddmm(centroid.y)  # Latitude

    def load_data(self):
        """1) Read GADM layer and Divider lines layer."""
        print(f"-> [READ] Opening GADM provinces: {self.input_gpkg.resolve()}")
        self.gdf = gpd.read_file(self.input_gpkg, layer="ADM_ADM_1")
        
        if self.divider_gpkg.exists():
            print(f"-> [READ] Opening Divider lines: {self.divider_gpkg.resolve()}")
            self.divider_gdf = gpd.read_file(self.divider_gpkg, layer="Divider_Prov")
        else:
            print(f"-> [WARNING] Divider file not found at {self.divider_gpkg.resolve()}. Skipping splits.")
            self.divider_gdf = None

    def fix_iso_codes(self):
        """2) Fix ISO_1 for TH.BM."""
        print("-> [PROCESS] Fixing ISO codes...")
        self.gdf.loc[self.gdf["HASC_1"] == "TH.BM", "ISO_1"] = "TH-10"
        # Add handling for specific HASC_1 updates
        if "HASC_1" in self.gdf.columns:
            self.gdf.loc[self.gdf["HASC_1"] == "TH.BM.CT", "HASC_1"] = "TH.CM.CT"

    def union_greater_bkk(self):
        """3) Union TH.BM, TH.NO, TH.SP into TH.GBKK."""
        gbkk_targets = ["TH.BM", "TH.NO", "TH.SP"]
        gbkk_mask = self.gdf["HASC_1"].isin(gbkk_targets)
        
        if gbkk_mask.any():
            print("-> [PROCESS] Unioning TH.BM, TH.NO, TH.SP into GreaterBKK (TH.GBKK)...")
            gbkk_geom = self.gdf[gbkk_mask].geometry.union_all()
            
            gbkk_attrs = {
                "GID_1": "THA.999",
                "GID_0": "THA",
                "COUNTRY": "Thailand",
                "NAME_1": "GreaterBKK",
                "VARNAME_1": "MEA BKK",
                "NL_NAME_1": "กรุงเทพและปริมณฑล",
                "TYPE_1": "Changwat",
                "ENGTYPE_1": "Province",
                "CC_1": "999",
                "HASC_1": "TH.GBKK",
                "ISO_1": "TH-999",
                "geometry": gbkk_geom
            }
            
            self.gdf = self.gdf[~gbkk_mask].copy()
            gbkk_gdf = gpd.GeoDataFrame([gbkk_attrs], crs=self.gdf.crs)
            self.gdf = pd.concat([self.gdf, gbkk_gdf], ignore_index=True)

    def process_geometries(self):
        """4) Explode multipolygons and calculate areas."""
        print("-> [PROCESS] Exploding multipolygons and calculating areas...")
        exploded = self.gdf.explode(index_parts=False).reset_index(drop=True)
        exploded["part_area"] = exploded.geometry.area * 111 * 111
        
        self.poly_counts = exploded.groupby("HASC_1").size().rename("GADM_num_polys")
        self.total_areas = exploded.groupby("HASC_1")["part_area"].sum().rename("total_area")
        
        self.largest_polys = exploded.sort_values("part_area", ascending=False).drop_duplicates(subset=["HASC_1"]).copy()
        
        # Keep self.gdf updated with the processed largest polygons
        self.gdf = self.largest_polys.copy()

    def apply_splitter(self, hasc_target: str, cutters: list, split_code: str):
        """Consolidated function to split a province polygon into 2 or 3 parts."""
        match_idx = self.gdf[self.gdf["HASC_1"] == hasc_target].index
        if match_idx.empty:
            return
        #print( hasc_target) 
        prov_row = self.gdf.loc[match_idx[0]].copy()
        poly_geom = prov_row.geometry

        try:
            # Instantiate unified PolygonSpatialSplitter
            splitter = PolygonSpatialSplitter(polygon=poly_geom, cutters=cutters, split_code=split_code)
            result = splitter.split()
        except Exception as e:
            print(f"-> [ERROR] Spatial Splitter failed for {hasc_target} (Code: {split_code}): {e}")
            return

        new_rows = []
        for split_char, part in result.items():
            new_row = prov_row.copy()
            new_row.geometry = part
            
            part_area = part.area * 111 * 111
            area_sqkm = int(part_area)

            suffix, label_suffix = self.SUFFIX_MAP[split_char]
            
            new_row["HASC_1"] = f"{hasc_target}{suffix}"
            new_row["NAME_1"] = f"{prov_row['NAME_1']}{label_suffix}"
            new_row["part_area"] = part_area
            
            print(f"   - Split {hasc_target} -> {new_row['HASC_1']} | Area: {area_sqkm:,} sq km")
            new_rows.append(new_row)

        # Update main GeoDataFrame
        self.gdf = self.gdf.drop(index=match_idx[0]).copy()
        new_gdf = gpd.GeoDataFrame(new_rows, crs=self.gdf.crs)
        self.gdf = pd.concat([self.gdf, new_gdf], ignore_index=True)
        self.largest_polys = self.gdf.copy()


    def check_ldp_design(self):
        """6) Calculate rectangular cover dimensions, LDP projection types, and CM_CP."""
        print("-> [PROCESS] Checking LDP Design (Dimensions, LDP, and CM_CP)...")
        bounds = self.largest_polys.bounds
        mid_y = (bounds["maxy"] + bounds["miny"]) / 2.0
        
        self.largest_polys["NS_km"] = ((bounds["maxy"] - bounds["miny"]) * 111).astype(int)
        self.largest_polys["EW_km"] = ((bounds["maxx"] - bounds["minx"]) * 111 * np.cos(np.radians(mid_y))).astype(int)
        
        # Determine LDP projection type based on extent
        diff_pct = (self.largest_polys["EW_km"] - self.largest_polys["NS_km"]).abs() / self.largest_polys[["EW_km", "NS_km"]].max(axis=1)
        self.largest_polys["LDP"] = np.where(
            (self.largest_polys["NS_km"] >= self.largest_polys["EW_km"]) | (diff_pct < 0.10), 
            'TM', 
            'LCC'
        )
        
        # Calculate Centroid and CM_CP
        self.largest_polys["CM_CP"] = self.largest_polys.apply(self._get_cm_cp, axis=1)
        self.gdf = self.largest_polys.copy()

    def export_data(self):
        """7) Write outputs to GeoPackage, Extended CSV, and TOML configuration."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write GeoPackage
        print(f"-> [WRITE] Saving simplified polygons to: {self.output_gpkg.resolve()}")
        original_columns = [col for col in self.gdf.columns if col in self.largest_polys.columns]
        out_gdf = self.largest_polys[original_columns]
        out_gdf.to_file(self.output_gpkg, layer="ADM_ADM_1", driver="GPKG")
        
        # Write Extended CSV summary
        print(f"-> [WRITE] Saving extended CSV summary to: {self.output_csv.resolve()}")
        csv_export = self.largest_polys[["ISO_1", "HASC_1", "NAME_1", "EW_km", "NS_km", "LDP", "CM_CP"]].copy()
        csv_export["area_sqkm"] = self.largest_polys["part_area"].astype(int) if "part_area" in self.largest_polys.columns else (self.largest_polys.geometry.area * 111 * 111).astype(int)
        csv_export = csv_export.merge(self.poly_counts, on="HASC_1", how="left")
        csv_export["GADM_num_polys"] = csv_export["GADM_num_polys"].fillna(1)
        csv_export = csv_export[["ISO_1", "HASC_1", "NAME_1", "GADM_num_polys", "area_sqkm", "EW_km", "NS_km", "LDP", "CM_CP"]]
        csv_export.to_csv(self.output_csv, index=False)
        
        # Write TOML config
        print(f"-> [WRITE] Generating TOML configuration to: {self.output_toml.resolve()}")
        with open(self.output_toml, "w", encoding="utf-8") as f:
            for _, row in self.largest_polys.sort_values("HASC_1").iterrows():
                hasc = row['HASC_1']
                file_code = hasc.replace(".", "_")
                ldp = row['LDP']
                cm_cp = row['CM_CP']
                
                f.write(f'["{hasc}"]\n')
                f.write(f'LDP = ["{ldp}", "{cm_cp}"]\n')
                f.write(f'FALSE_EN = "AUTO"    # [-10000, +2000000]\n')
                f.write(f'PP_MSL = "AUTO"      #  255\n')
                f.write(f'#POPU_PLOT = [ max_msl, min_msl, msl_interval ]\n')
                f.write(f'GPKG = ["OUTPUT_SAMPL/{file_code}/{file_code}_SAMPL.gpkg", "samples"]\n\n')

    def print_report(self):
        """8) Build and print analytical execution report."""
        print("\nGenerating report...\n")
        
        report_df = self.largest_polys.copy()
        if "part_area" not in report_df.columns:
            report_df["part_area"] = report_df.geometry.area * 111 * 111
            
        report = report_df[["HASC_1", "NAME_1", "part_area", "EW_km", "NS_km", "LDP", "CM_CP"]].copy()
        report = report.merge(self.poly_counts, on="HASC_1", how="left")
        report["GADM_num_polys"] = report["GADM_num_polys"].fillna(1)
        report = report.merge(self.total_areas, on="HASC_1", how="left")
        report["total_area"] = report["total_area"].fillna(report["part_area"])
        
        report["area_sqkm"] = report["part_area"].astype(int)
        report["dropped_area_sqkm"] = (report["total_area"] - report["part_area"]).astype(int)
        
        report["area_sqkm"] = report["area_sqkm"].apply(lambda x: f"{x:,}")
        report["dropped_area_sqkm"] = report["dropped_area_sqkm"].apply(lambda x: f"{x:,}")
        report["NAME_1"] = report["NAME_1"].astype(str).str[:12]

        report = report.rename(columns={
            "GADM_num_polys": "n_polys",
            "dropped_area_sqkm": "_area_sqkm",
        })
        report = report[["HASC_1", "NAME_1", "n_polys", "area_sqkm", "_area_sqkm", "EW_km", "NS_km", "LDP", "CM_CP"]]
        report = report.sort_values("HASC_1", ascending=True)
        
        print("========================= PROVINCE SIMPLIFICATION REPORT =========================")
        print(f"Source file  : {self.input_gpkg.resolve()}")
        print(f"Output file  : {self.output_gpkg.resolve()}")
        print("==================================================================================\n")
        try:
            print(report.to_markdown(index=False, stralign="right"))
        except ImportError:
            print(report.to_string(index=False, justify="right"))
            
        tm_count = (self.largest_polys["LDP"] == "TM").sum()
        lcc_count = (self.largest_polys["LDP"] == "LCC").sum()
        print("\n" + "="*82)
        print(f"SUMMARY COUNT => TM (Transverse Mercator): {tm_count} | LCC (Lambert Conformal Conic): {lcc_count}")
        print("="*82 + "\n")

    def run(self):
        """Execute the full OOP pipeline."""
        self.load_data()
        self.fix_iso_codes()
        self.union_greater_bkk()
        self.process_geometries()

        # Divider lines grouping and routing logic
        if self.divider_gdf is not None and not self.divider_gdf.empty:
            print("-> [PROCESS] Applying divider linestrings to split provinces...")
            
            # Enforce valid LS_Divide codes
            valid_ls_codes = {"NS", "WE", "WC", "CE", "NC", "CS"}
            self.divider_gdf = self.divider_gdf[self.divider_gdf["LS_Divide"].isin(valid_ls_codes)]
            
            grouped = self.divider_gdf.groupby("HASC_1")
            
            for hasc_target, grp in grouped:
                ls_divides = set(grp["LS_Divide"])
                cutters = grp.geometry.tolist()
                
                # BiSplitter Logic (1 cutter)
                if ls_divides == {"NS"}:
                    self.apply_splitter(hasc_target, cutters, split_code='NS')
                elif ls_divides == {"WE"}:
                    self.apply_splitter(hasc_target, cutters, split_code='WE')
                    
                # TriSplitter Logic (2 cutters)
                elif ls_divides == {'WC', 'CE'}:
                    self.apply_splitter(hasc_target, cutters, split_code='WCE')
                elif ls_divides == {'NC', 'CS'}:
                    self.apply_splitter(hasc_target, cutters, split_code='NCS')
                else:
                    print(f"-> [WARNING] Unrecognized split combination {ls_divides} for {hasc_target}. Skipping.")

        self.check_ldp_design()
        self.export_data()
        self.print_report()


if __name__ == "__main__":
    simplifier = ProvinceSimplifier(
        input_gpkg="DATA/gadm41_THA.gpkg",
        divider_gpkg="DATA/Divider_Prov.gpkg",
        output_dir="OUTPUT_PROV"
    )
    simplifier.run()
