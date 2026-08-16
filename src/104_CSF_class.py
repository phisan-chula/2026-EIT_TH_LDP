import argparse
import sys
import os
import geopandas as gpd
import pandas as pd

def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate cumulative POP, point counts, and %POP based on HASC_1."
    )
    # Changed from --has_1 to --hasc_1 and made it required
    parser.add_argument(
        '--hasc_1', 
        type=str, 
        required=True,
        help="HASC_1 attribute (e.g., 'TH.UD_E'). Used to filter data and build the GPKG path."
    )
    return parser.parse_args()


def load_and_filter_data(filepath: str, hasc_filter: str) -> gpd.GeoDataFrame:
    """Reads the Point layer from the GeoPackage and applies the HASC_1 filter."""
    print(f"Reading layer 'Point' from {filepath} ...")
    
    if not os.path.exists(filepath):
        print(f"Error: The file '{filepath}' does not exist.")
        sys.exit(1)

    try:
        gdf = gpd.read_file(filepath, layer='Point')
    except Exception as e:
        print(f"Error reading the GeoPackage: {e}")
        sys.exit(1)

    print(f"Filtering data where HASC_1 == '{hasc_filter}' ...")
    gdf = gdf[gdf['HASC_1'] == hasc_filter]

    if gdf.empty:
        print(f"No points found matching HASC_1 == '{hasc_filter}'.")
        sys.exit(0)

    return gdf


def summarize_cumulative_data(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """Calculates cumulative counts, POP sums, and %POP for specific thresholds."""
    
    # Calculate the grand total for ALL points matching the HASC_1 filter
    total_pop_all = gdf['POP'].sum()
    total_points_all = len(gdf)
    
    thresholds = [20, 50, 100]
    results = []
    
    for t in thresholds:
        # Create a mask for all points where absolute CSF_ppm is < threshold
        mask = gdf['CSF_ppm'].abs() < t
        subset = gdf[mask]
        
        category_pop_sum = subset['POP'].sum()
        
        # Calculate %POP (handling division by zero)
        percent_pop = (category_pop_sum / total_pop_all * 100) if total_pop_all > 0 else 0
        
        results.append({
            'CSF_ppm_Range': f'< +/-{t} ppm',
            'point_count': len(subset),
            'total_POP': category_pop_sum,
            '%POP': round(percent_pop, 2)
        })
        
    # Append the grand total row at the end
    results.append({
        'CSF_ppm_Range': 'All Points',
        'point_count': total_points_all,
        'total_POP': total_pop_all,
        '%POP': 100.00
    })
        
    return pd.DataFrame(results)


def main():
    # 1. Setup and parse arguments
    args = parse_arguments()

    # 2. Build the GeoPackage path based on the HASC_1 pattern
    # Transforms "TH.UD_E" into "TH_UD_E" to match your folder/file naming convention
    hasc_1_safe = args.hasc_1.replace('.', '_')
    gpkg_path = f"OUTPUT_LDP/{hasc_1_safe}/{hasc_1_safe}_LDP.gpkg"

    # 3. Extract and filter data
    gdf = load_and_filter_data(gpkg_path, args.hasc_1)

    # 4. Generate the cumulative summary
    summary_table = summarize_cumulative_data(gdf)

    # 5. Display results
    print("\n" + "=" * 65)
    print(f" CUMULATIVE POINT COUNT, POP, AND %POP FOR {args.hasc_1}")
    print("=" * 65)
    print(summary_table.to_markdown(index=False, tablefmt="grid"))


if __name__ == "__main__":
    main()
