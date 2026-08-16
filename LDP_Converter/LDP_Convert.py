import re
import pandas as pd
import geopandas as gpd
import pyproj
import pygeodesy as pgd
from pathlib import Path

class LDPTransformer:
    def __init__(self, raw_text):
        self.raw_text = raw_text.strip()
        self.ldp_proj = None
        self.points_data = []
        
        # Load Geoid model for Undulation calculation
        self.geoid = None
        tgm_paths = [
            "/usr/share/GeographicLib/geoids/tgm2017-1.pgm",
            Path(__file__).resolve().parent / "tgm2017-1.pgm"
        ]
        for p in tgm_paths:
            if Path(p).is_file():
                try:
                    self.geoid = pgd.geoids.GeoidKarney(str(p))
                    break
                except Exception:
                    pass

    def parse_input(self):
        lines = self.raw_text.split('\n')
        
        for line in lines:
            # 1. Strip comments: keep everything before the first '#'
            line = line.split('#')[0].strip()
            
            # 2. Skip if the line is now empty (was fully a comment or blank)
            if not line:
                continue
                
            # 3. The first valid line encountered becomes the PROJ string
            if self.ldp_proj is None:
                self.ldp_proj = line.strip('\'"')
            
            # 4. All subsequent valid lines are treated as coordinate data
            else:
                # Strip out empty strings resulting from multiple spaces/commas
                parts = [p for p in re.split(r'[,\s]+', line) if p]
                
                if len(parts) >= 5:
                    name = parts[0]
                    epsg_code = parts[1].upper()
                    
                    # Normalize EPSG format
                    epsg = epsg_code if epsg_code.startswith("EPSG:") else f"EPSG:{epsg_code}"
                    
                    coord1 = float(parts[2]) # Lat or Easting
                    coord2 = float(parts[3]) # Lng or Northing
                    msl = float(parts[4])
                    
                    self.points_data.append({
                        'Name': name, 
                        'Source_CRS': epsg,
                        'Coord1': coord1,
                        'Coord2': coord2,
                        'MSL': msl
                    })

    def transform(self):
        self.parse_input()
        
        if not self.ldp_proj:
            return "Error: No PROJ string found in input."
        if not self.points_data:
            return "Error: No valid coordinate points found."

        # Unify all incoming points to WGS84 (EPSG:4326)
        unified_points = []
        for pt in self.points_data:
            try:
                if pt['Source_CRS'] == "EPSG:4326":
                    lat, lon = pt['Coord1'], pt['Coord2']
                else:
                    # For projected CRSs: Coord1 = Easting (X), Coord2 = Northing (Y)
                    transformer = pyproj.Transformer.from_crs(pt['Source_CRS'], "EPSG:4326", always_xy=True)
                    lon, lat = transformer.transform(pt['Coord1'], pt['Coord2'])
                
                unified_points.append({
                    'Name': pt['Name'],
                    'Source_CRS': pt['Source_CRS'],
                    'Lat': lat,
                    'Lon': lon,
                    'MSL': pt['MSL']
                })
            except Exception as e:
                return f"Error transforming {pt['Name']} from {pt['Source_CRS']}: {str(e)}"

        df = pd.DataFrame(unified_points)
        gdf = gpd.GeoDataFrame(
            df, 
            geometry=gpd.points_from_xy(df.Lon, df.Lat), 
            crs="EPSG:4326"
        )
        
        try:
            gdf_ldp = gdf.to_crs(self.ldp_proj)
            proj_obj = pyproj.Proj(self.ldp_proj)
            ellps = pgd.datums.Ellipsoids.WGS84
        except Exception as e:
            return f"Projection Error: {str(e)}"

        output_lines = ["Name, LDP_E, LDP_N, MSL, CSF_ppm"]
        
        for idx, row in gdf_ldp.iterrows():
            lat = df.loc[idx, 'Lat']
            lon = df.loc[idx, 'Lon']
            msl = df.loc[idx, 'MSL']
            
            # --- CSF Algorithm ---
            undul = self.geoid.height(lat, lon) if self.geoid else 0.0
            h = undul + msl
            rg = ellps.rocGauss(lat)
            hsf = rg / (rg + h)
            psf = proj_obj.get_factors(lon, lat).meridional_scale
            csf = psf * hsf
            csf_ppm = (csf - 1) * 1E6
            # ---------------------
            
            east = f"{row.geometry.x:.4f}"
            north = f"{row.geometry.y:.4f}"
            
            # Determine if the warning emoji is needed
            alert = " ❗️" if csf_ppm < -20 or csf_ppm > 20 else ""
            
            # Format cleanly with spacing and append the alert if applicable
            output_lines.append(f"{row['Name']:<12} {east:<14} {north:<14} {msl:<5} {csf_ppm:+.1f}{alert}")

        return "\n".join(output_lines)

if __name__ == "__main__":
    # The first uncommented line MUST be the PROJ string.
    # Subsequent lines MUST follow the format: Name EPSG Coord1 Coord2 MSL
    
    raw_input_data = """
    # --- Custom LDP Definition ---
    +proj=tmerc +lat_0=13.73 +lon_0=100.53 +k=1.000000 +x_0=40000 +y_0=140000 +ellps=WGS84 +units=m +no_defs
    
    # --- Coordinate Data (Name, Source_CRS, Easting/Lon, Northing/Lat, MSL) ---
    VICT_MONU    32647    665200.0    1522000.0    15.0
    SRI_AYUTH    32647    664800.0    1521200.0    18.0
    SIAM_SQ      32647    664400.0    1519900.0    30.0
    Y3_MITR      32647    664100.0    1518400.0    20.5
    VICT_MONU    32647    665200.0    1522000.0   -17.0
    SRI_AYUTH    32647    664800.0    1521200.0   -20.0
    SIAM_SQ      32647    664400.0    1519900.0   -32.0
    Y3_MITR      32647    664100.0    1518400.0   -22.5
    """
    
    # Initialize transformer and run
    transformer = LDPTransformer(raw_input_data)
    result = transformer.transform()
    
    # Print the output table
    print(result)
