from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.deficiency import User, PredictionHistory
from app.schemas.predict import PredictInput, PredictResponse, PredictionHistoryOut
from app.services.predict_service import PredictionService

router = APIRouter()


@router.post("/", response_model=PredictResponse, status_code=status.HTTP_200_OK)
def predict_deficiency(
    data: PredictInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run deficiency risk predictions for the authenticated user.

    Pipeline:
      1. Resolve user demographics (from request body or stored profile)
      2. Aggregate today's food log nutrient totals (14 features)
      3. Run ML model (XGBoost / Random Forest / best model per target)
      4. Generate SHAP explanations for each of the 7 deficiency targets
      5. Persist prediction history to PostgreSQL
      6. Generate personalized food recommendations + weekly meal plan
    """
    return PredictionService.execute_prediction(db, current_user, data)


@router.get("/history", response_model=list[PredictionHistoryOut])
def get_prediction_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the authenticated user's past deficiency prediction records (most recent first)."""
    return (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == current_user.id)
        .order_by(PredictionHistory.prediction_date.desc())
        .all()
    )
