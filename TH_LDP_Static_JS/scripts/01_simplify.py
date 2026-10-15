#!/usr/bin/env python3
"""Create GitHub Pages GeoJSON at a fixed 250 metre simplification tolerance."""
from pathlib import Path
import subprocess, tempfile, json, sys
TOL_METERS = 250.0
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/OUTPUT_PROV/gadm41_THA.gpkg"
OUTPUT = ROOT / "TH_LDP_Static_JS/web/data/provinces.geojson"
def run(*args):
    print(" ".join(map(str,args)),flush=True)
    subprocess.run(list(map(str,args)),check=True)
if not SOURCE.is_file():
    sys.exit(f"Source GeoPackage not found: {SOURCE}")
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir)/"projected.gpkg"
    run("ogr2ogr","-f","GPKG",tmp,SOURCE,"-t_srs","EPSG:32647","-nln","province","-select","HASC_1,NAME_1,LDP")
    run("ogr2ogr","-f","GeoJSON",OUTPUT,tmp,"-t_srs","EPSG:4326","-simplify",TOL_METERS,"-lco","RFC7946=YES","-lco","COORDINATE_PRECISION=6")
data=json.loads(OUTPUT.read_text())
if not data.get("features") or any(not f.get("properties",{}).get("HASC_1") for f in data["features"]):
    sys.exit("Invalid province GeoJSON or missing HASC_1")
print(f"Created {len(data['features'])} regions at {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
