"""
recommendations.py — GET /api/v1/recommendations
Returns personalized food recommendations based on the user's latest
deficiency prediction run.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.deficiency import User, PredictionHistory
from app.schemas.predict import RecommendationsOut
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.get("/", response_model=RecommendationsOut)
def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return personalized food recommendations based on the user's most recent
    deficiency prediction. If no prediction has been run yet, returns general
    recommendations for a balanced diet.
    """
    # Get latest prediction
    latest = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == current_user.id)
        .order_by(PredictionHistory.prediction_date.desc())
        .first()
    )

    if latest:
        risks = {
            "iron": latest.iron_risk,
            "calcium": latest.calcium_risk,
            "vitamin_d": latest.vitamin_d_risk,
            "vitamin_b12": latest.vitamin_b12_risk,
            "zinc": latest.zinc_risk,
            "magnesium": latest.magnesium_risk,
            "vitamin_c": latest.vitamin_c_risk,
        }
    else:
        # Default to moderate risk across all to give general recommendations
        risks = {k: 0.0 for k in ["iron", "calcium", "vitamin_d", "vitamin_b12", "zinc", "magnesium", "vitamin_c"]}

    return RecommendationService.generate_recommendations(db, current_user, risks)
