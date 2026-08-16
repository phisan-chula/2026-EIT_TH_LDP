#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

targets=(./OUTPUT_*)

if ((${#targets[@]} == 0)); then
    echo "No OUTPUT_* files or directories found."
    exit 0
fi

echo "The following items will be moved to Trash:"
printf '  %q\n' "${targets[@]}"

read -r -p "Type YES to continue: " answer
[[ "$answer" == "YES" ]] || {
    echo "Cancelled."
    exit 0
}

gio trash -- "${targets[@]}"
echo "Moved ${#targets[@]} item(s) to Trash."
