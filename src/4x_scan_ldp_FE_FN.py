#!/usr/bin/env python3
"""Summarize provincial LDP pipeline logs and compute rounded FE/FN shifts."""

import argparse
import fnmatch
import json
import re
import os
import shutil
import tempfile
try:
    import tomllib          # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib # Python 3.10 or older
from datetime import datetime
from pathlib import Path

import pandas as pd

COORD_RANGE_CENTER = {
     "L": 32_500,   "M": 55_000,   "U": 77_500,
    "LL": 325_000, "MM": 550_000, "UU": 775_000,
}

# Rows: E coordinate range; columns: N coordinate range.
SHIFT_TABLE = (
    (("L", "U"), ("L", "LL"), ("L", "LL")),
    (("M", "LL"), ("M", "LL"), ("M", "LL")),
    (("LL", "UU"), ("LL", "UU"), ("LL", "UU")),
)

ROWS = ("min", "max", "diff")
TABLE_ROW_RE = re.compile(
    r"^\s*\|\s*(min|max|diff)\s*\|\s*([^|]+)\|\s*([^|]+)\|",
    re.IGNORECASE | re.MULTILINE,
)

BASE_COLUMNS = [
    "Province", "LDP_E_min", "LDP_E_max", "LDP_E_diff",
    "LDP_N_min", "LDP_N_max", "LDP_N_diff", "FE", "FN",
]
SHIFT_COLUMNS = ["E_Center", "N_Center", "E_Target", "N_Target", "NewFE", "NewFN"]


def parse_number(value: str) -> float:
    return float(value.strip().replace(",", ""))


def proj_parameter(proj: str, parameter: str) -> float:
    match = re.search(rf"(?:^|\s)\+{re.escape(parameter)}=([^\s]+)", proj)
    if not match:
        raise ValueError(f"Missing +{parameter} in PROJ_String_Decimal")
    return float(match.group(1))


def extract_definition(text: str) -> dict:
    decoder = json.JSONDecoder()
    for line in text.splitlines():
        if 'LDP_Definition' not in line:
            continue
        for match in re.finditer(r"\{", line):
            try:
                obj, _ = decoder.raw_decode(line[match.start():])
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and obj.get("meta") == "LDP_Definition":
                return obj
    raise ValueError('No valid JSON object with meta="LDP_Definition"')


def read_log(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    result = {"Province": path.parent.name}
    matches = {}
    for match in TABLE_ROW_RE.finditer(text):
        key = match.group(1).lower()
        # Keep the last complete table if the report includes multiple stages.
        matches[key] = (parse_number(match.group(2)), parse_number(match.group(3)))

    missing = set(ROWS) - matches.keys()
    if missing:
        raise ValueError(f"Missing Markdown table rows: {', '.join(sorted(missing))}")
    for name in ROWS:
        result[f"LDP_E_{name}"], result[f"LDP_N_{name}"] = matches[name]

    definition = extract_definition(text)
    proj = definition.get("PROJ_String_Decimal", "")
    result["FE"] = proj_parameter(proj, "x_0")
    result["FN"] = proj_parameter(proj, "y_0")
    return result


def range_class(span: float) -> int:
    """Classes: 0–50 km, >50–100 km, >100–200 km."""
    if 0 <= span <= 50_000:
        return 0
    if span <= 100_000 and span > 50_000:
        return 1
    if span <= 200_000 and span > 100_000:
        return 2
    raise ValueError(f"Unsupported coordinate span: {span:,.3f} m")


def calculate_shift(row: dict) -> dict:
    """Offset existing FE/FN so each coordinate midpoint hits its chosen target.

    New FE/FN are rounded to the nearest 1,000 m (half up).
    """
    e_code, n_code = SHIFT_TABLE[
        range_class(row["LDP_E_diff"])
    ][range_class(row["LDP_N_diff"])]
    target_e = COORD_RANGE_CENTER[e_code]
    target_n = COORD_RANGE_CENTER[n_code]
    e_mid = (row["LDP_E_min"] + row["LDP_E_max"]) / 2
    n_mid = (row["LDP_N_min"] + row["LDP_N_max"]) / 2

    def nearest_thousand(value: float) -> int:
        # Positive FE/FN are expected; use symmetric half-away-from-zero rounding.
        import math
        return (1 if value >= 0 else -1) * int(math.floor(abs(value) / 1000 + 0.5)) * 1000

    return {
        "E_Center": e_code,
        "N_Center": n_code,
        "E_Target": target_e,
        "N_Target": target_n,
        "NewFE": nearest_thousand(row["FE"] + target_e - e_mid),
        "NewFN": nearest_thousand(row["FN"] + target_n - n_mid),
    }


def scan_logs(root: Path, selection: str = "ALL") -> tuple[pd.DataFrame, list[str]]:
    pattern = selection.upper().replace(".", "*")
    if pattern == "ALL":
        pattern = "TH_*"
    elif not pattern.startswith("TH_") and not any(ch in pattern for ch in "*?[]"):
        pattern = f"TH_{pattern}"

    paths = sorted(
        path for path in root.glob("TH_*/TH_*_pipeline.log")
        if fnmatch.fnmatchcase(path.parent.name.upper(), pattern)
        and path.stem == f"{path.parent.name}_pipeline"
    )
    results, warnings = [], []
    for path in paths:
        try:
            row = read_log(path)
            row.update(calculate_shift(row))
            results.append(row)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            warnings.append(f"{path}: {exc}")
    return pd.DataFrame(results, columns=BASE_COLUMNS + SHIFT_COLUMNS), warnings



def update_province_toml(toml_path: Path, df: pd.DataFrame) -> tuple[Path, list[str]]:
    """Back up TOML, then update FALSE_EN for provinces with calculated shifts.

    Preserves existing section order, comments, and unrelated keys. Does not
    touch provinces absent from df. Returns backup path and update notes.
    """
    if df.empty:
        raise ValueError("No computed provinces to write")
    if not toml_path.is_file():
        raise FileNotFoundError(toml_path)

    data = toml_path.read_bytes()
    existing = tomllib.loads(data.decode("utf-8-sig"))
    # Exact mapping: TH_AC -> TH.AC, TH_CM_N -> TH.CM_N
    calculated = {}
    for _, row in df.iterrows():
        section = str(row["Province"]).replace("TH_", "TH.", 1)
        calculated[section] = (int(row["NewFE"]), int(row["NewFN"]))

    header_re = re.compile(r'^\s*\[\s*["\'](TH\.[A-Za-z0-9_]+)["\']\s*\]\s*(?:#.*)?$')
    value_re = re.compile(r'^(\s*FALSE_EN\s*=\s*)(?:"AUTO"|\[[^\]\r\n]*\])([^\r\n]*)$')
    original = data.decode("utf-8-sig")
    lines = original.splitlines(keepends=True)
    current, updated, seen, notes = None, set(), set(), []
    output = []

    def insert_if_missing(section):
        if section in calculated and section not in updated:
            e, n = calculated[section]
            output.append(f"FALSE_EN = [{e}, {n}]\n")
            updated.add(section)
            notes.append(f"{section}: inserted FALSE_EN = [{e}, {n}]")

    for line in lines:
        match = header_re.match(line.rstrip("\r\n"))
        if match:
            insert_if_missing(current)
            current = match.group(1)
            seen.add(current)
            output.append(line)
            continue
        if current in calculated:
            match = value_re.match(line.rstrip("\r\n"))
            if match:
                if current in updated:
                    raise ValueError(f"Duplicate FALSE_EN in [{current}]")
                e, n = calculated[current]
                suffix = match.group(2)
                newline = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
                output.append(f"{match.group(1)}[{e}, {n}]{suffix}{newline}")
                updated.add(current)
                notes.append(f"{current}: FALSE_EN = [{e}, {n}]")
                continue
        output.append(line)
    insert_if_missing(current)
    missing = sorted(set(calculated) - seen)
    if missing:
        notes.append("No matching TOML section (skipped): " + ", ".join(missing))
    if not updated:
        raise ValueError("No matching TOML provinces; file left unchanged")

    result = "".join(output)
    parsed_result = tomllib.loads(result)
    for section in updated:
        if section not in existing:
            raise ValueError(f"Unexpected section [{section}]")
        if parsed_result[section]["FALSE_EN"] != list(calculated[section]):
            raise ValueError(f"Failed to validate [{section}].FALSE_EN")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup = toml_path.with_name(f"{toml_path.name}.{stamp}.bak")
    shutil.copy2(toml_path, backup)   # Backup first, never overwrite a backup.
    fd, temporary = tempfile.mkstemp(prefix=f".{toml_path.name}.", suffix=".tmp", dir=toml_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as file:
            file.write(result)
        shutil.copymode(toml_path, temporary)
        os.replace(temporary, toml_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    notes.append(f"Updated {len(updated)} TOML sections")
    return backup, notes

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selection", nargs="?", default="ALL", help="ALL, TH_AC, TH_A*, TH.*")
    parser.add_argument("--root", type=Path, default=Path("OUTPUT_SAMPL"))
    parser.add_argument("--output", type=Path, default=Path("LDP_Coordinate_Shift.csv"))
    parser.add_argument("--toml", type=Path, default=Path("PROV_LDP.toml"))
    parser.add_argument("--update-toml", action="store_true", help="Back up TOML, then write NewFE/NewFN to matching province sections")
    args = parser.parse_args()

    df, warnings = scan_logs(args.root, args.selection)
    for message in warnings:
        print(f"WARNING: {message}")
    if df.empty:
        print("No valid matching logs found.")
        return

    with pd.option_context("display.max_columns", None, "display.width", 220, "display.float_format", "{:,.3f}".format):
        print(df.to_string(index=False))

    for column in ("LDP_E_diff", "LDP_N_diff"):
        row = df.loc[df[column].idxmax()]
        print(f"Maximum {column}: {row[column]:,.3f} m ({row['Province']})")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False, float_format="%.3f")
    print(f"Saved {len(df)} provinces to {args.output}")

    if args.update_toml:
        backup, notes = update_province_toml(args.toml, df)
        print(f"Backup created: {backup}")
        for note in notes:
            print(note)


if __name__ == "__main__":
    main()
