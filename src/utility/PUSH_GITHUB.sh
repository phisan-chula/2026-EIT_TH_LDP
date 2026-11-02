#!/bin/bash
set -e
set -x

# Normal files in current directory only
find . -maxdepth 1 -type f -print0 | xargs -0 git add --

# README.md one level above
git add -- '../README.md'

# Selected outputs/subdirectories
git add -- \
  './OUTPUT_LDP/README.md' \
  './OUTPUT_LDP/TH_*/TH_*_OnePage.pdf' \
  './OUTPUT_LDP/TH_*/TH_*_LDP.gpkg' \
  './OUTPUT_SAMPL/TH_*/TH_*_pipeline.log' \
  './OUTPUT_LDP/TH_AT/TH_AT_LDP_CRS.WKT' \
  './OUTPUT_PROV/' \
  './DATA/'

git status

if ! git diff --cached --quiet; then
    git commit -m "docs: update LDP source and outputs"
fi

git pull --rebase origin main
git push origin main

set +x
