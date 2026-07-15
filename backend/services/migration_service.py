"""Business logic for migration runs and file uploads.

Keeps route handlers thin: they delegate to functions here, which interact
with the ORM models and the filesystem.
"""
import csv
import io
import json
import os
import uuid
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from database.models import MigrationRun, RunStatus, UploadedFile

# Upload directory — relative to the backend working dir, mounted via Docker
UPLOAD_DIR = os.environ.get("MEP_UPLOAD_DIR", os.path.join(os.getcwd(), "uploads"))


def _ensure_upload_dir(run_id: int) -> str:
    """Create and return the upload directory for a specific run."""
    run_dir = os.path.join(UPLOAD_DIR, str(run_id))
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


# ---------------------------------------------------------------------------
# Migration Run CRUD
# ---------------------------------------------------------------------------

def create_run(db: Session, name: str, environment: str, description: Optional[str] = None) -> MigrationRun:
    """Create a new migration run and persist it."""
    run = MigrationRun(
        name=name,
        environment=environment,
        description=description,
        status=RunStatus.CREATED,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_run(db: Session, run_id: int) -> Optional[MigrationRun]:
    """Return a migration run by ID, or None."""
    return db.query(MigrationRun).filter(MigrationRun.id == run_id).first()


def list_runs(db: Session, skip: int = 0, limit: int = 50) -> tuple[list[MigrationRun], int]:
    """Return a paginated list of runs (newest first) and the total count."""
    total = db.query(MigrationRun).count()
    runs = (
        db.query(MigrationRun)
        .order_by(MigrationRun.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return runs, total


def delete_run(db: Session, run_id: int) -> bool:
    """Delete a run and its associated files from DB and disk. Returns True if found."""
    run = get_run(db, run_id)
    if not run:
        return False
    # Remove uploaded files from disk
    run_dir = os.path.join(UPLOAD_DIR, str(run_id))
    if os.path.isdir(run_dir):
        import shutil
        shutil.rmtree(run_dir, ignore_errors=True)
    db.delete(run)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# File Upload
# ---------------------------------------------------------------------------

def _parse_csv_metadata(content: bytes, filename: str) -> dict:
    """Quickly parse CSV content to extract row count, column count, and column names."""
    result = {"row_count": None, "column_count": None, "columns": None}
    try:
        text = content.decode("utf-8-sig")  # handles BOM
        reader = csv.reader(io.StringIO(text))
        headers = next(reader, None)
        if headers:
            result["columns"] = json.dumps([h.strip() for h in headers])
            result["column_count"] = len(headers)
            # Count data rows (excluding header)
            row_count = sum(1 for _ in reader)
            result["row_count"] = row_count
    except Exception:
        pass  # non-fatal — metadata is optional
    return result


async def upload_file(db: Session, run_id: int, file: UploadFile) -> Optional[UploadedFile]:
    """Save an uploaded file to disk and create a DB record.

    Returns the UploadedFile object, or None if the run doesn't exist.
    """
    run = get_run(db, run_id)
    if not run:
        return None

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Generate a unique stored filename to avoid collisions
    ext = os.path.splitext(file.filename or "file.csv")[1]
    stored_name = f"{uuid.uuid4().hex}{ext}"

    # Save to disk
    run_dir = _ensure_upload_dir(run_id)
    file_path = os.path.join(run_dir, stored_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse CSV metadata
    meta = _parse_csv_metadata(content, file.filename or "unknown.csv")

    # Persist to DB
    uploaded = UploadedFile(
        migration_run_id=run_id,
        original_filename=file.filename or "unknown.csv",
        stored_filename=stored_name,
        file_size=file_size,
        content_type=file.content_type or "text/csv",
        row_count=meta["row_count"],
        column_count=meta["column_count"],
        columns=meta["columns"],
    )
    db.add(uploaded)

    # Update run status to UPLOADING if still CREATED
    if run.status == RunStatus.CREATED:
        run.status = RunStatus.UPLOADING

    db.commit()
    db.refresh(uploaded)
    return uploaded


def list_files(db: Session, run_id: int) -> list[UploadedFile]:
    """Return all files for a given run."""
    return (
        db.query(UploadedFile)
        .filter(UploadedFile.migration_run_id == run_id)
        .order_by(UploadedFile.uploaded_at)
        .all()
    )


def delete_file(db: Session, file_id: int) -> bool:
    """Delete a single uploaded file from DB and disk. Returns True if found."""
    uploaded = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not uploaded:
        return False
    # Remove from disk
    run_dir = os.path.join(UPLOAD_DIR, str(uploaded.migration_run_id))
    file_path = os.path.join(run_dir, uploaded.stored_filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.delete(uploaded)
    db.commit()
    return True
