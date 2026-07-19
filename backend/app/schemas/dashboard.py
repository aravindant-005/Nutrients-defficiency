from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class NutrientSummary(BaseModel):
    """Daily macro and micro nutrient totals vs targets."""
    nutrient: str
    current: float
    target: float
    unit: str
    percentage: float           # (current / target) * 100
    status: str                 # Adequate / Low / Deficient


class WeeklyTrendPoint(BaseModel):
    date: str                   # YYYY-MM-DD
    calories: float
    iron: float
    calcium: float
    vitamin_d: float
    vitamin_b12: float
    zinc: float
    magnesium: float
    vitamin_c: float


class MealTypeSummary(BaseModel):
    meal_type: str
    count: int
    calories: float


class DashboardOut(BaseModel):
    """Complete dashboard data for the authenticated user."""
    user_id: int
    date: str                       # Today's date (YYYY-MM-DD)

    # Daily totals
    total_calories: float
    total_protein: float
    total_carbohydrates: float
    total_fat: float
    total_fiber: float

    # Micronutrient summary with RDA comparison
    nutrient_summary: List[NutrientSummary]

    # Latest deficiency risk scores
    deficiency_risks: dict          # {nutrient: {risk_score, risk_label}}

    # 7-day nutrient trend
    weekly_trend: List[WeeklyTrendPoint]

    # Meal breakdown for today
    meal_breakdown: List[MealTypeSummary]

    # Metadata
    total_food_items_today: int
    last_prediction_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
