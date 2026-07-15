"""Migration execution — load validated CSVs into PostgreSQL staging tables.

Creates a staging table per CSV file (named staging_{run_id}_{safe_filename}),
uses bulk INSERT, and tracks per-file status.
"""
import csv
import hashlib
import io
import os
import re
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from database.models import MigrationRun, RunStatus, UploadedFile
from services.migration_service import UPLOAD_DIR
from services.schema_service import discover_schema

# Type map: inferred CSV types → PostgreSQL column types
_PG_TYPE_MAP = {
    "integer": "BIGINT",
    "decimal": "DOUBLE PRECISION",
    "boolean": "BOOLEAN",
    "date": "TIMESTAMP",
    "text": "TEXT",
}


def _safe_table_name(run_id: int, filename: str) -> str:
    """Generate a safe PostgreSQL table name from run ID and filename."""
    base = os.path.splitext(filename)[0]
    safe = re.sub(r"[^a-zA-Z0-9]", "_", base).lower().strip("_")[:40]
    return f"staging_{run_id}_{safe}"


def _safe_col_name(name: str) -> str:
    """Sanitize a column name for PostgreSQL."""
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", name).lower().strip("_")
    if not safe or safe[0].isdigit():
        safe = "col_" + safe
    return safe[:63]


def _create_staging_table(db: Session, table_name: str, schema: list[dict]) -> str:
    """Create a staging table with columns matching the CSV schema. Returns the DDL."""
    cols = []
    for col in schema:
        pg_type = _PG_TYPE_MAP.get(col["inferred_type"], "TEXT")
        col_name = _safe_col_name(col["name"])
        cols.append(f'"{col_name}" {pg_type}')

    cols_sql = ", ".join(cols)
    ddl = f'DROP TABLE IF EXISTS "{table_name}"; CREATE TABLE "{table_name}" ({cols_sql});'
    db.execute(text(ddl))
    db.commit()
    return ddl


def _load_csv_into_table(db: Session, table_name: str, file_path: str, schema: list[dict]) -> int:
    """Bulk-insert CSV rows into the staging table. Returns row count loaded."""
    col_names = [_safe_col_name(c["name"]) for c in schema]
    placeholders = ", ".join([f":{c}" for c in col_names])
    quoted_cols = ", ".join([f'"{c}"' for c in col_names])
    insert_sql = f'INSERT INTO "{table_name}" ({quoted_cols}) VALUES ({placeholders})'

    with open(file_path, "r", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        batch = []
        total = 0
        for row in reader:
            mapped = {}
            for orig_col, safe_col in zip([c["name"] for c in schema], col_names):
                val = row.get(orig_col, "").strip()
                mapped[safe_col] = val if val else None
            batch.append(mapped)
            if len(batch) >= 500:
                db.execute(text(insert_sql), batch)
                total += len(batch)
                batch = []
        if batch:
            db.execute(text(insert_sql), batch)
            total += len(batch)

    db.commit()
    return total


def execute_migration(db: Session, run_id: int) -> Optional[dict[str, Any]]:
    """Execute migration for all files in a run.

    1. Discovers schema per file
    2. Creates staging tables
    3. Bulk-loads data
    4. Updates run status

    Returns summary dict or None if run not found.
    """
    run = db.query(MigrationRun).filter(MigrationRun.id == run_id).first()
    if not run:
        return None

    run.status = RunStatus.MIGRATING
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
            "summary": {"total_files": 0, "total_rows_loaded": 0, "tables_created": 0, "success": False},
        }

    file_results = []
    total_rows = 0
    tables_created = 0
    has_error = False

    for f in files:
        file_path = os.path.join(UPLOAD_DIR, str(run_id), f.stored_filename)
        if not os.path.exists(file_path):
            file_results.append({
                "file_id": f.id,
                "filename": f.original_filename,
                "status": "error",
                "error": "File not found on disk",
                "table_name": None,
                "rows_loaded": 0,
            })
            has_error = True
            continue

        try:
            schema = discover_schema(file_path)
            if not schema:
                file_results.append({
                    "file_id": f.id,
                    "filename": f.original_filename,
                    "status": "error",
                    "error": "Empty schema — no columns found",
                    "table_name": None,
                    "rows_loaded": 0,
                })
                has_error = True
                continue

            table_name = _safe_table_name(run_id, f.original_filename)
            _create_staging_table(db, table_name, schema)
            tables_created += 1

            rows = _load_csv_into_table(db, table_name, file_path, schema)
            total_rows += rows

            file_results.append({
                "file_id": f.id,
                "filename": f.original_filename,
                "status": "loaded",
                "table_name": table_name,
                "rows_loaded": rows,
                "error": None,
            })
        except Exception as exc:
            has_error = True
            file_results.append({
                "file_id": f.id,
                "filename": f.original_filename,
                "status": "error",
                "error": str(exc),
                "table_name": None,
                "rows_loaded": 0,
            })

    run.status = RunStatus.COMPLETED if not has_error else RunStatus.FAILED
    db.commit()

    return {
        "run_id": run_id,
        "status": "completed" if not has_error else "failed",
        "files": file_results,
        "summary": {
            "total_files": len(files),
            "total_rows_loaded": total_rows,
            "tables_created": tables_created,
            "success": not has_error,
        },
    }
