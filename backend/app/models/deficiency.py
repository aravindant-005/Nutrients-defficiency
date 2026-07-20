"""
app/models/deficiency.py
-----------------------
SQLAlchemy ORM models for all database tables.
Covers: User, FoodLog, PredictionHistory, FoodCatalog, MealPlan
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    ForeignKey, DateTime, Text, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, index=True)
    name             = Column(String(255), nullable=False)
    email            = Column(String(255), unique=True, index=True, nullable=False)
    password_hash    = Column(String(255), nullable=False)

    # ── Basic demographics ────────────────────────────────────────────────────
    age              = Column(Integer, nullable=True)
    gender           = Column(String(20), nullable=True)        # Male / Female / Other
    height           = Column(Float, nullable=True)             # cm
    weight           = Column(Float, nullable=True)             # kg
    bmi              = Column(Float, nullable=True)

    # ── Extended health profile ───────────────────────────────────────────────
    activity_level   = Column(String(50), nullable=True)        # Sedentary / Light / Moderate / Active / Very Active
    occupation       = Column(String(100), nullable=True)
    sleep_hours      = Column(Float, nullable=True)             # hours/night
    water_intake_l   = Column(Float, nullable=True)             # litres/day
    is_smoker        = Column(Boolean, default=False, nullable=True)
    drinks_alcohol   = Column(Boolean, default=False, nullable=True)
    medical_conditions = Column(Text, nullable=True)            # comma-separated
    food_allergies   = Column(Text, nullable=True)              # comma-separated
    diet_preference  = Column(String(30), nullable=True)        # Vegetarian / Non-Vegetarian / Vegan

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())

    # ── Relationships ─────────────────────────────────────────────────────────
    predictions = relationship(
        "PredictionHistory", back_populates="user", cascade="all, delete-orphan"
    )
    food_logs = relationship(
        "FoodLog", back_populates="user", cascade="all, delete-orphan"
    )
    meal_plans = relationship(
        "MealPlan", back_populates="user", cascade="all, delete-orphan"
    )


class FoodLog(Base):
    __tablename__ = "food_logs"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    meal_type        = Column(String(20), nullable=False)       # Breakfast / Lunch / Dinner / Snack

    # ── Food identity ─────────────────────────────────────────────────────────
    food_name        = Column(String(500), nullable=False)
    quantity         = Column(Float, nullable=False)
    serving_size     = Column(String(50), nullable=False)       # grams / ml / cup / piece / tablespoon

    # ── Macronutrients ────────────────────────────────────────────────────────
    calories         = Column(Float, nullable=True, default=0.0)
    protein          = Column(Float, nullable=True, default=0.0)       # g
    carbohydrates    = Column(Float, nullable=True, default=0.0)       # g
    fat              = Column(Float, nullable=True, default=0.0)       # g
    fiber            = Column(Float, nullable=True, default=0.0)       # g
    sugar            = Column(Float, nullable=True, default=0.0)       # g

    # ── Micronutrients — Minerals ─────────────────────────────────────────────
    iron             = Column(Float, nullable=True, default=0.0)       # mg
    calcium          = Column(Float, nullable=True, default=0.0)       # mg
    magnesium        = Column(Float, nullable=True, default=0.0)       # mg
    potassium        = Column(Float, nullable=True, default=0.0)       # mg
    sodium           = Column(Float, nullable=True, default=0.0)       # mg
    zinc             = Column(Float, nullable=True, default=0.0)       # mg
    copper           = Column(Float, nullable=True, default=0.0)       # mg
    phosphorus       = Column(Float, nullable=True, default=0.0)       # mg

    # ── Micronutrients — Vitamins ─────────────────────────────────────────────
    vitamin_a        = Column(Float, nullable=True, default=0.0)       # mcg RAE
    vitamin_c        = Column(Float, nullable=True, default=0.0)       # mg
    vitamin_d        = Column(Float, nullable=True, default=0.0)       # mcg
    vitamin_e        = Column(Float, nullable=True, default=0.0)       # mg
    vitamin_k        = Column(Float, nullable=True, default=0.0)       # mcg
    vitamin_b1       = Column(Float, nullable=True, default=0.0)       # mg (Thiamine)
    vitamin_b2       = Column(Float, nullable=True, default=0.0)       # mg (Riboflavin)
    vitamin_b6       = Column(Float, nullable=True, default=0.0)       # mg
    vitamin_b12      = Column(Float, nullable=True, default=0.0)       # mcg

    logged_at        = Column(DateTime(timezone=True), server_default=func.now())

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship("User", back_populates="food_logs")


class PredictionHistory(Base):
    __tablename__ = "prediction_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    iron_risk = Column(Float, nullable=False)
    vitamin_d_risk = Column(Float, nullable=False)
    vitamin_b12_risk = Column(Float, nullable=False)
    calcium_risk = Column(Float, nullable=False)
    zinc_risk = Column(Float, nullable=False)
    magnesium_risk = Column(Float, nullable=False, default=0.0)
    vitamin_c_risk = Column(Float, nullable=False, default=0.0)
    prediction_date = Column(DateTime(timezone=True), server_default=func.now())
    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # ── Deficiency risk scores (0.0 – 1.0) ───────────────────────────────────
    iron_risk        = Column(Float, nullable=False, default=0.0)
    vitamin_d_risk   = Column(Float, nullable=False, default=0.0)
    vitamin_b12_risk = Column(Float, nullable=False, default=0.0)
    calcium_risk     = Column(Float, nullable=False, default=0.0)
    zinc_risk        = Column(Float, nullable=False, default=0.0)
    magnesium_risk   = Column(Float, nullable=False, default=0.0)
    vitamin_c_risk   = Column(Float, nullable=False, default=0.0)

    prediction_date  = Column(DateTime(timezone=True), server_default=func.now())

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship("User", back_populates="predictions")


class FoodCatalog(Base):
    """
    Unified food nutrition database — populated from USDA FDC, Open Food Facts, IFCT.
    Values are per 100g of the food item unless otherwise noted.
    """
    __tablename__ = "food_catalog"

    id               = Column(Integer, primary_key=True, index=True)
    fdc_id           = Column(Integer, nullable=True, index=True)
    food_name        = Column(String(500), nullable=False, index=True)
    source           = Column(String(50), nullable=True)        # USDA / OpenFoodFacts / IFCT
    food_category    = Column(String(100), nullable=True)
    cuisine_type     = Column(String(50), nullable=True)        # Indian / Western / Global
    serving_size_g   = Column(Float, nullable=True)             # standard serving in grams

    # ── Macronutrients (per 100g) ─────────────────────────────────────────────
    calories_kcal    = Column(Float, nullable=True)
    protein_g        = Column(Float, nullable=True)
    carbs_g          = Column(Float, nullable=True)
    fat_g            = Column(Float, nullable=True)
    fiber_g          = Column(Float, nullable=True)
    sugar_g          = Column(Float, nullable=True)

    # ── Minerals (per 100g) ───────────────────────────────────────────────────
    iron_mg          = Column(Float, nullable=True)
    calcium_mg       = Column(Float, nullable=True)
    magnesium_mg     = Column(Float, nullable=True)
    potassium_mg     = Column(Float, nullable=True)
    sodium_mg        = Column(Float, nullable=True)
    zinc_mg          = Column(Float, nullable=True)
    copper_mg        = Column(Float, nullable=True)
    phosphorus_mg    = Column(Float, nullable=True)

    # ── Vitamins (per 100g) ───────────────────────────────────────────────────
    vitamin_a_mcg    = Column(Float, nullable=True)             # RAE
    vitamin_c_mg     = Column(Float, nullable=True)
    vitamin_d_mcg    = Column(Float, nullable=True)
    vitamin_e_mg     = Column(Float, nullable=True)
    vitamin_k_mcg    = Column(Float, nullable=True)
    vitamin_b1_mg    = Column(Float, nullable=True)             # Thiamine
    vitamin_b2_mg    = Column(Float, nullable=True)             # Riboflavin
    vitamin_b6_mg    = Column(Float, nullable=True)
    vitamin_b12_mcg  = Column(Float, nullable=True)


class MealPlan(Base):
    """Stores generated weekly meal plans for users."""
    __tablename__ = "meal_plans"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    week_start       = Column(DateTime(timezone=True), nullable=False)
    plan_data        = Column(JSON, nullable=False)              # structured weekly plan JSON
    deficiency_focus = Column(String(200), nullable=True)       # comma-separated target deficiencies
    diet_preference  = Column(String(30), nullable=True)        # Vegetarian / Non-Vegetarian / Vegan
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship("User", back_populates="meal_plans")
