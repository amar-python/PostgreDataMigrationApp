#!/usr/bin/env python3
# =============================================================================
# csv/validator.py — CSV Validator (Windows / Mac / Linux compatible)
# =============================================================================
# Called by csv_loader.sh via: python3 csv/validator.py
#
# Reads environment variables:
#   CSV_FILE   — path to the source CSV file
#   VALID_CSV  — path to write accepted rows
#   SKIP_FILE  — path to write rejected rows with reasons
#   TABLE_NAME — target table name (used for logging only)
#
# Exit codes:
#   0 — validation passed (at least one valid row found)
#   1 — validation failed (no valid rows or file error)
# =============================================================================

import csv
import os
import sys

# ── Colours (work on Windows 10+ terminal and Git Bash) ──────────────────────
GREEN  = '\033[0;32m'
YELLOW = '\033[1;33m'
RED    = '\033[0;31m'
NC     = '\033[0m'

def log(msg):  print(f"{GREEN}  [validator ✓]{NC} {msg}")
def warn(msg): print(f"{YELLOW}  [validator ⚠]{NC} {msg}")
def err(msg):  print(f"{RED}  [validator ✗]{NC} {msg}", file=sys.stderr)

# ── Read environment variables ────────────────────────────────────────────────
CSV_FILE   = os.environ.get('CSV_FILE',   '')
VALID_CSV  = os.environ.get('VALID_CSV',  '')
SKIP_FILE  = os.environ.get('SKIP_FILE',  '')
TABLE_NAME = os.environ.get('TABLE_NAME', 'unknown')

# Validate required vars
missing = [v for v in ('CSV_FILE','VALID_CSV','SKIP_FILE') if not os.environ.get(v)]
if missing:
    err(f"Missing required environment variables: {', '.join(missing)}")
    sys.exit(1)

# ── Check source file exists ──────────────────────────────────────────────────
if not os.path.isfile(CSV_FILE):
    err(f"CSV file not found: {CSV_FILE}")
    sys.exit(1)

# ── Ensure output directories exist ──────────────────────────────────────────
os.makedirs(os.path.dirname(VALID_CSV), exist_ok=True)
os.makedirs(os.path.dirname(SKIP_FILE), exist_ok=True)

# ── Open and validate CSV ─────────────────────────────────────────────────────
try:
    with open(CSV_FILE, 'r', encoding='utf-8-sig', newline='') as src, \
         open(VALID_CSV, 'w', encoding='utf-8',    newline='') as vf,  \
         open(SKIP_FILE, 'w', encoding='utf-8',    newline='') as sf:

        reader   = csv.reader(src)
        writer_v = csv.writer(vf)
        writer_s = csv.writer(sf)

        # ── Read and validate header ──────────────────────────────────────────
        try:
            headers = next(reader)
        except StopIteration:
            err("CSV file is empty — no header row found.")
            sys.exit(1)

        # Strip whitespace from header names
        headers = [h.strip() for h in headers]
        ncols   = len(headers)

        if ncols == 0:
            err("Header row is empty.")
            sys.exit(1)

        log(f"Header: {ncols} columns detected — {' | '.join(headers)}")

        # Check for duplicate column names
        dupes = [h for h in set(headers) if headers.count(h) > 1]
        if dupes:
            warn(f"Duplicate column names: {', '.join(dupes)}")

        # Write headers to both output files
        writer_v.writerow(headers)
        writer_s.writerow(headers + ['_skip_reason'])

        # ── Process each data row ─────────────────────────────────────────────
        valid_count = 0
        skip_count  = 0

        for line_num, row in enumerate(reader, start=2):

            # Rule 1: skip completely empty rows
            if not any(cell.strip() for cell in row):
                writer_s.writerow(row + ['empty row — all values blank'])
                skip_count += 1
                continue

            # Rule 2: column count must match header
            if len(row) != ncols:
                reason = f'column mismatch — expected {ncols}, got {len(row)}'
                writer_s.writerow(row + [reason])
                skip_count += 1
                continue

            # Valid row
            writer_v.writerow(row)
            valid_count += 1

        # ── Summary ───────────────────────────────────────────────────────────
        total = valid_count + skip_count
        log(f"Validation complete — {total} rows processed.")
        log(f"  Valid rows   : {valid_count}")

        if skip_count > 0:
            warn(f"  Skipped rows : {skip_count} — written to: {SKIP_FILE}")

        if valid_count == 0:
            err("No valid rows found. Nothing to load.")
            sys.exit(1)

        sys.exit(0)

except PermissionError as e:
    err(f"Permission denied: {e}")
    sys.exit(1)
except Exception as e:
    err(f"Unexpected error: {e}")
    sys.exit(1)
