import argparse
import sys
import os
import geopandas as gpd
import pandas as pd
from typing import Optional, Dict, Any, List

def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate cumulative POP, point counts, and %POP based on HASC_1."
    )
    parser.add_argument(
        '--hasc_1', 
        type=str,
        nargs='+',
        default=['TH.MH_S', 'TH.TK_C', 'TH.MH_N', 'TH.CM_S'],
        help="List of HASC_1 attributes (e.g., '--hasc_1 TH.AC TH.UD_E'). Defaults to TH.MH_S, TH.TK_C, TH.MH_N, TH.CM_S."
    )
    return parser.parse_args()


def load_and_filter_data(filepath: str, hasc_filter: str) -> Optional[gpd.GeoDataFrame]:
    """Reads the Point layer from the GeoPackage and applies the HASC_1 filter."""
    if not os.path.exists(filepath):
        print(f"Warning: The file '{filepath}' does not exist. Skipping {hasc_filter}.")
        return None

    try:
        gdf = gpd.read_file(filepath, layer='Point')
    except Exception as e:
        print(f"Warning: Error reading the GeoPackage '{filepath}': {e}. Skipping.")
        return None

    # Filter data for the specific HASC code
    gdf = gdf[gdf['HASC_1'] == hasc_filter]

    if gdf.empty:
        print(f"Warning: No points found matching HASC_1 == '{hasc_filter}'. Skipping.")
        return None

    return gdf


def summarize_cumulative_data(gdf: gpd.GeoDataFrame, hasc_1: str) -> Dict[str, Any]:
    """Calculates cumulative %POP for specific thresholds and formats them as a row."""
    # Calculate the grand total for ALL points matching the HASC_1 filter
    total_pop_all = gdf['POP'].sum()
    
    # Initialize dictionary for the wide-format row
    row_result = {'HASC_1': hasc_1}
    
    thresholds = [20, 50, 100]
    
    for t in thresholds:
        if total_pop_all > 0:
            # Create a mask for all points where absolute CSF_ppm is < threshold
            mask = gdf['CSF_ppm'].abs() < t
            category_pop_sum = gdf[mask]['POP'].sum()
            
            # Calculate %POP and format as integer percentage string
            percent_pop = (category_pop_sum / total_pop_all * 100)
            row_result[f'+/-{t}ppm'] = f"{int(round(percent_pop))}%"
        else:
            row_result[f'+/-{t}ppm'] = "0%"
            
    # Append the all_points column dynamically
    row_result['all_points'] = "100%"
        
    return row_result


def main():
    # 1. Setup and parse arguments
    args = parse_arguments()

    results: List[Dict[str, Any]] = []

    # 2. Loop through all provided HASC_1 codes
    for hasc in args.hasc_1:
        # Transforms "TH.UD_E" into "TH_UD_E" to match your folder/file naming convention
        hasc_safe = hasc.replace('.', '_')
        gpkg_path = f"OUTPUT_LDP/{hasc_safe}/{hasc_safe}_LDP.gpkg"

        # 3. Extract and filter data
        gdf = load_and_filter_data(gpkg_path, hasc)

        # 4. If data is valid, calculate the summary and append to results
        if gdf is not None:
            summary_row = summarize_cumulative_data(gdf, hasc)
            results.append(summary_row)

    if not results:
        print("\nNo valid data could be processed for the provided HASC_1 codes.")
        sys.exit(1)

    # 5. Convert the list of dictionaries into a wide-format DataFrame
    summary_table = pd.DataFrame(results)

    # 6. Display results in the requested format
    print("\n" + "=" * 70)
    print(" CUMULATIVE %POP COVERAGE SUMMARY")
    print("=" * 70 + "\n")
    
    # Render table as Markdown
    print(summary_table.to_markdown(index=False, tablefmt="pipe"))
    print("\n")


if __name__ == "__main__":
    main()
