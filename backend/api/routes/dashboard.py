"""API route for dashboard statistics.

GET /api/dashboard — aggregate stats for the dashboard view
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.schemas import DashboardStats
from database.connection import get_db
from services import dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    """Return aggregate dashboard statistics."""
    return dashboard_service.get_dashboard_stats(db)
