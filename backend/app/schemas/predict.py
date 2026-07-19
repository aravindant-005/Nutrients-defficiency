from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


# ── Prediction Input ───────────────────────────────────────────────────────────

class PredictInput(BaseModel):
    """
    Optional demographic overrides. If not provided, values are taken from the
    authenticated user's stored profile.
    """
    age: Optional[float]          = Field(None, ge=1, le=120, description="Age in years")
    gender: Optional[Union[str, int]] = Field(None, description="Male / Female / Other or 0/1")
    weight_kg: Optional[float]    = Field(None, gt=0, description="Body weight in kilograms")
    height_cm: Optional[float]    = Field(None, gt=0, description="Height in centimetres")
    bmi: Optional[float]          = Field(None, gt=0, description="Body Mass Index (kg/m²)")
    activity_level: Optional[str] = Field(None, description="Physical activity level")
    include_shap: bool            = Field(True, description="Include SHAP feature explanations")


# ── SHAP Explanation ──────────────────────────────────────────────────────────

class ShapFeature(BaseModel):
    feature: str
    value: float
    contribution: float


# ── Per-nutrient result ───────────────────────────────────────────────────────

class NutrientRisk(BaseModel):
    risk_score: float                          # probability 0.0 – 1.0
    risk_label: str                            # Low / Moderate / High
    explanation: Optional[List[ShapFeature]] = None


# ── Recommendation types ──────────────────────────────────────────────────────

class RecommendationFoodItem(BaseModel):
    food_name: str
    nutrient_amount: float
    unit: str
    is_vegetarian: bool = True
    is_indian: bool = False
    meal_suggestion: Optional[str] = None


class NutrientTarget(BaseModel):
    nutrient: str
    target_value: float
    current_value: float = 0.0
    unit: str
    percentage_achieved: float = 0.0


class DayMealPlan(BaseModel):
    day: str                                   # Monday, Tuesday, ...
    breakfast: List[str]
    lunch: List[str]
    dinner: List[str]
    snacks: List[str]


class RecommendationsOut(BaseModel):
    foods_to_eat: List[RecommendationFoodItem]
    foods_to_avoid: List[str]
    daily_nutrient_targets: List[NutrientTarget]
    short_health_advice: str
    weekly_meal_plan: Optional[List[DayMealPlan]] = None


# ── Full prediction response ──────────────────────────────────────────────────

class PredictResponse(BaseModel):
    user_id: int
    prediction_date: datetime
    results: Dict[str, NutrientRisk]           # keyed by nutrient name

    # Flat risk scores for convenience and DB storage
    iron_risk: float
    vitamin_d_risk: float
    vitamin_b12_risk: float
    calcium_risk: float
    zinc_risk: float
    magnesium_risk: float
    vitamin_c_risk: float

    recommendations: Optional[RecommendationsOut] = None


# ── History schema ────────────────────────────────────────────────────────────

class PredictionHistoryOut(BaseModel):
    id: int
    user_id: int
    iron_risk: float
    vitamin_d_risk: float
    vitamin_b12_risk: float
    calcium_risk: float
    zinc_risk: float
    magnesium_risk: float
    vitamin_c_risk: float
    prediction_date: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Meal Plan schemas ─────────────────────────────────────────────────────────

class MealPlanGenerateRequest(BaseModel):
    diet_preference: Optional[str] = None     # Vegetarian / Non-Vegetarian / Vegan
    deficiency_focus: Optional[List[str]] = None  # override detected deficiencies


class MealPlanOut(BaseModel):
    id: int
    user_id: int
    week_start: datetime
    plan_data: dict
    deficiency_focus: Optional[str] = None
    diet_preference: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
