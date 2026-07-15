"""Schema discovery and validation for uploaded CSV files.

Analyses CSV content to infer column data types, detect nullability,
uniqueness, and sample values. Then runs validation checks to surface
data-quality issues before migration.
"""
import csv
import io
import json
import os
import re
from collections import Counter
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from database.models import MigrationRun, RunStatus, UploadedFile
from services.migration_service import UPLOAD_DIR

# ---------------------------------------------------------------------------
# Type-inference helpers
# ---------------------------------------------------------------------------

_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+\.\d+$")
_DATE_PATTERNS = [
    "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d",
    "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S",
    "%d-%b-%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
]
_BOOL_VALUES = {"true", "false", "yes", "no", "1", "0", "t", "f", "y", "n"}


def _infer_type(values: list[str]) -> str:
    """Infer the most likely data type from a sample of non-empty string values."""
    if not values:
        return "text"

    # Check boolean
    if all(v.lower() in _BOOL_VALUES for v in values):
        return "boolean"

    # Check integer
    if all(_INT_RE.match(v) for v in values):
        return "integer"

    # Check decimal/float
    if all(_FLOAT_RE.match(v) or _INT_RE.match(v) for v in values):
        return "decimal"

    # Check date
    for fmt in _DATE_PATTERNS:
        try:
            for v in values:
                datetime.strptime(v.strip(), fmt)
            return "date"
        except (ValueError, TypeError):
            continue

    return "text"


# ---------------------------------------------------------------------------
# Schema discovery
# ---------------------------------------------------------------------------

def discover_schema(file_path: str) -> list[dict[str, Any]]:
    """Read a CSV file and return a list of column descriptors.

    Each descriptor:
        {
            "name": "column_name",
            "inferred_type": "integer" | "decimal" | "date" | "boolean" | "text",
            "nullable": true/false,
            "unique": true/false,
            "sample_values": ["v1", "v2", "v3"],
            "null_count": 5,
            "total_count": 100,
        }
    """
    with open(file_path, "r", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        headers = next(reader, None)
        if not headers:
            return []

        # Collect all values per column
        col_values: list[list[str]] = [[] for _ in headers]
        row_count = 0
        for row in reader:
            row_count += 1
            for i, val in enumerate(row):
                if i < len(headers):
                    col_values[i].append(val)

    columns = []
    for i, name in enumerate(headers):
        raw_vals = col_values[i] if i < len(col_values) else []
        non_empty = [v.strip() for v in raw_vals if v.strip()]
        null_count = len(raw_vals) - len(non_empty)

        # Uniqueness
        unique = len(set(non_empty)) == len(non_empty) and len(non_empty) > 0

        # Infer type from a sample (first 200 non-empty values)
        sample = non_empty[:200]
        inferred = _infer_type(sample)

        # Pick up to 5 distinct sample values
        sample_vals = list(dict.fromkeys(non_empty[:50]))[:5]

        columns.append({
            "name": name.strip(),
            "inferred_type": inferred,
            "nullable": null_count > 0,
            "unique": unique,
            "sample_values": sample_vals,
            "null_count": null_count,
            "total_count": row_count,
        })

    return columns


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_file(file_path: str, schema: list[dict]) -> list[dict[str, Any]]:
    """Run validation checks against a CSV file given its discovered schema.

    Returns a list of issue dicts:
        {
            "severity": "error" | "warning" | "info",
            "check": "check_name",
            "column": "col_name" or null,
            "message": "description",
        }
    """
    issues: list[dict] = []

    if not schema:
        issues.append({
            "severity": "error",
            "check": "empty_schema",
            "column": None,
            "message": "CSV file has no headers or is empty.",
        })
        return issues

    # Check 1: duplicate column names
    col_names = [c["name"] for c in schema]
    dupes = [name for name, cnt in Counter(col_names).items() if cnt > 1]
    for d in dupes:
        issues.append({
            "severity": "error",
            "check": "duplicate_column",
            "column": d,
            "message": f"Column '{d}' appears multiple times in the header.",
        })

    # Check 2: empty column names
    for i, name in enumerate(col_names):
        if not name or not name.strip():
            issues.append({
                "severity": "error",
                "check": "empty_column_name",
                "column": f"Column {i + 1}",
                "message": f"Column at position {i + 1} has an empty or blank name.",
            })

    # Check 3: null violations per column
    for col in schema:
        if col["null_count"] > 0:
            pct = round(col["null_count"] / max(col["total_count"], 1) * 100, 1)
            severity = "error" if pct > 50 else "warning" if pct > 10 else "info"
            issues.append({
                "severity": severity,
                "check": "null_values",
                "column": col["name"],
                "message": f"{col['null_count']} null/empty values ({pct}% of {col['total_count']} rows).",
            })

    # Check 4: duplicate rows  — read the file again for full-row dupe check
    try:
        with open(file_path, "r", encoding="utf-8-sig") as fh:
            reader = csv.reader(fh)
            next(reader, None)  # skip header
            row_hashes: list[str] = []
            for row in reader:
                row_hashes.append("|".join(row))
        total_rows = len(row_hashes)
        unique_rows = len(set(row_hashes))
        dupe_rows = total_rows - unique_rows
        if dupe_rows > 0:
            issues.append({
                "severity": "warning",
                "check": "duplicate_rows",
                "column": None,
                "message": f"{dupe_rows} duplicate row(s) detected out of {total_rows} total rows.",
            })
    except Exception:
        pass

    # Check 5: type consistency  — look for mixed-type columns
    for col in schema:
        if col["inferred_type"] == "text" and col["total_count"] > 0 and col["null_count"] < col["total_count"]:
            # See if a sizable portion look numeric
            sample = col["sample_values"]
            numeric_count = sum(1 for v in sample if _INT_RE.match(v) or _FLOAT_RE.match(v))
            if 0 < numeric_count < len(sample) and len(sample) >= 3:
                issues.append({
                    "severity": "warning",
                    "check": "mixed_types",
                    "column": col["name"],
                    "message": f"Column appears to contain mixed data types (some numeric, some text).",
                })

    # If no issues, add a success info
    if not issues:
        issues.append({
            "severity": "info",
            "check": "all_passed",
            "column": None,
            "message": "All validation checks passed.",
        })

    return issues


# ---------------------------------------------------------------------------
# Orchestration — run schema + validation for a migration run
# ---------------------------------------------------------------------------

def validate_run(db: Session, run_id: int) -> Optional[dict]:
    """Discover schema and validate all files in a migration run.

    Updates the run status to VALIDATING then back to CREATED (or FAILED).

    Returns a summary dict or None if run not found.
    """
    run = db.query(MigrationRun).filter(MigrationRun.id == run_id).first()
    if not run:
        return None

    run.status = RunStatus.VALIDATING
    db.commit()

    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.migration_run_id == run_id)
        .all()
    )

    if not files:
        run.status = RunStatus.CREATED
        db.commit()
        return {
            "run_id": run_id,
            "status": "no_files",
            "files": [],
            "summary": {"total_files": 0, "errors": 0, "warnings": 0, "passed": True},
        }

    file_results = []
    total_errors = 0
    total_warnings = 0

    for f in files:
        file_path = os.path.join(UPLOAD_DIR, str(run_id), f.stored_filename)
        if not os.path.exists(file_path):
            file_results.append({
                "file_id": f.id,
                "filename": f.original_filename,
                "schema": [],
                "issues": [{
                    "severity": "error",
                    "check": "file_missing",
                    "column": None,
                    "message": "Uploaded file not found on disk.",
                }],
            })
            total_errors += 1
            continue

        schema = discover_schema(file_path)
        issues = validate_file(file_path, schema)

        errors = sum(1 for i in issues if i["severity"] == "error")
        warnings = sum(1 for i in issues if i["severity"] == "warning")
        total_errors += errors
        total_warnings += warnings

        file_results.append({
            "file_id": f.id,
            "filename": f.original_filename,
            "schema": schema,
            "issues": issues,
        })

    passed = total_errors == 0
    # Revert to CREATED status (validation is a pre-check, not a final state)
    run.status = RunStatus.CREATED if passed else RunStatus.CREATED
    db.commit()

    return {
        "run_id": run_id,
        "status": "passed" if passed else "failed",
        "files": file_results,
        "summary": {
            "total_files": len(files),
            "errors": total_errors,
            "warnings": total_warnings,
            "passed": passed,
        },
    }
