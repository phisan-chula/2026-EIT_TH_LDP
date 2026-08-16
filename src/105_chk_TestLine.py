#!/usr/bin/env python3

from pathlib import Path
import pandas as pd
import geopandas as gpd

ROOT = Path("./OUTPUT_LDP")
SOURCE_LAYER = "QAQC_Line"
OUTPUT = ROOT / "AllTestLine.gpkg"
LIMIT_PPM = 20.0


def main():

    files = sorted(ROOT.glob("**/*_TestLine.gpkg"))

    # exclude output itself
    files = [
        f for f in files
        if f.resolve() != OUTPUT.resolve()
    ]

    if not files:
        print("No *_TestLine.gpkg found")
        return

    print(f"Found {len(files)} files")

    gdfs = []

    for gpkg in files:
        print(f"Read: {gpkg}")

        try:
            gdf = gpd.read_file(
                gpkg,
                layer=SOURCE_LAYER
            )

            # CSF -> ppm
            gdf["LDP_CSF1_ppm"] = (
                gdf["LDP_CSF1"] - 1.0
            ) * 1e6

            gdf["LDP_CSF2_ppm"] = (
                gdf["LDP_CSF2"] - 1.0
            ) * 1e6

            gdf["SOURCE_FILE"] = gpkg.name

            gdfs.append(gdf)

        except Exception as e:
            print(f"ERROR: {gpkg}")
            print(f"       {e}")

    if not gdfs:
        print("No valid data")
        return

    # -----------------------------------------
    # combine
    # -----------------------------------------
    crs = gdfs[0].crs

    all_gdf = gpd.GeoDataFrame(
        pd.concat(gdfs, ignore_index=True),
        geometry="geometry",
        crs=crs,
    )

    # -----------------------------------------
    # split by +/-20 ppm
    # -----------------------------------------
    within_mask = (
        (all_gdf["LDP_CSF1_ppm"].abs() <= LIMIT_PPM)
        &
        (all_gdf["LDP_CSF2_ppm"].abs() <= LIMIT_PPM)
    )

    within = all_gdf[within_mask].copy()
    over = all_gdf[~within_mask].copy()

    # -----------------------------------------
    # remove old output
    # -----------------------------------------
    if OUTPUT.exists():
        OUTPUT.unlink()

    # -----------------------------------------
    # write 2 layers
    # -----------------------------------------
    within.to_file(
        OUTPUT,
        layer="within_20ppm",
        driver="GPKG",
    )

    over.to_file(
        OUTPUT,
        layer="over_20ppm",
        driver="GPKG",
        mode="a",
    )

    # -----------------------------------------
    # report
    # -----------------------------------------
    print()
    print(f"Written: {OUTPUT}")
    print(f"Total:          {len(all_gdf):,}")
    print(f"within_20ppm:   {len(within):,}")
    print(f"over_20ppm:     {len(over):,}")

    print()
    print("HASC_1 over +/-20 ppm:")

    if over.empty:
        print("NONE")
    else:
        print(
            ", ".join(
                sorted(
                    over["HASC_1"]
                    .dropna()
                    .unique()
                )
            )
        )


if __name__ == "__main__":
    main()
