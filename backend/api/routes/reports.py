"""API routes for report generation and download.

POST /api/reports/{id}/generate?format=json|html  — generate report
GET  /api/reports/{id}/download/{format}           — download generated report
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database.connection import get_db
from services import report_service, schema_service, execution_service, evaluation_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/{run_id}/generate")
def generate_report(
    run_id: int,
    format: str = Query("json", pattern="^(json|html)$"),
    db: Session = Depends(get_db),
):
    """Generate a report for a migration run.

    Automatically gathers validation, migration, and evaluation data.
    """
    # Gather available data
    validation_data = schema_service.validate_run(db, run_id)
    if validation_data is None:
        raise HTTPException(status_code=404, detail=f"Migration run {run_id} not found")

    # Try evaluation (may fail if migration hasn't been run)
    evaluation_data = None
    try:
        evaluation_data = evaluation_service.evaluate_run(db, run_id)
    except Exception:
        pass

    result = report_service.generate_report(
        db, run_id, format,
        validation_data=validation_data,
        evaluation_data=evaluation_data,
    )
    if result is None:
        raise HTTPException(status_code=400, detail="Invalid format")
    return result


@router.get("/{run_id}/download/{format}")
def download_report(run_id: int, format: str):
    """Download a previously generated report."""
    path = report_service.get_report_path(run_id, format)
    if not path:
        raise HTTPException(status_code=404, detail="Report not found. Generate it first.")

    media_type = "application/json" if format == "json" else "text/html"
    filename = f"mep_report_{run_id}.{format}"
    return FileResponse(path, media_type=media_type, filename=filename)
