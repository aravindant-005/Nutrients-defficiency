from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    activity_level = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    predictions = relationship(
        "PredictionHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    food_logs = relationship(
        "FoodLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class FoodLog(Base):
    __tablename__ = "food_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    meal_type = Column(String, nullable=False)  # Breakfast, Lunch, Dinner, Snack
    food_name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    serving_size = Column(String, nullable=False)
    calories = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    carbohydrates = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    iron = Column(Float, nullable=True)
    calcium = Column(Float, nullable=True)
    vitamin_d = Column(Float, nullable=True)
    vitamin_b12 = Column(Float, nullable=True)
    zinc = Column(Float, nullable=True)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
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

    # Relationships
    user = relationship("User", back_populates="predictions")


class FoodCatalog(Base):
    __tablename__ = "food_catalog"

    id = Column(Integer, primary_key=True, index=True)
    fdc_id = Column(Integer, nullable=True)
    food_name = Column(String, nullable=False)
    source = Column(String, nullable=True)
    calories_kcal = Column(Float, nullable=True)
    protein_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)
    iron_mg = Column(Float, nullable=True)
    calcium_mg = Column(Float, nullable=True)
    vitamin_d_mcg = Column(Float, nullable=True)
    vitamin_b12_mcg = Column(Float, nullable=True)
    zinc_mg = Column(Float, nullable=True)
