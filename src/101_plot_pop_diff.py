#!/usr/bin/env python3
import subprocess
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path
import fiona

GADM_GPKG = Path("DATA/gadm41_THA.gpkg")

def get_province_mapping(gpkg_path: Path) -> dict:
    """Read GADM GPKG and create a mapping of HASC_1 to English NAME_1."""
    if not gpkg_path.exists():
        print(f" -> Warning: GADM file not found at {gpkg_path}. Using HASC_1 codes instead.")
        return {}
    
    try:
        # 1. Identify the correct province (ADM1) layer
        layers = fiona.listlayers(gpkg_path)
        target_layer = None
        for layer in layers:
            if layer.endswith("_1") or "ADM1" in layer.upper() or "ADM_1" in layer.upper():
                target_layer = layer
                break
        
        if not target_layer and layers:
            target_layer = layers[0]
            
        print(f" -> Loading province names from {gpkg_path} (Layer: {target_layer})...")
        
        # 2. Read the layer and extract the mapping
        gdf = gpd.read_file(gpkg_path, layer=target_layer, engine="pyogrio") 
        # Fallback to standard engine if pyogrio is not installed:
        # gdf = gpd.read_file(gpkg_path, layer=target_layer)
        
        if "HASC_1" in gdf.columns and "NAME_1" in gdf.columns:
            # Create a dictionary mapping HASC_1 -> NAME_1
            mapping = dict(zip(gdf["HASC_1"], gdf["NAME_1"]))
            mapping = {str(k).strip(): str(v).strip() for k, v in mapping.items() if pd.notna(k) and str(k).strip()}
            return mapping
        else:
            print(" -> Warning: 'HASC_1' or 'NAME_1' column not found in GPKG. Using HASC_1 codes.")
            return {}
            
    except Exception as e:
        print(f" -> Error reading GPKG mapping: {e}")
        # Retry without pyogrio just in case
        try:
             gdf = gpd.read_file(gpkg_path, layer=target_layer)
             mapping = dict(zip(gdf["HASC_1"], gdf["NAME_1"]))
             return {str(k).strip(): str(v).strip() for k, v in mapping.items() if pd.notna(k) and str(k).strip()}
        except Exception:
             return {}


def main():
    # 1. Get English province mapping from GPKG
    prov_eng = get_province_mapping(GADM_GPKG)
    
    # Add a fallback for the non-standard codes you encountered earlier, 
    # just in case they differ from the official GADM 4.1 HASC_1 entries.
    fallback_mapping = {
        'TH.BM': 'Bangkok Metropolis', 'TH.SW': 'Sa Kaeo', 'TH.NR': 'Nakhon Ratchasima', 
        'TH.SI': 'Si Sa Ket', 'TH.UR': 'Ubon Ratchathani', 'TH.CY': 'Chaiyaphum', 
        'TH.KL': 'Kalasin', 'TH.NF': 'Nakhon Phanom', 'TH.NT': 'Nan', 
        'TH.MH': 'Mae Hong Son', 'TH.NS': 'Nakhon Sawan', 'TH.PH': 'Phitsanulok'
    }
    
    # Overwrite the fallbacks with actual GPKG data where available
    fallback_mapping.update(prov_eng)
    prov_eng = fallback_mapping

    # 2. Scan log files
    cmd = 'find OUT* -type f -name "*.log" -exec grep -h -A 1 "HASC_1" {} + | grep -v "^--"'
    print(" -> Scanning log files...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    lines = result.stdout.strip().split('\n')
    data = []
    
    # 3. Process Data
    for line in lines:
        if "HASC_1" in line or line.strip() == "":
            continue
            
        parts = line.split()
        if len(parts) >= 8:
            hasc_code = parts[0]
            try:
                pop2025 = int(parts[5].replace(',', ''))
                dopa_pop = int(parts[6].replace(',', ''))
                diff = int(parts[7].replace(',', ''))
                
                # Map to English name, fallback to code if not found
                eng_name = prov_eng.get(hasc_code, hasc_code)
                
                data.append({
                    'HASC_1': hasc_code,
                    'Province': eng_name,
                    'POP2025': pop2025,
                    'DOPA_Pop': dopa_pop,
                    'Diff': diff
                })
            except ValueError:
                pass

    if not data:
        print("No valid population data found in logs.")
        return

    # 4. Create DataFrame and Sort
    df = pd.DataFrame(data)
    df = df.sort_values(by='Diff', ascending=False).reset_index(drop=True)
    
    print("\n================ Population Difference Summary ================")
    print(df[['Province', 'HASC_1', 'POP2025', 'DOPA_Pop', 'Diff']].to_string(index=False))
    print("===============================================================\n")

    # 5. Plot Bar Chart (Standard Matplotlib Fonts)
    plt.figure(figsize=(18, 9))
    
    colors = ['#1f77b4' if x > 0 else '#d62728' for x in df['Diff']]
    
    bars = plt.bar(df['Province'], df['Diff'], color=colors, edgecolor='black', linewidth=0.5)
    
    plt.title('Population Difference by Province (POP2025 vs DOPA_Pop)', fontsize=18, fontweight='bold', pad=20)
    plt.xlabel('Province', fontsize=14, labelpad=10)
    plt.ylabel('Difference (Persons)', fontsize=14, labelpad=10)
    
    # Format Y-axis with commas
    plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    plt.tick_params(axis='y', labelsize=12)
    
    plt.axhline(0, color='black', linewidth=1.5)
    
    # Set X-axis labels
    plt.xticks(rotation=90, fontsize=11)
    
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    # Save the output image
    out_img = 'POP_Diff_Chart_EN.png'
    plt.savefig(out_img, dpi=300, bbox_inches='tight')
    print(f" -> Bar chart saved successfully as: {out_img}")

if __name__ == "__main__":
    main()
