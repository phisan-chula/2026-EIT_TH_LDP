# TH-LDP Online Province Map
Static GitHub Pages deployment of the TH-LDP province/region map. Uses Leaflet and browser-side polygon click selection. No continuously running server is needed.

Source: `src/OUTPUT_PROV/gadm41_THA.gpkg`. The GitHub Actions workflow installs GDAL, runs `scripts/01_simplify.py` (250 m tolerance in EPSG:32647), and publishes the generated GeoJSON together with `index.html`.

Public URL after enabling GitHub Pages Actions source:
https://phisan-chula.github.io/2026-EIT_TH_LDP/EIT_LDP_Rust_WebMap/

Navigate to repository Settings > Pages and set Build and deployment > Source to **GitHub Actions**. Open Actions > Deploy Thailand LDP Web Map > Run workflow if it did not run automatically.

Important: This GitHub Pages version runs point selection in the browser (Leaflet). The separate Axum Rust backend from the downloadable package is intended for a VPS or local server, not GitHub Pages. LDP resource links are inferred from HASC_1 and are not validated for existence.
