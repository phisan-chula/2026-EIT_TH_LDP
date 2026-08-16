# -*- coding: utf-8 -*-
"""
PROGRAM: QAQC_LDP_TestLine.py
Description: Quality Control module to validate custom LDP parameters vs Ground and UTM.
"""

import math
import json
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import pyproj
import rasterio
import pygeodesy as pgd
from pathlib import Path


def extract_ldp_definitions(sampl_dir, out_dir):
    """
    Scans pipeline logs for LDP JSONL definitions and extracts 
    the Decimal PROJ strings into .PJ4 files.
    """
    print("Scanning pipeline logs for LDP PROJ definitions...")
    sampl_path = Path(sampl_dir)
    log_files = list(sampl_path.glob("*/*_pipeline.log"))
    
    if not log_files:
        print(f"  -> No pipeline logs found in {sampl_dir}")
        return

    extracted_count = 0
    for log_file in log_files:
        hasc_safe = log_file.parent.name 
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '{"meta": "LDP_Definition"' in line:
                    try:
                        data = json.loads(line.strip())
                        proj_decimal = data.get("PROJ_String_Decimal")
                        
                        if proj_decimal:
                            prov_dir = Path(out_dir) / hasc_safe
                            prov_dir.mkdir(parents=True, exist_ok=True)
                            pj4_path = prov_dir / f"{hasc_safe}_LDP_CRS.PJ4"
                            
                            with open(pj4_path, 'w', encoding='utf-8') as pj4_f:
                                pj4_f.write(proj_decimal)
                            
                            extracted_count += 1
                            break  
                            
                    except json.JSONDecodeError:
                        print(f"  -> Error parsing JSON in {log_file}")
                        
    print(f"Extracted {extracted_count} LDP definitions to {out_dir}\n")


class LDPValidator:
    def __init__(self, gadm_path, dem_path, out_dir, force_points=None):
        """Initialize the validator with paths, geodesic models, and forced points."""
        self.gadm_path = Path(gadm_path)
        self.dem_path = Path(dem_path)
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
        self.geod = pyproj.Geod(ellps='WGS84')
        self.ellps = pgd.datums.Ellipsoids.WGS84
        self.geoid = self._init_geoid()
        
        # Store forced geometries and track which ones were utilized
        self.force_points = force_points or {}
        self.used_force_points = set()
        
    def _init_geoid(self):
        """Initialize the TGM2017 Geoid model."""
        print("Loading TGM2017 Geoid model...")
        tgm_2017 = "/usr/share/GeographicLib/geoids/tgm2017-1.pgm"
        base_dir = Path(__file__).resolve().parent
        tgm_path = base_dir / "tgm2017-1.pgm"
        
        if Path(tgm_2017).is_file():
            return pgd.geoids.GeoidKarney(tgm_2017)
        return pgd.geoids.GeoidKarney(str(tgm_path))

    def _get_elevations(self, src, coords):
        """Extract orthometric heights from the DEM raster."""
        try:
            elevs = list(src.sample(coords))
            return float(elevs[0][0]), float(elevs[1][0])
        except Exception as e:
            raise ValueError(f"DEM sampling failed: {e}")

    def _calc_utm_parameters(self, lon1, lat1, lon2, lat2):
        """Calculate UTM grid distance, average PSF, and individual PSFs."""
        utm_crs_info = pyproj.database.query_utm_crs_info(
            datum_name="WGS 84", 
            area_of_interest=pyproj.aoi.AreaOfInterest(lon1, lat1, lon1, lat1)
        )[0]
        utm_proj = pyproj.CRS.from_epsg(utm_crs_info.code)
        transformer_utm = pyproj.Transformer.from_crs("EPSG:4326", utm_proj, always_xy=True)
        
        utm1_e, utm1_n = transformer_utm.transform(lon1, lat1)
        utm2_e, utm2_n = transformer_utm.transform(lon2, lat2)
        L3_UTM = math.hypot(utm2_e - utm1_e, utm2_n - utm1_n)
        
        utm_proj_obj = pyproj.Proj(utm_proj)
        psf1 = utm_proj_obj.get_factors(lon1, lat1).meridional_scale
        psf2 = utm_proj_obj.get_factors(lon2, lat2).meridional_scale
        psf_avg = (psf1 + psf2) / 2.0
        
        return L3_UTM, psf_avg, psf1, psf2

    def _calc_ldp_parameters(self, hasc_safe, lon1, lat1, lon2, lat2):
        """Calculate LDP grid distance, point scale factors, definition, and coordinates."""
        pj4_path = self.out_dir / hasc_safe / f"{hasc_safe}_LDP_CRS.PJ4"
        
        if not pj4_path.exists():
            print(f"  -> WARNING: {pj4_path} not found. L6 will be NaN.")
            return (
                np.nan, np.nan, np.nan, np.nan,
                "Not found", (np.nan, np.nan), (np.nan, np.nan)
            )
            
        with open(pj4_path, 'r') as f:
            ldp_proj_str = f.read().strip()
            
        ldp_crs = pyproj.CRS(ldp_proj_str)
        transformer_ldp = pyproj.Transformer.from_crs("EPSG:4326", ldp_crs, always_xy=True)
        
        ldp1_e, ldp1_n = transformer_ldp.transform(lon1, lat1)
        ldp2_e, ldp2_n = transformer_ldp.transform(lon2, lat2)
        ldp_distance = math.hypot(ldp2_e - ldp1_e, ldp2_n - ldp1_n)

        ldp_proj_obj = pyproj.Proj(ldp_crs)
        ldp_psf1 = ldp_proj_obj.get_factors(lon1, lat1).meridional_scale
        ldp_psf2 = ldp_proj_obj.get_factors(lon2, lat2).meridional_scale
        ldp_psf_avg = (ldp_psf1 + ldp_psf2) / 2.0

        return (
            ldp_distance, ldp_psf_avg, ldp_psf1, ldp_psf2,
            ldp_proj_str, (ldp1_e, ldp1_n), (ldp2_e, ldp2_n)
        )

    def process_province(self, row, src):
        """Process a single province boundary to compute all test distances."""
        hasc = row.get('HASC_1')
        if not hasc or pd.isna(hasc): 
            return None
            
        hasc_safe = str(hasc).replace('.', '_').upper()
        name_1 = row.get('NAME_1', 'Unknown')
        
        # 1. P1: Check for forced override, otherwise use centroid
        if hasc in self.force_points:
            p1_geom = self.force_points[hasc]
            self.used_force_points.add(hasc)
            lon1, lat1 = p1_geom.x, p1_geom.y
            print(f"  -> 🎯 ForcePoint overridden for {hasc_safe} ({name_1}) at ({lon1:.6f}, {lat1:.6f})")
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                p1_geom = row.geometry.representative_point()
            lon1, lat1 = p1_geom.x, p1_geom.y
        
        # 2. P2: 1000m North
        L1 = 1000.000 
        lon2, lat2, _ = self.geod.fwd(lon1, lat1, 0, L1)
        
        # 3. Heights and Geoid
        try:
            H1, H2 = self._get_elevations(src, [(lon1, lat1), (lon2, lat2)])
        except ValueError as e:
            print(f"  -> Skipping {hasc_safe}: {e}")
            return None
            
        N1 = self.geoid.height(lat1, lon1)
        N2 = self.geoid.height(lat2, lon2)
        h1 = H1 + N1
        h2 = H2 + N2
        
        H_avg = (H1 + H2) / 2.0
        N_avg = (N1 + N2) / 2.0
        h_avg = H_avg + N_avg
        
        # 4. Height Scale Factor & Ground Distance
        RG1 = self.ellps.rocGauss(lat1)
        RG2 = self.ellps.rocGauss(lat2)
        HSF1 = RG1 / (RG1 + h1)
        HSF2 = RG2 / (RG2 + h2)
        
        avg_lat = (lat1 + lat2) / 2.0
        RG = self.ellps.rocGauss(avg_lat)
        HSF = RG / (RG + h_avg)
        L2 = L1 / HSF
        
        # 5. UTM Distance & Point Scale Factor
        L3, PSF_avg, PSF1, PSF2 = self._calc_utm_parameters(lon1, lat1, lon2, lat2)
        
        # 6. UTM Combined Scale Factor (for comparison only)
        L4 = L3 / PSF_avg
        UTM_CSF_avg = PSF_avg * HSF
        UTM_CSF1 = PSF1 * HSF1
        UTM_CSF2 = PSF2 * HSF2
        L5 = L3 / UTM_CSF_avg

        # 7. LDP Grid Distance, Definition, Coordinates, and LDP scale factors
        (
            L6, LDP_PSF_avg, LDP_PSF1, LDP_PSF2,
            ldp_def, p1_ldp, p2_ldp
        ) = self._calc_ldp_parameters(hasc_safe, lon1, lat1, lon2, lat2)

        LDP_CSF1 = LDP_PSF1 * HSF1 if np.isfinite(LDP_PSF1) else np.nan
        LDP_CSF2 = LDP_PSF2 * HSF2 if np.isfinite(LDP_PSF2) else np.nan
        LDP_CSF_avg = LDP_PSF_avg * HSF if np.isfinite(LDP_PSF_avg) else np.nan
        
        return {
            'HASC_1': hasc,
            'NAME_1': name_1,
            'Province_Code': hasc_safe,
            'lat1': lat1, 'lon1': lon1,
            'lat2': lat2, 'lon2': lon2,
            'H_Orthometric': H_avg,
            'N_Undulation': N_avg,
            'h_Ellipsoidal': h_avg,
            'HSF': HSF,
            'UTM_PSF': PSF_avg,
            'UTM_CSF': UTM_CSF_avg,
            'UTM_CSF1': UTM_CSF1,
            'UTM_CSF2': UTM_CSF2,
            'LDP_PSF': LDP_PSF_avg,
            'LDP_PSF1': LDP_PSF1,
            'LDP_PSF2': LDP_PSF2,
            'LDP_CSF': LDP_CSF_avg,
            'LDP_CSF1': LDP_CSF1,
            'LDP_CSF2': LDP_CSF2,
            'L1_Ellps': L1,
            'L2_Grnd': L2,
            'L3_UTM': L3,
            'L4_UTM2Ellps': L4,
            'L5_UTM2Grnd': L5,
            'L6_LDP': L6,
            'LDP_Def': ldp_def,
            'P1_LDP': p1_ldp,
            'P2_LDP': p2_ldp,
            'diff_L1': L1 - L2,
            'diff_L2': 0.000,
            'diff_L3': L3 - L2,
            'diff_L4': L4 - L2,
            'diff_L5': L5 - L2,
            'diff_L6': L6 - L2,
            'geometry': LineString([Point(lon1, lat1), Point(lon2, lat2)])
        }

    def write_geopackages(self, df_results):
        """Export individual province Geopackages."""
        print(f"\nSaving generated test lines to Geopackages...")
        gdf_results = gpd.GeoDataFrame(df_results, geometry='geometry', crs="EPSG:4326")
        
        for hasc_safe, group in gdf_results.groupby('Province_Code'):
            prov_dir = self.out_dir / hasc_safe
            prov_dir.mkdir(parents=True, exist_ok=True)
            out_gpkg = prov_dir / f"{hasc_safe}_TestLine.gpkg"
            group.to_file(out_gpkg, driver='GPKG', layer='QAQC_Line')

    def write_markdown_report(self, df_results, df_line_descr):
        """Generate the final README.md summary report."""
        print("Generating Summary in OUTPUT_LDP/README.md ...")
        md_path = self.out_dir / 'README.md'
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# LDP Quality Control & Validation Summary\n\n")
            f.write("This report provides a comparative analysis of distances calculated across various map projections and surfaces. By establishing the **Ground Distance (L2)** as the true baseline of length 1,000.000 meter, we measure the linear distortion introduced by standard UTM grids against the custom Low Distortion Projections (LDP).\n\n")
            
            f.write("## --- Distance Definitions ---\n\n")
            f.write(df_line_descr.to_markdown(index=False) + "\n\n")
            
            for _, res in df_results.iterrows():
                p1_str = f"({res['lat1']:.9f}, {res['lon1']:.9f})"
                p2_str = f"({res['lat2']:.9f}, {res['lon2']:.9f})"
                
                msl_val = f"{int(round(res['H_Orthometric']))}"
                hae_val = f"{int(round(res['h_Ellipsoidal']))}"
                
                p1_ldp = res.get('P1_LDP', (np.nan, np.nan))
                p2_ldp = res.get('P2_LDP', (np.nan, np.nan))
                
                if pd.isna(p1_ldp[0]):
                    p1_ldp_str = "(NaN, NaN)"
                    p2_ldp_str = "(NaN, NaN)"
                else:
                    p1_ldp_str = f"({p1_ldp[0]:.3f}, {p1_ldp[1]:.3f})"
                    p2_ldp_str = f"({p2_ldp[0]:.3f}, {p2_ldp[1]:.3f})"
                
                diff_l6_str = "NaN" if pd.isna(res['diff_L6']) else f"{res['diff_L6']:+.3f}"
                
                csf1_ppm = (res['LDP_CSF1'] - 1.0) * 1_000_000
                csf2_ppm = (res['LDP_CSF2'] - 1.0) * 1_000_000
                
                flag1 = " ❗" if abs(csf1_ppm) > 20 else ""
                flag2 = " ❗" if abs(csf2_ppm) > 20 else ""
                
                utm_csf1_ppm = (res['UTM_CSF1'] - 1.0) * 1_000_000
                utm_csf2_ppm = (res['UTM_CSF2'] - 1.0) * 1_000_000
                
                f.write("---\n\n") 
                f.write(f"### 🧭 Province: {res['NAME_1']} ({res['HASC_1']})\n\n")
                
                f.write(f"| P1 | {p1_str} | P2 | {p2_str} |\n")
                f.write("|:---|:---|:---|:---|\n")
                f.write(f"| MSL | {msl_val} | HAE | {hae_val} |\n")
                f.write(f"| P1_LDP | {p1_ldp_str} | P2_LDP | {p2_ldp_str} |\n")
                f.write(f"| P1_LDP_CSF | {csf1_ppm:+.1f} ppm{flag1} | P2_LDP_CSF | {csf2_ppm:+.1f} ppm{flag2} |\n")
                f.write(f"| P1_UTM_CSF | {utm_csf1_ppm:+.1f} ppm | P2_UTM_CSF | {utm_csf2_ppm:+.1f} ppm |\n\n")
                
                f.write(f"> **LDP Definition:**\n> `{res['LDP_Def']}`\n\n")
                
                f.write("| ΔL1 | ΔL2 | ΔL3 | ΔL4 | ΔL5 | ΔL6 |\n")
                f.write("|:---:|:---:|:---:|:---:|:---:|:---:|\n")
                f.write(f"| {res['diff_L1']:+.3f} | *0.000 | {res['diff_L3']:+.3f} | {res['diff_L4']:+.3f} | {res['diff_L5']:+.3f} | {diff_l6_str} |\n\n")


def generate_line_descriptions(out_dir):
    """Generate and save the line descriptions lookup table."""
    line_descriptions = {
        'Line': ['L1', 'L2', 'L3', 'L4', 'L5', 'L6'],
        'LineDescr': [
            'on ellipsoid surface',
            'on ellipsoid surface , HSF applied (Ground)', 
            'on UTM grid',
            'on UTM grid , PSF applied',
            'on UTM grid , PSF&HSF (CSF) applied',
            'on LDP grid'
        ]
    }
    df = pd.DataFrame(line_descriptions)
    df.to_csv(Path(out_dir) / 'Line_Descriptions.csv', index=False)
    return df


def main():
    GADM_PATH = 'OUTPUT_PROV/gadm41_THA.gpkg'
    DEM_PATH = 'DATA/FABDEM_Thailand.vrt'
    OUT_DIR = 'OUTPUT_LDP'
    SAMPL_DIR = 'OUTPUT_SAMPL'
    FORCE_PNT_PATH = Path('DATA/ForceTestPnt.gpkg')
    
    # 0. Extract PROJ Strings from logs before running the validator
    extract_ldp_definitions(SAMPL_DIR, OUT_DIR)
    
    # 0.5. Load forced points into a dictionary for fast lookup
    force_dict = {}
    if FORCE_PNT_PATH.exists():
        print(f"Loading forced test points from {FORCE_PNT_PATH}...")
        gdf_force = gpd.read_file(FORCE_PNT_PATH, layer='ForceTestPnt')
        # Ensure projection aligns with processing requirements
        if gdf_force.crs and gdf_force.crs.to_epsg() != 4326:
            gdf_force = gdf_force.to_crs("EPSG:4326")
            
        for _, row in gdf_force.iterrows():
            if pd.notna(row.get('HASC_1')) and row.geometry:
                force_dict[row['HASC_1']] = row.geometry
        print(f"  -> Found {len(force_dict)} force points to potentially override.")
    
    # 1. Initialization
    df_line_descr = generate_line_descriptions(OUT_DIR)
    validator = LDPValidator(GADM_PATH, DEM_PATH, OUT_DIR, force_points=force_dict)
    
    # 2. Read Province Geometries
    if not Path(GADM_PATH).exists():
        raise FileNotFoundError(f"Cannot find province boundaries at {GADM_PATH}")
        
    print(f"Reading {GADM_PATH} (layer: ADM_ADM_1) ...")
    gdf_prov = gpd.read_file(GADM_PATH, layer='ADM_ADM_1')
    if gdf_prov.crs.to_epsg() != 4326:
        gdf_prov = gdf_prov.to_crs("EPSG:4326")

    # 3. Processing Loop
    results = []
    print(f"Processing {len(gdf_prov)} provinces ...")
    
    with rasterio.open(DEM_PATH) as src:
        for _, row in gdf_prov.iterrows():
            result = validator.process_province(row, src)
            if result:
                results.append(result)

    # 4. Validation: Verify all points from ForceTestPnt were used
    if force_dict:
        unused_points = set(force_dict.keys()) - validator.used_force_points
        if unused_points:
            print(f"\n⚠️ WARNING: The following HASC_1 codes in ForceTestPnt were NOT mapped to GADM geometries: {', '.join(unused_points)}")
        else:
            print("\n✅ SUCCESS: All ForceTestPnt geometries were successfully utilized.")

    # 5. Export Data and Reports
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        # Sort the DataFrame by HASC_1 ascendingly before writing outputs
        df_results = df_results.sort_values(by='HASC_1', ascending=True).reset_index(drop=True)
        
        validator.write_geopackages(df_results)
        validator.write_markdown_report(df_results, df_line_descr)
        
    print("QA/QC module execution complete.")


if __name__ == "__main__":
    main()
