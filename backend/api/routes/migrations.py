"""API routes for migration runs and CSV file uploads.

Phase 1 endpoints:
  POST   /api/migrations             – create a new run
  GET    /api/migrations             – list all runs
  GET    /api/migrations/{id}        – get run detail
  DELETE /api/migrations/{id}        – delete a run and its files
  POST   /api/migrations/{id}/files  – upload one or more CSV files
  GET    /api/migrations/{id}/files  – list files for a run
  DELETE /api/migrations/files/{id}  – delete a single file
"""
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.schemas import (
    DeleteResponse,
    MigrationRunCreate,
    MigrationRunListResponse,
    MigrationRunResponse,
    UploadedFileListResponse,
    UploadedFileResponse,
)
from database.connection import get_db
from services import migration_service

router = APIRouter(prefix="/migrations", tags=["migrations"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_to_response(run) -> MigrationRunResponse:
    """Convert an ORM MigrationRun to a response schema."""
    files = run.files or []
    return MigrationRunResponse(
        id=run.id,
        name=run.name,
        environment=run.environment,
        description=run.description,
        status=run.status.value if hasattr(run.status, "value") else run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        file_count=len(files),
        total_size=sum(f.file_size for f in files),
    )


# ---------------------------------------------------------------------------
# Migration Run endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=MigrationRunResponse, status_code=201)
def create_migration_run(body: MigrationRunCreate, db: Session = Depends(get_db)):
    """Create a new migration run."""
    run = migration_service.create_run(
        db, name=body.name, environment=body.environment, description=body.description
    )
    return _run_to_response(run)


@router.get("", response_model=MigrationRunListResponse)
def list_migration_runs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List migration runs, newest first."""
    runs, total = migration_service.list_runs(db, skip=skip, limit=limit)
    return MigrationRunListResponse(
        runs=[_run_to_response(r) for r in runs],
        total=total,
    )


@router.get("/{run_id}", response_model=MigrationRunResponse)
def get_migration_run(run_id: int, db: Session = Depends(get_db)):
    """Get a single migration run by ID."""
    run = migration_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Migration run {run_id} not found")
    return _run_to_response(run)


@router.delete("/{run_id}", response_model=DeleteResponse)
def delete_migration_run(run_id: int, db: Session = Depends(get_db)):
    """Delete a migration run and all its files."""
    deleted = migration_service.delete_run(db, run_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Migration run {run_id} not found")
    return DeleteResponse(detail="Migration run deleted", id=run_id)


# ---------------------------------------------------------------------------
# File Upload endpoints
# ---------------------------------------------------------------------------

@router.post("/{run_id}/files", response_model=List[UploadedFileResponse], status_code=201)
async def upload_files(
    run_id: int,
    files: List[UploadFile] = File(..., description="One or more CSV files"),
    db: Session = Depends(get_db),
):
    """Upload one or more CSV files to a migration run."""
    # Validate the run exists
    run = migration_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Migration run {run_id} not found")

    results = []
    for file in files:
        uploaded = await migration_service.upload_file(db, run_id, file)
        if uploaded:
            results.append(UploadedFileResponse.model_validate(uploaded))

    return results


@router.get("/{run_id}/files", response_model=UploadedFileListResponse)
def list_uploaded_files(run_id: int, db: Session = Depends(get_db)):
    """List all files uploaded for a migration run."""
    run = migration_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Migration run {run_id} not found")
    files = migration_service.list_files(db, run_id)
    return UploadedFileListResponse(
        files=[UploadedFileResponse.model_validate(f) for f in files],
        total=len(files),
    )


@router.delete("/files/{file_id}", response_model=DeleteResponse)
def delete_uploaded_file(file_id: int, db: Session = Depends(get_db)):
    """Delete a single uploaded file."""
    deleted = migration_service.delete_file(db, file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    return DeleteResponse(detail="File deleted", id=file_id)
