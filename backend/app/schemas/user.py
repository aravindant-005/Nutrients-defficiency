from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None

    # Basic demographics
    age: Optional[int] = None
    gender: Optional[str] = None          # Male / Female / Other
    height: Optional[float] = None        # cm
    weight: Optional[float] = None        # kg
    bmi: Optional[float] = None

    # Extended health profile
    activity_level: Optional[str] = None  # Sedentary / Light / Moderate / Active / Very Active
    occupation: Optional[str] = None
    sleep_hours: Optional[float] = None
    water_intake_l: Optional[float] = None
    is_smoker: Optional[bool] = None
    drinks_alcohol: Optional[bool] = None
    medical_conditions: Optional[str] = None   # comma-separated
    food_allergies: Optional[str] = None       # comma-separated
    diet_preference: Optional[str] = None      # Vegetarian / Non-Vegetarian / Vegan


class UserCreate(UserBase):
    email: EmailStr
    name: str
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserOut(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
