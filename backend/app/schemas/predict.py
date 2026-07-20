from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


# ── Input ──────────────────────────────────────────────────────────────────────

class PredictInput(BaseModel):
    """
    Patient demographic and physiological attributes sent by the frontend.
    All values come from the user's registered profile or can be overridden.
    """
    age: Optional[float]          = Field(None, ge=18, le=100, description="Age in years")
    # Accept either numeric code or string label from frontend (e.g. 0/1 or 'Male'/'Female')
    gender: Optional[Union[int, str]] = Field(None, description="0/1 or 'Male'/'Female'")
    race_ethnicity: Optional[int] = Field(3,    ge=1, le=7,    description="NHANES race/ethnicity code (1-7)")
    weight_kg: Optional[float]    = Field(None, gt=0,          description="Body weight in kilograms")
    height_cm: Optional[float]    = Field(None, gt=0,          description="Height in centimetres")
    bmi: Optional[float]          = Field(None, gt=0,          description="Body Mass Index (kg/m^2)")
    activity_level: Optional[str] = Field(None,                description="User physical activity level")
    include_shap: bool            = Field(True,                description="Include SHAP feature explanations")
    # Optional override: aggregate food log for a specific date (YYYY-MM-DD)
    date_str: Optional[str]       = Field(None,                description="Optional date (YYYY-MM-DD) to use for food log aggregation")
    # Optional: frontend can supply already-aggregated nutrient totals to bypass DB aggregation
    nutrient_totals: Optional[Dict[str, float]] = Field(None, description="Optional per-nutrient totals to use for prediction")


# ── SHAP explanation item ──────────────────────────────────────────────────────

class ShapFeature(BaseModel):
    feature: str
    value: float
    contribution: float


# ── Per-nutrient result ────────────────────────────────────────────────────────

class NutrientRisk(BaseModel):
    risk_score: float                     # probability 0.0 – 1.0
    risk_label: str                       # "Low", "Moderate", "High"
    explanation: Optional[List[ShapFeature]] = None


class RecommendationFoodItem(BaseModel):
    food_name: str
    nutrient_amount: float
    unit: str

class NutrientTarget(BaseModel):
    nutrient: str
    target_value: float
    unit: str

class RecommendationsOut(BaseModel):
    foods_to_eat: List[RecommendationFoodItem]
    foods_to_avoid: List[str]
    daily_nutrient_targets: List[NutrientTarget]
    short_health_advice: str

# ── Full prediction response ───────────────────────────────────────────────────

class PredictResponse(BaseModel):
    user_id: int
    prediction_date: datetime
    results: Dict[str, NutrientRisk]      # keyed by nutrient name
    # Flat risk scores for backward compatibility and DB storage
    iron_risk: float
    vitamin_d_risk: float
    vitamin_b12_risk: float
    calcium_risk: float
    zinc_risk: float
    magnesium_risk: float = 0.0
    vitamin_c_risk: float = 0.0
    recommendations: Optional[RecommendationsOut] = None


# ── History schema ─────────────────────────────────────────────────────────────

class PredictionHistoryOut(BaseModel):
    id: int
    user_id: int
    iron_risk: float
    vitamin_d_risk: float
    vitamin_b12_risk: float
    calcium_risk: float
    zinc_risk: float
    magnesium_risk: float = 0.0
    vitamin_c_risk: float = 0.0
    prediction_date: datetime

    model_config = ConfigDict(from_attributes=True)
