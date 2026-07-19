"""
meal_plan.py — POST /api/v1/meal-plan/generate | GET /api/v1/meal-plan
Weekly meal plan generation and retrieval endpoints.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.deficiency import User, PredictionHistory, MealPlan
from app.schemas.predict import MealPlanGenerateRequest, MealPlanOut
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.post("/generate", response_model=MealPlanOut, status_code=status.HTTP_201_CREATED)
def generate_meal_plan(
    request: MealPlanGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate and persist a personalized 7-day meal plan based on the user's
    latest deficiency predictions and dietary preferences.
    """
    # Determine diet preference (request overrides profile)
    diet_pref = request.diet_preference or current_user.diet_preference or "Non-Vegetarian"

    # Get latest prediction risks
    latest = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == current_user.id)
        .order_by(PredictionHistory.prediction_date.desc())
        .first()
    )

    if request.deficiency_focus:
        deficiency_keys = request.deficiency_focus
    elif latest:
        risks = {
            "iron": latest.iron_risk,
            "calcium": latest.calcium_risk,
            "vitamin_d": latest.vitamin_d_risk,
            "vitamin_b12": latest.vitamin_b12_risk,
            "zinc": latest.zinc_risk,
            "magnesium": latest.magnesium_risk,
            "vitamin_c": latest.vitamin_c_risk,
        }
        deficiency_keys = [k for k, v in sorted(risks.items(), key=lambda x: x[1], reverse=True) if v >= 0.45]
        if not deficiency_keys:
            deficiency_keys = list(risks.keys())[:3]
    else:
        deficiency_keys = ["iron", "calcium", "vitamin_d"]

    # Generate weekly plan
    plan_data = RecommendationService.generate_weekly_meal_plan(
        deficiency_keys=deficiency_keys,
        diet_preference=diet_pref
    )

    now = datetime.now(timezone.utc)
    meal_plan = MealPlan(
        user_id=current_user.id,
        week_start=now,
        plan_data=plan_data,
        deficiency_focus=", ".join(deficiency_keys),
        diet_preference=diet_pref,
    )
    db.add(meal_plan)
    db.commit()
    db.refresh(meal_plan)
    return meal_plan


@router.get("/", response_model=MealPlanOut)
def get_latest_meal_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the most recently generated meal plan for the current user."""
    plan = (
        db.query(MealPlan)
        .filter(MealPlan.user_id == current_user.id)
        .order_by(MealPlan.created_at.desc())
        .first()
    )
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No meal plan found. Use POST /meal-plan/generate to create one."
        )
    return plan
