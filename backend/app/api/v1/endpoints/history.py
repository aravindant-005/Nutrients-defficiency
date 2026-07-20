"""
history.py — GET /api/v1/history
Retrieves the user's full prediction history with pagination support.
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.deficiency import User, PredictionHistory
from app.schemas.predict import PredictionHistoryOut

router = APIRouter()


@router.get("/", response_model=List[PredictionHistoryOut])
def get_prediction_history(
    limit: int = Query(30, ge=1, le=100, description="Max records to return"),
    skip: int = Query(0, ge=0, description="Records to skip (for pagination)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the authenticated user's deficiency prediction history.
    Returns records sorted most-recent first. Supports pagination via limit/skip.
    """
    return (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == current_user.id)
        .order_by(PredictionHistory.prediction_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
