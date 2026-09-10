#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
9_Package_LDP.py

Package EIT Thailand LDP CRS definition files into one ZIP archive.

Workflow
--------
1) Recursively find all *.PJ4 files under OUTPUT_LDP/ and add unchanged.
2) Recursively find all *.WKT files under OUTPUT_LDP/.
3) For each WKT, use its parent-directory name as the LDP code and edit
   the WKT IN MEMORY before adding it to the ZIP:

       PROJCRS["unknown",
           BASEGEOGCRS["unknown",

   becomes, for parent directory TH_GBKK:

       PROJCRS["EIT_TH_GBKK",
           BASEGEOGCRS["WGS 84",

The original WKT files on disk are NOT changed.
"""

from __future__ import annotations

import glob
import re
import sys
import zipfile
from pathlib import Path
from typing import Iterable


# ======================================================================
# USER CONFIGURATION -- CHANGE VALUES HERE
# ======================================================================

# Root folder containing TH_SN/, TH_BK/, TH_KP/, TH_GBKK/, ...
INPUT_ROOT = Path("OUTPUT_LDP")

# Recursive glob patterns
PJ4_GLOB = "**/*.PJ4"
WKT_GLOB = "**/*.WKT"

# Output ZIP
OUTPUT_ZIP = Path("EIT_LDP_SEP2569.zip")

# WKT naming rules
PROJCRS_PREFIX = "EIT_"        # TH_GBKK -> EIT_TH_GBKK
BASEGEOGCRS_NAME = "WGS 84"

# ZIP layout
# True  -> TH_GBKK/TH_GBKK_LDP_CRS.WKT
# False -> TH_GBKK_LDP_CRS.WKT
KEEP_RELATIVE_DIRECTORIES = True

# ZIP settings
ZIP_COMPRESSION = zipfile.ZIP_DEFLATED
ZIP_COMPRESSLEVEL = 9
OVERWRITE_ZIP = True

# WKT text settings
WKT_ENCODING = "utf-8"
STRICT_WKT_CHECK = True

# Console output
VERBOSE = True


# ======================================================================
# WKT SEARCH PATTERNS
# ======================================================================

# Only the first matching PROJCRS and BASEGEOGCRS names are replaced.
PROJCRS_UNKNOWN_RE = re.compile(
    r'(\bPROJCRS\s*\[\s*)["\']unknown["\']',
    flags=re.IGNORECASE,
)

BASEGEOGCRS_UNKNOWN_RE = re.compile(
    r'(\bBASEGEOGCRS\s*\[\s*)["\']unknown["\']',
    flags=re.IGNORECASE,
)


# ======================================================================
# FILE DISCOVERY
# ======================================================================

def find_files(root: Path, pattern: str) -> list[Path]:
    """Recursively find files using glob()."""
    search_pattern = str(root / pattern)
    files = [
        Path(name)
        for name in glob.glob(search_pattern, recursive=True)
        if Path(name).is_file()
    ]
    return sorted(files, key=lambda p: str(p).lower())


def make_archive_name(file_path: Path, root: Path) -> str:
    """Return the path stored inside the ZIP."""
    if KEEP_RELATIVE_DIRECTORIES:
        return file_path.relative_to(root).as_posix()
    return file_path.name


def ldp_code_from_parent(file_path: Path) -> str:
    """Example: OUTPUT_LDP/TH_KP/file.WKT -> TH_KP."""
    return file_path.parent.name


# ======================================================================
# WKT EDITING
# ======================================================================

def edit_wkt_text(text: str, ldp_code: str) -> tuple[str, int, int]:
    """
    Replace:
        PROJCRS["unknown"   -> PROJCRS["EIT_<parent>"
        BASEGEOGCRS["unknown" -> BASEGEOGCRS["WGS 84"

    Returns:
        edited_text, n_projcrs_replacements, n_basegeogcrs_replacements
    """
    projcrs_name = f"{PROJCRS_PREFIX}{ldp_code}"

    edited, n_proj = PROJCRS_UNKNOWN_RE.subn(
        rf'\1"{projcrs_name}"',
        text,
        count=1,
    )

    edited, n_base = BASEGEOGCRS_UNKNOWN_RE.subn(
        rf'\1"{BASEGEOGCRS_NAME}"',
        edited,
        count=1,
    )

    return edited, n_proj, n_base


# ======================================================================
# ZIP WRITERS
# ======================================================================

def add_pj4_files(
    zf: zipfile.ZipFile,
    files: Iterable[Path],
    root: Path,
) -> int:
    """Add PJ4 files unchanged."""
    count = 0

    for path in files:
        arcname = make_archive_name(path, root)
        zf.write(path, arcname=arcname)
        count += 1

        if VERBOSE:
            print(f"[PJ4] {path} -> {arcname}")

    return count


def add_wkt_files(
    zf: zipfile.ZipFile,
    files: Iterable[Path],
    root: Path,
) -> int:
    """Edit WKT in memory and add edited text to the ZIP."""
    count = 0

    for path in files:
        ldp_code = ldp_code_from_parent(path)
        projcrs_name = f"{PROJCRS_PREFIX}{ldp_code}"
        arcname = make_archive_name(path, root)

        source_text = path.read_text(
            encoding=WKT_ENCODING,
            errors="strict",
        )

        edited_text, n_proj, n_base = edit_wkt_text(
            source_text,
            ldp_code,
        )

        if STRICT_WKT_CHECK and (n_proj != 1 or n_base != 1):
            raise ValueError(
                "Unexpected WKT structure:\n"
                f"  File: {path}\n"
                f"  PROJCRS replacements: {n_proj}\n"
                f"  BASEGEOGCRS replacements: {n_base}\n"
                "Expected exactly one replacement of each 'unknown'."
            )

        # Write edited text directly to the ZIP.
        # Original WKT source file remains unchanged.
        zf.writestr(arcname, edited_text)
        count += 1

        if VERBOSE:
            print(f"[WKT] {path} -> {arcname}")
            print(f'      PROJCRS     = "{projcrs_name}"')
            print(f'      BASEGEOGCRS = "{BASEGEOGCRS_NAME}"')

    return count


# ======================================================================
# REPORTING
# ======================================================================

def print_discovery_summary(
    pj4_files: list[Path],
    wkt_files: list[Path],
) -> None:
    print("=" * 72)
    print("EIT LDP PACKAGE")
    print("=" * 72)
    print(f"Input root : {INPUT_ROOT.resolve()}")
    print(f"Output ZIP : {OUTPUT_ZIP.resolve()}")
    print(f"PJ4 files  : {len(pj4_files)}")
    print(f"WKT files  : {len(wkt_files)}")
    print()

    if VERBOSE:
        if pj4_files:
            print("PJ4 files found:")
            for path in pj4_files:
                print(f"  {path}")
            print()

        if wkt_files:
            print("WKT files found:")
            for path in wkt_files:
                print(f"  {path}")
            print()


# ======================================================================
# MAIN WORKFLOW
# ======================================================================

def create_package() -> Path:
    if not INPUT_ROOT.is_dir():
        raise FileNotFoundError(
            f"Input directory does not exist: {INPUT_ROOT}"
        )

    # Equivalent idea to:
    #   find OUTPUT_LDP/ | grep PJ4
    #   find OUTPUT_LDP/ | grep WKT
    pj4_files = find_files(INPUT_ROOT, PJ4_GLOB)
    wkt_files = find_files(INPUT_ROOT, WKT_GLOB)

    print_discovery_summary(pj4_files, wkt_files)

    if not pj4_files and not wkt_files:
        raise FileNotFoundError(
            f"No PJ4 or WKT files found under {INPUT_ROOT}"
        )

    if OUTPUT_ZIP.exists():
        if not OVERWRITE_ZIP:
            raise FileExistsError(f"ZIP already exists: {OUTPUT_ZIP}")
        OUTPUT_ZIP.unlink()

    OUTPUT_ZIP.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(
        OUTPUT_ZIP,
        mode="w",
        compression=ZIP_COMPRESSION,
        compresslevel=ZIP_COMPRESSLEVEL,
    ) as zf:

        print("=" * 72)
        print("ADD PJ4")
        print("=" * 72)
        n_pj4 = add_pj4_files(zf, pj4_files, INPUT_ROOT)

        print()
        print("=" * 72)
        print("EDIT + ADD WKT")
        print("=" * 72)
        n_wkt = add_wkt_files(zf, wkt_files, INPUT_ROOT)

    print()
    print("=" * 72)
    print("DONE")
    print("=" * 72)
    print(f"ZIP       : {OUTPUT_ZIP.resolve()}")
    print(f"PJ4 added : {n_pj4}")
    print(f"WKT added : {n_wkt}")
    print(f"Total     : {n_pj4 + n_wkt}")

    return OUTPUT_ZIP


def main() -> int:
    try:
        create_package()
        return 0
    except Exception as exc:
        print()
        print("=" * 72)
        print("ERROR")
        print("=" * 72)
        print(exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
