"""
dashboard.py — GET /api/v1/dashboard
Aggregates today's food log, 7-day trend, and latest deficiency risks
into a single comprehensive dashboard payload.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.deficiency import User
from app.schemas.dashboard import DashboardOut
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/", response_model=DashboardOut)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return a full dashboard payload for the authenticated user including:
    - Today's macro + micro nutrient totals
    - RDA percentage for each micronutrient
    - Latest deficiency risk scores from last prediction
    - 7-day nutrient intake trend
    - Meal type breakdown for today
    """
    return DashboardService.get_dashboard(db, current_user)
