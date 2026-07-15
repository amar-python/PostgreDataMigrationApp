"""Dashboard statistics service.

Provides aggregate stats across all migration runs for the dashboard view.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import MigrationRun, RunStatus, UploadedFile


def get_dashboard_stats(db: Session) -> dict:
    """Return aggregate statistics for the dashboard."""
    # Total runs
    total_runs = db.query(func.count(MigrationRun.id)).scalar() or 0

    # Runs by status
    status_counts = (
        db.query(MigrationRun.status, func.count(MigrationRun.id))
        .group_by(MigrationRun.status)
        .all()
    )
    runs_by_status = {
        (s.value if hasattr(s, "value") else str(s)): c
        for s, c in status_counts
    }

    # File stats
    total_files = db.query(func.count(UploadedFile.id)).scalar() or 0
    total_rows = db.query(func.coalesce(func.sum(UploadedFile.row_count), 0)).scalar() or 0
    total_size = db.query(func.coalesce(func.sum(UploadedFile.file_size), 0)).scalar() or 0

    # Recent runs (last 10)
    recent = (
        db.query(MigrationRun)
        .order_by(MigrationRun.created_at.desc())
        .limit(10)
        .all()
    )

    recent_runs = []
    for run in recent:
        files = run.files or []
        recent_runs.append({
            "id": run.id,
            "name": run.name,
            "environment": run.environment,
            "description": run.description,
            "status": run.status.value if hasattr(run.status, "value") else str(run.status),
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "updated_at": run.updated_at.isoformat() if run.updated_at else None,
            "file_count": len(files),
            "total_size": sum(f.file_size for f in files),
        })

    return {
        "total_runs": total_runs,
        "runs_by_status": runs_by_status,
        "total_files": total_files,
        "total_rows": int(total_rows),
        "total_size": int(total_size),
        "recent_runs": recent_runs,
    }
