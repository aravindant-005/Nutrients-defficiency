from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, default="Dhakshanesh R")
    age = Column(Float, default=28.0)
    gender = Column(Float, default=1.0) # 1.0 = Male, 2.0 = Female
    race = Column(Float, default=3.0)
    weight_kg = Column(Float, default=70.0)
    height_cm = Column(Float, default=175.0)
    bmi = Column(Float, default=22.86)
    activity_level = Column(String, default="Moderate")
    diet_type = Column(String, default="Vegetarian") # Vegetarian, Vegan, Non-Vegetarian
    health_conditions = Column(String, default="Anemia, Vitamin D Deficiency") # Comma-separated tags
    daily_calorie_goal = Column(Float, default=2000.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    logs = relationship("FoodLogItem", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("PredictionResult", back_populates="user", cascade="all, delete-orphan")


class FoodLogItem(Base):
    __tablename__ = "food_log_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"))
    food_code = Column(String, nullable=True)
    food_name = Column(String, nullable=False)
    serving_size_g = Column(Float, default=100.0)
    calories_kcal = Column(Float, default=0.0)
    protein_g = Column(Float, default=0.0)
    carbs_g = Column(Float, default=0.0)
    fat_g = Column(Float, default=0.0)
    fiber_g = Column(Float, default=0.0)
    iron_mg = Column(Float, default=0.0)
    calcium_mg = Column(Float, default=0.0)
    vitamin_d_mcg = Column(Float, default=0.0)
    vitamin_b12_mcg = Column(Float, default=0.0)
    zinc_mg = Column(Float, default=0.0)
    magnesium_mg = Column(Float, default=0.0)
    vitamin_c_mg = Column(Float, default=0.0)
    log_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserProfile", back_populates="logs")


class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"))
    nutrient = Column(String, nullable=False)
    risk_probability = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False) # Low, Moderate, High
    top_factor = Column(String, nullable=True)
    explanation = Column(Text, nullable=True)
    recommended_foods = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserProfile", back_populates="predictions")
