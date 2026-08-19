#!/usr/bin/env bash

# Run the full map-projection pipeline (Steps 1 through 6).
# Usage:
#   ./run_pipeline.sh TH.AC   # Runs pipeline for a single province
#   ./run_pipeline.sh ALL     # Runs pipeline concurrently for all provinces

set -Eeuo pipefail

readonly MAX_JOBS="${MAX_JOBS:-16}"
readonly PYTHON_BIN="${PYTHON_BIN:-python3}"

readonly SCRIPT_1="${SCRIPT_1:-1_fabdem_province.py}"
readonly SCRIPT_2="${SCRIPT_2:-2_popu2025_grid.py}"
readonly SCRIPT_3="${SCRIPT_3:-3_generate_sample.py}"
readonly SCRIPT_4="${SCRIPT_4:-4_analyse_ldp.py}"
readonly SCRIPT_5="${SCRIPT_5:-5_plot_PP_PctPopu.py}"
readonly SCRIPT_6="${SCRIPT_6:-6_LDP_OnePage.py}"

readonly OUTPUT_ROOT="${OUTPUT_ROOT:-OUTPUT_SAMPL}"

export PYTHON_BIN SCRIPT_1 SCRIPT_2 SCRIPT_3 SCRIPT_4 SCRIPT_5 SCRIPT_6 OUTPUT_ROOT

log_error() {
    printf 'Error: %s\n' "$*" >&2
}

check_requirements() {
    local script

    command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
        log_error "Python executable not found: $PYTHON_BIN"
        exit 1
    }

    printf 'Checking required Python scripts...\n'
    for script in "$SCRIPT_1" "$SCRIPT_2" "$SCRIPT_3" "$SCRIPT_4" "$SCRIPT_5" "$SCRIPT_6"; do
        if [[ ! -f "$script" ]]; then
            log_error "Could not find '$script' in $(pwd)"
            exit 1
        fi
    done
}

get_provinces() {
    "$PYTHON_BIN" "$SCRIPT_1" --list-provinces \
        | awk '$1 ~ /^TH\.[A-Za-z0-9_-]+$/ {print $1}' \
        | sort -u
}

run_python_step() {
    local province="$1"
    local step="$2"

    case "$step" in
        1)
            printf '%s\n' "--> [$province] Step 1: $SCRIPT_1"
            "$PYTHON_BIN" "$SCRIPT_1" -p "$province" --overwrite
            ;;
        2)
            printf '%s\n' "--> [$province] Step 2: $SCRIPT_2"
            "$PYTHON_BIN" "$SCRIPT_2" -p "$province" --overwrite
            ;;
        3)
            printf '%s\n' "--> [$province] Step 3: $SCRIPT_3"
            "$PYTHON_BIN" "$SCRIPT_3" -p "$province" --grid 500 --overwrite
            ;;
        4)
            printf '%s\n' "--> [$province] Step 4: $SCRIPT_4"
            "$PYTHON_BIN" "$SCRIPT_4" "$province"
            ;;
        5)
            printf '%s\n' "--> [$province] Step 5: $SCRIPT_5"
            "$PYTHON_BIN" "$SCRIPT_5" "$province"
            ;;
        6)
            printf '%s\n' "--> [$province] Step 6: $SCRIPT_6"
            "$PYTHON_BIN" "$SCRIPT_6" --hasc "$province"
            ;;
        *)
            log_error "Unknown pipeline step: $step"
            return 2
            ;;
    esac
}

process_province() {
    local province="$1"

    # Keep the official HASC_1 code (e.g. TH.KK) for GADM/TOML lookups,
    # but use a filesystem-safe code (e.g. TH_KK) for directories/files.
    local province_fs="${province//./_}"
    local out_dir="${OUTPUT_ROOT}/${province_fs}"
    local log_file="${out_dir}/${province_fs}_pipeline.log"
    local step

    mkdir -p "$out_dir"
    printf '%s\n' "--> [$province] Starting (log: $log_file)"

    if (
        printf '%s\n' '======================================================================'
        printf 'Processing province: %s\n' "$province"
        printf 'Started: %s\n' "$(date --iso-8601=seconds)"
        printf '%s\n' '======================================================================'

        for step in 1 2 3 4 5 6; do
            run_python_step "$province" "$step" || exit $?
        done

        printf '%s\n' '======================================================================'
        printf 'Completed province: %s\n' "$province"
        printf 'Finished: %s\n' "$(date --iso-8601=seconds)"
        printf '%s\n' '======================================================================'
    ) >"$log_file" 2>&1; then
        printf '%s\n' "--> [$province] Finished successfully"
    else
        local status=$?
        printf '%s\n' "--> [$province] FAILED (exit $status; see $log_file)" >&2
        return "$status"
    fi
}

export -f log_error run_python_step process_province

main() {
    if [ -z "${1:-}" ]; then
        echo "Error: Missing argument."
        echo "Usage: $0 <HASC_1 | ALL>"
        echo "Example (Single): $0 TH.AC"
        echo "Example (All):    $0 ALL"
        exit 1
    fi

    local target="$1"
    check_requirements

    if [[ "${target^^}" == "ALL" ]]; then
        local -a provinces
        local total

        printf 'Reading province codes from %s...\n' "$SCRIPT_1"
        mapfile -t provinces < <(get_provinces)

        if (( ${#provinces[@]} == 0 )); then
            log_error 'No province codes were returned. Check the default GADM path and --list-provinces output.'
            exit 1
        fi

        total=${#provinces[@]}
        printf 'Found %d provinces.\n' "$total"
        printf 'Running up to %s provinces concurrently.\n\n' "$MAX_JOBS"

        if ! printf '%s\n' "${provinces[@]}" \
            | xargs -r -n 1 -P "$MAX_JOBS" bash -c 'process_province "$1"' _; then
            log_error 'One or more provinces failed. Review the per-province log files.'
            exit 1
        fi

        printf '%s\n' '======================================================================'
        printf 'Batch processing completed successfully for all %d provinces.\n' "$total"
        printf 'Logs: %s/{HASC_1_WITH_UNDERSCORE}/{HASC_1_WITH_UNDERSCORE}_pipeline.log\n' "$OUTPUT_ROOT"
        printf '%s\n' '======================================================================'
    else
        # Process a single province
        process_province "$target"
    fi
}

main "$@"
