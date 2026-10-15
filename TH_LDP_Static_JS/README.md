# TH-LDP Static Province Map
HTML/CSS/JavaScript-only map; no Rust or WASM. Original tested package: TH_LDP_Static_JS_Fixed.zip. Simplification is 250 metres using GDAL and EPSG:32647. Province selection and coordinate point-in-polygon use JavaScript.

## Local testing
Run from repository root:
```bash
sudo apt-get install -y gdal-bin
python3 TH_LDP_Static_JS/scripts/01_simplify.py
cd TH_LDP_Static_JS/web
python3 -m http.server 8000
```
Open http://localhost:8000.

## Deployment
GitHub Actions at .github/workflows/deploy-ldp-webmap.yml generates the GeoJSON at build time from src/OUTPUT_PROV/gadm41_THA.gpkg and publishes the web folder.
Set Settings > Pages > Source to GitHub Actions, then run the workflow. Public URL:
https://phisan-chula.github.io/2026-EIT_TH_LDP/TH_LDP_Static_JS/

Leaflet/OpenStreetMap basemap requires internet connectivity. GitHub link targets are derived from the selected HASC_1.
