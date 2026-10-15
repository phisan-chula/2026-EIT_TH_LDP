#!/usr/bin/env python3
"""Generate GeoJSON for GitHub Pages. Tolerance fixed at 250 metres."""
import json,subprocess,tempfile
from pathlib import Path
TOLERANCE_METERS=250.0
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'src/OUTPUT_PROV/gadm41_THA.gpkg'
DEST=ROOT/'EIT_LDP_Rust_WebMap/provinces.geojson'
def cmd(*args): subprocess.run(list(map(str,args)),check=True)
if not SOURCE.exists(): raise SystemExit(f'Missing {SOURCE}')
with tempfile.TemporaryDirectory() as d:
 projected=Path(d)/'projected.gpkg'
 simplified=Path(d)/'simplified.gpkg'
 # Use a metres-based projection before Douglas-Peucker simplification.
 cmd('ogr2ogr','-f','GPKG',projected,SOURCE,'-t_srs','EPSG:32647','-select','HASC_1,NAME_1,LDP','-nln','regions')
 cmd('ogr2ogr','-f','GPKG',simplified,projected,'-simplify',TOLERANCE_METERS,'-nln','regions')
 cmd('ogr2ogr','-f','GeoJSON',DEST,simplified,'-t_srs','EPSG:4326','-lco','RFC7946=YES','-lco','COORDINATE_PRECISION=6')
 features=json.loads(DEST.read_text()).get('features',[])
 if not features or any(not f.get('properties',{}).get('HASC_1') for f in features):
  raise RuntimeError('Missing features or HASC_1')
 print(f'Created {DEST}: {len(features)} features, {DEST.stat().st_size} bytes')
