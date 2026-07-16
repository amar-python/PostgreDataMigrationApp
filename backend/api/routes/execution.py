"""API routes for migration execution and evaluation.

POST /api/migrations/{id}/execute   — load CSVs into PostgreSQL staging tables
POST /api/migrations/{id}/evaluate  — run quality checks against loaded data
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas import EvaluationResponse, MigrationExecuteResponse
from database.connection import get_db
from services import execution_service, evaluation_service

router = APIRouter(prefix="/migrations", tags=["execution"])


@router.post("/{run_id}/execute", response_model=MigrationExecuteResponse)
def execute_migration(run_id: int, db: Session = Depends(get_db)):
    """Execute migration — create staging tables and load CSV data."""
    result = execution_service.execute_migration(db, run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Migration run {run_id} not found")
    return result


@router.post("/{run_id}/evaluate", response_model=EvaluationResponse)
def evaluate_migration(run_id: int, db: Session = Depends(get_db)):
    """Evaluate data quality of migrated data vs source CSVs."""
    result = evaluation_service.evaluate_run(db, run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Migration run {run_id} not found")
    return result
