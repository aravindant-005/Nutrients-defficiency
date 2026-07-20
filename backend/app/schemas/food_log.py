from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class FoodLogBase(BaseModel):
    food_name: str
    quantity: float
    serving_size: str                           # grams / ml / cup / piece / tablespoon

    # Macronutrients
    calories: Optional[float] = 0.0
    protein: Optional[float] = 0.0             # g
    carbohydrates: Optional[float] = 0.0       # g
    fat: Optional[float] = 0.0                 # g
    fiber: Optional[float] = 0.0               # g
    sugar: Optional[float] = 0.0               # g

    # Minerals
    iron: Optional[float] = 0.0               # mg
    calcium: Optional[float] = 0.0            # mg
    magnesium: Optional[float] = 0.0          # mg
    potassium: Optional[float] = 0.0          # mg
    sodium: Optional[float] = 0.0             # mg
    zinc: Optional[float] = 0.0               # mg
    copper: Optional[float] = 0.0             # mg
    phosphorus: Optional[float] = 0.0         # mg

    # Vitamins
    vitamin_a: Optional[float] = 0.0          # mcg RAE
    vitamin_c: Optional[float] = 0.0          # mg
    vitamin_d: Optional[float] = 0.0          # mcg
    vitamin_e: Optional[float] = 0.0          # mg
    vitamin_k: Optional[float] = 0.0          # mcg
    vitamin_b1: Optional[float] = 0.0         # mg
    vitamin_b2: Optional[float] = 0.0         # mg
    vitamin_b6: Optional[float] = 0.0         # mg
    vitamin_b12: Optional[float] = 0.0        # mcg


class FoodLogCreate(FoodLogBase):
    meal_type: str  # Breakfast, Lunch, Dinner, Snack

    @field_validator('meal_type')
    @classmethod
    def validate_meal_type(cls, v: str) -> str:
        allowed = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
        if v not in allowed:
            raise ValueError(f"meal_type must be one of {allowed}")
        return v


class FoodLogOut(FoodLogBase):
    id: int
    user_id: int
    meal_type: str
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DailySummary(BaseModel):
    """Aggregated daily nutrient totals."""
    # Macros
    calories: float = 0.0
    protein: float = 0.0
    carbohydrates: float = 0.0
    fat: float = 0.0
    fiber: float = 0.0
    sugar: float = 0.0

    # Minerals
    iron: float = 0.0
    calcium: float = 0.0
    magnesium: float = 0.0
    potassium: float = 0.0
    sodium: float = 0.0
    zinc: float = 0.0
    copper: float = 0.0
    phosphorus: float = 0.0

    # Vitamins
    vitamin_a: float = 0.0
    vitamin_c: float = 0.0
    vitamin_d: float = 0.0
    vitamin_e: float = 0.0
    vitamin_k: float = 0.0
    vitamin_b1: float = 0.0
    vitamin_b2: float = 0.0
    vitamin_b6: float = 0.0
    vitamin_b12: float = 0.0


class FoodCatalogOut(BaseModel):
    id: int
    fdc_id: Optional[int] = None
    food_name: str
    source: Optional[str] = None
    food_category: Optional[str] = None
    cuisine_type: Optional[str] = None
    serving_size_g: Optional[float] = None

    # Macros
    calories_kcal: Optional[float] = 0.0
    protein_g: Optional[float] = 0.0
    carbs_g: Optional[float] = 0.0
    fat_g: Optional[float] = 0.0
    fiber_g: Optional[float] = 0.0
    sugar_g: Optional[float] = 0.0

    # Minerals
    iron_mg: Optional[float] = 0.0
    calcium_mg: Optional[float] = 0.0
    magnesium_mg: Optional[float] = 0.0
    potassium_mg: Optional[float] = 0.0
    sodium_mg: Optional[float] = 0.0
    zinc_mg: Optional[float] = 0.0
    copper_mg: Optional[float] = 0.0
    phosphorus_mg: Optional[float] = 0.0

    # Vitamins
    vitamin_a_mcg: Optional[float] = 0.0
    vitamin_c_mg: Optional[float] = 0.0
    vitamin_d_mcg: Optional[float] = 0.0
    vitamin_e_mg: Optional[float] = 0.0
    vitamin_k_mcg: Optional[float] = 0.0
    vitamin_b1_mg: Optional[float] = 0.0
    vitamin_b2_mg: Optional[float] = 0.0
    vitamin_b6_mg: Optional[float] = 0.0
    vitamin_b12_mcg: Optional[float] = 0.0

    model_config = ConfigDict(from_attributes=True)
