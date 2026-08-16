set -x

# 1. Stage the files (Note the added \ after './src/*')
git add -- \
  './src/*' \
  './README.md' \
  './OUTPUT_LDP/README.md' \
  './src/OUTPUT_LDP/TH_*/TH_*_OnePage.pdf' \
  './src/OUTPUT_LDP/TH_*/TH_*_LDP.gpkg' \
  './src/OUTPUT_SAMPL/TH_*/TH_*_pipeline.log' \
  './src/OUTPUT_LDP/TH_AT/TH_AT_LDP_CRS.WKT' \
  './src/OUTPUT_PROV/' \
  './src/DATA/'

# 2. Verify what was actually staged (crucial when using wildcards)
git status

# 3. Commit the changes with a descriptive message
git commit -m "docs: expose LDP source code, update README, and add GeoPackage/WKT outputs"

# 4. Push to your remote repository (assuming your branch is 'main')
git push origin main

# Turn off bash debugging
set +x
