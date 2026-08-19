#!/usr/bin/env bash

# Usage:
#   ./run_4_only.sh TH.AC   # Run single
#   ./run_4_only.sh ALL     # Run all concurrently

TARGET="${1:-ALL}"
MAX_JOBS="${MAX_JOBS:-16}"

if [[ "${TARGET^^}" == "ALL" ]]; then
    # Parse TOML headers and run concurrently without log redirection
    awk -F'[""]' '/^\["TH\./ {print $2}' PROV_LDP.toml | sort -u | \
        xargs -r -n 1 -P "$MAX_JOBS" bash -c 'python3 4_analyse_ldp.py "$1" -t PROV_LDP.toml' _
else
    # Run a single target directly
    python3 4_analyse_ldp.py "$TARGET" -t PROV_LDP.toml
fi
