"""Evaluation engine — compare source CSVs against loaded staging tables.

Checks: row counts, null percentages, duplicate detection, and computes
an overall quality score with PASS/FAIL verdict.
"""
import csv
import hashlib
import os
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from database.models import MigrationRun, UploadedFile
from services.migration_service import UPLOAD_DIR
from services.execution_service import _safe_table_name, _safe_col_name
from services.schema_service import discover_schema


def _source_row_count(file_path: str) -> int:
    """Count data rows in CSV (excluding header)."""
    with open(file_path, "r", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        next(reader, None)  # skip header
        return sum(1 for _ in reader)


def _source_row_hashes(file_path: str) -> list[str]:
    """Return a hash per row for duplicate detection."""
    hashes = []
    with open(file_path, "r", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        next(reader, None)
        for row in reader:
            h = hashlib.md5("|".join(row).encode()).hexdigest()
            hashes.append(h)
    return hashes


def evaluate_run(db: Session, run_id: int) -> Optional[dict[str, Any]]:
    """Evaluate data quality for a completed migration run.

    For each file, compares:
      - Source vs target row count
      - Null percentage per column in target
      - Duplicate rows in target
      - Overall quality score (0-100)

    Returns evaluation dict or None if run not found.
    """
    run = db.query(MigrationRun).filter(MigrationRun.id == run_id).first()
    if not run:
        return None

    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.migration_run_id == run_id)
        .all()
    )

    if not files:
        return {
            "run_id": run_id,
            "status": "no_files",
            "files": [],
            "summary": {
                "total_files": 0,
                "overall_score": 0,
                "verdict": "FAIL",
                "total_source_rows": 0,
                "total_target_rows": 0,
            },
        }

    file_results = []
    total_source = 0
    total_target = 0
    scores = []

    for f in files:
        file_path = os.path.join(UPLOAD_DIR, str(run_id), f.stored_filename)
        table_name = _safe_table_name(run_id, f.original_filename)

        # Check if staging table exists
        try:
            result = db.execute(
                text(f"SELECT COUNT(*) FROM \"{table_name}\"")
            )
            target_count = result.scalar()
        except Exception:
            file_results.append({
                "file_id": f.id,
                "filename": f.original_filename,
                "status": "error",
                "error": f"Staging table '{table_name}' not found. Run migration first.",
                "score": 0,
            })
            scores.append(0)
            continue

        # Source row count
        if os.path.exists(file_path):
            source_count = _source_row_count(file_path)
        else:
            source_count = f.row_count or 0

        total_source += source_count
        total_target += target_count

        # --- Quality checks ---
        checks = []
        file_score = 100.0

        # 1. Row count match
        if source_count == target_count:
            checks.append({
                "check": "row_count_match",
                "status": "pass",
                "detail": f"Source: {source_count}, Target: {target_count}",
            })
        else:
            diff = abs(source_count - target_count)
            pct_diff = round(diff / max(source_count, 1) * 100, 1)
            checks.append({
                "check": "row_count_match",
                "status": "fail",
                "detail": f"Source: {source_count}, Target: {target_count} (diff: {diff}, {pct_diff}%)",
            })
            file_score -= min(30, pct_diff)

        # 2. Null percentage in target
        try:
            schema = discover_schema(file_path) if os.path.exists(file_path) else []
            col_names = [_safe_col_name(c["name"]) for c in schema]
            null_pcts = []
            for col in col_names:
                r = db.execute(
                    text(f'SELECT COUNT(*) FILTER (WHERE "{col}" IS NULL) FROM "{table_name}"')
                )
                null_count = r.scalar()
                pct = round(null_count / max(target_count, 1) * 100, 1)
                null_pcts.append({"column": col, "null_pct": pct})

            avg_null = sum(n["null_pct"] for n in null_pcts) / max(len(null_pcts), 1)
            checks.append({
                "check": "null_percentage",
                "status": "pass" if avg_null < 20 else "warning",
                "detail": f"Average null%: {round(avg_null, 1)}%",
                "columns": null_pcts,
            })
            if avg_null >= 20:
                file_score -= min(20, avg_null - 20)
        except Exception:
            checks.append({
                "check": "null_percentage",
                "status": "skipped",
                "detail": "Could not analyze null percentages",
            })

        # 3. Duplicate rows in target
        try:
            if col_names:
                cols_joined = ", ".join(f'"{c}"' for c in col_names)
                dup_query = f"""
                    SELECT COUNT(*) FROM (
                        SELECT {cols_joined}, COUNT(*) as cnt
                        FROM "{table_name}"
                        GROUP BY {cols_joined}
                        HAVING COUNT(*) > 1
                    ) dupes
                """
                r = db.execute(text(dup_query))
                dup_groups = r.scalar()
                if dup_groups == 0:
                    checks.append({
                        "check": "duplicate_rows",
                        "status": "pass",
                        "detail": "No duplicate rows found in target.",
                    })
                else:
                    checks.append({
                        "check": "duplicate_rows",
                        "status": "warning",
                        "detail": f"{dup_groups} groups of duplicate rows found in target.",
                    })
                    file_score -= min(10, dup_groups)
        except Exception:
            checks.append({
                "check": "duplicate_rows",
                "status": "skipped",
                "detail": "Could not check for duplicates",
            })

        file_score = max(0, min(100, round(file_score)))
        scores.append(file_score)

        file_results.append({
            "file_id": f.id,
            "filename": f.original_filename,
            "table_name": table_name,
            "source_rows": source_count,
            "target_rows": target_count,
            "score": file_score,
            "checks": checks,
            "status": "pass" if file_score >= 70 else "fail",
        })

    overall_score = round(sum(scores) / max(len(scores), 1))
    verdict = "PASS" if overall_score >= 70 else "FAIL"

    return {
        "run_id": run_id,
        "status": "evaluated",
        "files": file_results,
        "summary": {
            "total_files": len(files),
            "overall_score": overall_score,
            "verdict": verdict,
            "total_source_rows": total_source,
            "total_target_rows": total_target,
        },
    }
