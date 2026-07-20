from datetime import datetime, date, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.deficiency import User, FoodLog
from app.schemas.food_log import FoodLogCreate, FoodLogOut, DailySummary

router = APIRouter()


@router.post("/", response_model=FoodLogOut, status_code=status.HTTP_201_CREATED)
def create_food_log(
    food_in: FoodLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log a new food item with full macro and micronutrient data for the current user."""
    db_log = FoodLog(
        user_id=current_user.id,
        food_name=food_in.food_name,
        quantity=food_in.quantity,
        serving_size=food_in.serving_size,
        meal_type=food_in.meal_type,
        # Macros
        calories=food_in.calories,
        protein=food_in.protein,
        carbohydrates=food_in.carbohydrates,
        fat=food_in.fat,
        fiber=food_in.fiber,
        sugar=food_in.sugar,
        # Minerals
        iron=food_in.iron,
        calcium=food_in.calcium,
        magnesium=food_in.magnesium,
        potassium=food_in.potassium,
        sodium=food_in.sodium,
        zinc=food_in.zinc,
        copper=food_in.copper,
        phosphorus=food_in.phosphorus,
        # Vitamins
        vitamin_a=food_in.vitamin_a,
        vitamin_c=food_in.vitamin_c,
        vitamin_d=food_in.vitamin_d,
        vitamin_e=food_in.vitamin_e,
        vitamin_k=food_in.vitamin_k,
        vitamin_b1=food_in.vitamin_b1,
        vitamin_b2=food_in.vitamin_b2,
        vitamin_b6=food_in.vitamin_b6,
        vitamin_b12=food_in.vitamin_b12,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


@router.get("/", response_model=List[FoodLogOut])
def list_food_logs(
    date_str: Optional[str] = None,
    meal_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve food log items for the current user.
    Optionally filtered by date (YYYY-MM-DD) and/or meal_type.
    """
    query = db.query(FoodLog).filter(FoodLog.user_id == current_user.id)

    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_dt = datetime.combine(target_date, time.min)
            end_dt = datetime.combine(target_date, time.max)
            query = query.filter(FoodLog.logged_at >= start_dt, FoodLog.logged_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

    if meal_type:
        allowed = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
        if meal_type not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"meal_type must be one of {allowed}"
            )
        query = query.filter(FoodLog.meal_type == meal_type)

    return query.order_by(FoodLog.logged_at.desc()).all()


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_food_log(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific food log item owned by the current user."""
    food_log = db.query(FoodLog).filter(FoodLog.id == id).first()
    if not food_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food log not found")
    if food_log.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this log")
    db.delete(food_log)
    db.commit()
    return {"detail": "Food log deleted successfully"}


@router.get("/summary", response_model=DailySummary)
def get_daily_summary(
    date_str: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aggregate all nutrient totals for a given date (defaults to today)."""
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        target_date = datetime.utcnow().date()

    start_dt = datetime.combine(target_date, time.min)
    end_dt = datetime.combine(target_date, time.max)

    summary = db.query(
        func.coalesce(func.sum(FoodLog.calories), 0.0).label('calories'),
        func.coalesce(func.sum(FoodLog.protein), 0.0).label('protein'),
        func.coalesce(func.sum(FoodLog.carbohydrates), 0.0).label('carbohydrates'),
        func.coalesce(func.sum(FoodLog.fat), 0.0).label('fat'),
        func.coalesce(func.sum(FoodLog.fiber), 0.0).label('fiber'),
        func.coalesce(func.sum(FoodLog.sugar), 0.0).label('sugar'),
        func.coalesce(func.sum(FoodLog.iron), 0.0).label('iron'),
        func.coalesce(func.sum(FoodLog.calcium), 0.0).label('calcium'),
        func.coalesce(func.sum(FoodLog.magnesium), 0.0).label('magnesium'),
        func.coalesce(func.sum(FoodLog.potassium), 0.0).label('potassium'),
        func.coalesce(func.sum(FoodLog.sodium), 0.0).label('sodium'),
        func.coalesce(func.sum(FoodLog.zinc), 0.0).label('zinc'),
        func.coalesce(func.sum(FoodLog.copper), 0.0).label('copper'),
        func.coalesce(func.sum(FoodLog.phosphorus), 0.0).label('phosphorus'),
        func.coalesce(func.sum(FoodLog.vitamin_a), 0.0).label('vitamin_a'),
        func.coalesce(func.sum(FoodLog.vitamin_c), 0.0).label('vitamin_c'),
        func.coalesce(func.sum(FoodLog.vitamin_d), 0.0).label('vitamin_d'),
        func.coalesce(func.sum(FoodLog.vitamin_e), 0.0).label('vitamin_e'),
        func.coalesce(func.sum(FoodLog.vitamin_k), 0.0).label('vitamin_k'),
        func.coalesce(func.sum(FoodLog.vitamin_b1), 0.0).label('vitamin_b1'),
        func.coalesce(func.sum(FoodLog.vitamin_b2), 0.0).label('vitamin_b2'),
        func.coalesce(func.sum(FoodLog.vitamin_b6), 0.0).label('vitamin_b6'),
        func.coalesce(func.sum(FoodLog.vitamin_b12), 0.0).label('vitamin_b12'),
    ).filter(
        FoodLog.user_id == current_user.id,
        FoodLog.logged_at >= start_dt,
        FoodLog.logged_at <= end_dt
    ).first()

    return DailySummary(
        calories=float(summary.calories),
        protein=float(summary.protein),
        carbohydrates=float(summary.carbohydrates),
        fat=float(summary.fat),
        fiber=float(summary.fiber),
        sugar=float(summary.sugar),
        iron=float(summary.iron),
        calcium=float(summary.calcium),
        magnesium=float(summary.magnesium),
        potassium=float(summary.potassium),
        sodium=float(summary.sodium),
        zinc=float(summary.zinc),
        copper=float(summary.copper),
        phosphorus=float(summary.phosphorus),
        vitamin_a=float(summary.vitamin_a),
        vitamin_c=float(summary.vitamin_c),
        vitamin_d=float(summary.vitamin_d),
        vitamin_e=float(summary.vitamin_e),
        vitamin_k=float(summary.vitamin_k),
        vitamin_b1=float(summary.vitamin_b1),
        vitamin_b2=float(summary.vitamin_b2),
        vitamin_b6=float(summary.vitamin_b6),
        vitamin_b12=float(summary.vitamin_b12),
    )
