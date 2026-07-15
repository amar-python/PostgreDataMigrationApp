"""API routes for schema discovery and validation.

POST /api/migrations/{id}/validate  — run validation on all files
GET  /api/migrations/{id}/schema    — get schema for all files (without re-validating)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas import ValidationResponse
from database.connection import get_db
from services import schema_service

router = APIRouter(prefix="/migrations", tags=["validation"])


@router.post("/{run_id}/validate", response_model=ValidationResponse)
def validate_migration_run(run_id: int, db: Session = Depends(get_db)):
    """Discover schema and run validation checks on all files in a run."""
    result = schema_service.validate_run(db, run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Migration run {run_id} not found")
    return result
