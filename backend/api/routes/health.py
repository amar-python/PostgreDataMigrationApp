"""Health-check route for the Migration Evaluation Platform (MEP)."""
from fastapi import APIRouter

from config import settings
from database.connection import check_db_connection

router = APIRouter(tags=["health"])

# Application version, kept in sync with the FastAPI app version.
VERSION = "0.1.0"


@router.get("/health")
def health() -> dict:
    """Report service health.

    Always returns HTTP 200. If the database is unreachable, the response still
    succeeds but reports ``"database": "disconnected"``.
    """
    db_connected = check_db_connection()
    return {
        "status": "healthy",
        "version": VERSION,
        "environment": settings.APP_ENV,
        "database": "connected" if db_connected else "disconnected",
    }
