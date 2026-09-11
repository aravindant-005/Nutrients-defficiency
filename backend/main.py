import os
import logging
from typing import List, Optional
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.database import engine, get_db, db_type, Base
from backend.models_db import UserProfile, FoodLogItem, PredictionResult
from backend.indb_service import indb_service
from backend.ml_service import ml_service, RDA_MAP
from backend.auth_utils import hash_password, verify_password, generate_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NutriDetect AI Backend API",
    description="Full-stack AI platform for food logging, INDB nutrient calculations, ML deficiency risk prediction & SHAP explanations.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas ---
class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    age: float = 28.0
    gender: float = 1.0
    weight_kg: float = 70.0
    height_cm: float = 175.0
    diet_type: str = "Vegetarian"

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdateSchema(BaseModel):
    name: str
    age: float
    gender: float
    weight_kg: float
    height_cm: float
    activity_level: str = "Moderate"
    diet_type: str = "Vegetarian"
    health_conditions: str = "Anemia, Vitamin D Deficiency"
    daily_calorie_goal: float = 2000.0

class FoodLogAddSchema(BaseModel):
    user_id: Optional[int] = 1
    food_code: Optional[str] = None
    food_name: str
    serving_size_g: float = 100.0
    calories_kcal: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: float = 0.0
    iron_mg: float = 0.0
    calcium_mg: float = 0.0
    vitamin_d_mcg: float = 0.0
    vitamin_b12_mcg: float = 0.0
    zinc_mg: float = 0.0
    magnesium_mg: float = 0.0
    vitamin_c_mg: float = 0.0

# --- Helper ---
def get_user_by_id(db: Session, user_id: int = 1) -> UserProfile:
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        user = UserProfile(
            id=user_id if user_id != 1 else None,
            email=f"user{user_id}@example.com",
            hashed_password=hash_password("password123"),
            name="Dhakshanesh R",
            age=28.0,
            gender=1.0,
            weight_kg=70.0,
            height_cm=175.0,
            bmi=22.86,
            diet_type="Vegetarian",
            health_conditions="Anemia, Vitamin D Deficiency"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# --- Auth Routes ---
@app.post("/api/auth/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    existing = db.query(UserProfile).filter(UserProfile.email == data.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="User email already registered")

    bmi = round(data.weight_kg / ((data.height_cm / 100.0) ** 2), 2)
    user = UserProfile(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        name=data.name,
        age=data.age,
        gender=data.gender,
        weight_kg=data.weight_kg,
        height_cm=data.height_cm,
        bmi=bmi,
        diet_type=data.diet_type
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = generate_token(user.email)
    return {
        "message": "Account registered successfully",
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "age": user.age,
            "gender": user.gender,
            "weight_kg": user.weight_kg,
            "height_cm": user.height_cm,
            "bmi": user.bmi,
            "diet_type": user.diet_type,
            "health_conditions": user.health_conditions
        }
    }

@app.post("/api/auth/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(UserProfile).filter(UserProfile.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = generate_token(user.email)
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "age": user.age,
            "gender": user.gender,
            "weight_kg": user.weight_kg,
            "height_cm": user.height_cm,
            "bmi": user.bmi,
            "diet_type": user.diet_type,
            "health_conditions": user.health_conditions
        }
    }

@app.get("/api/auth/me/{user_id}")
def get_me(user_id: int = 1, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "age": user.age,
        "gender": user.gender,
        "weight_kg": user.weight_kg,
        "height_cm": user.height_cm,
        "bmi": user.bmi,
        "activity_level": user.activity_level,
        "diet_type": user.diet_type,
        "health_conditions": user.health_conditions,
        "daily_calorie_goal": user.daily_calorie_goal
    }

@app.post("/api/profile/update/{user_id}")
def update_profile(data: ProfileUpdateSchema, user_id: int = 1, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    user.name = data.name
    user.age = data.age
    user.gender = data.gender
    user.weight_kg = data.weight_kg
    user.height_cm = data.height_cm
    user.bmi = round(data.weight_kg / ((data.height_cm / 100.0) ** 2), 2)
    user.activity_level = data.activity_level
    user.diet_type = data.diet_type
    user.health_conditions = data.health_conditions
    user.daily_calorie_goal = data.daily_calorie_goal
    db.commit()
    db.refresh(user)
    return {"message": "Profile updated successfully", "user": get_me(user.id, db)}

# --- Food Search & Databank ---
@app.get("/api/food/search")
def search_food(q: str = Query("", description="Search term for Indian foods"), limit: int = 25):
    return indb_service.search_foods(query=q, limit=limit)

# --- Food Logging ---
@app.post("/api/logs/add")
def add_food_log(item: FoodLogAddSchema, db: Session = Depends(get_db)):
    uid = item.user_id if item.user_id else 1
    user = get_user_by_id(db, uid)
    ratio = item.serving_size_g / 100.0

    log_entry = FoodLogItem(
        user_id=user.id,
        food_code=item.food_code,
        food_name=item.food_name,
        serving_size_g=item.serving_size_g,
        calories_kcal=round(item.calories_kcal * ratio, 2),
        protein_g=round(item.protein_g * ratio, 2),
        carbs_g=round(item.carbs_g * ratio, 2),
        fat_g=round(item.fat_g * ratio, 2),
        fiber_g=round(item.fiber_g * ratio, 2),
        iron_mg=round(item.iron_mg * ratio, 2),
        calcium_mg=round(item.calcium_mg * ratio, 2),
        vitamin_d_mcg=round(item.vitamin_d_mcg * ratio, 2),
        vitamin_b12_mcg=round(item.vitamin_b12_mcg * ratio, 2),
        zinc_mg=round(item.zinc_mg * ratio, 2),
        magnesium_mg=round(item.magnesium_mg * ratio, 2),
        vitamin_c_mg=round(item.vitamin_c_mg * ratio, 2)
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return {"message": "Food item added to log", "entry_id": log_entry.id}

@app.get("/api/logs/daily/{user_id}")
def get_daily_logs(user_id: int = 1, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    logs = db.query(FoodLogItem).filter(FoodLogItem.user_id == user.id).all()
    
    totals = {
        "calories_kcal": sum(l.calories_kcal for l in logs),
        "protein_g": sum(l.protein_g for l in logs),
        "carbs_g": sum(l.carbs_g for l in logs),
        "fat_g": sum(l.fat_g for l in logs),
        "fiber_g": sum(l.fiber_g for l in logs),
        "iron_mg": sum(l.iron_mg for l in logs),
        "calcium_mg": sum(l.calcium_mg for l in logs),
        "vitamin_d_mcg": sum(l.vitamin_d_mcg for l in logs),
        "vitamin_b12_mcg": sum(l.vitamin_b12_mcg for l in logs),
        "zinc_mg": sum(l.zinc_mg for l in logs),
        "magnesium_mg": sum(l.magnesium_mg for l in logs),
        "vitamin_c_mg": sum(l.vitamin_c_mg for l in logs),
    }

    for k in totals:
        totals[k] = round(totals[k], 2)

    return {
        "logs": logs,
        "daily_totals": totals,
        "rda_targets": RDA_MAP,
        "logs_count": len(logs)
    }

@app.get("/api/logs/history/{user_id}")
def get_logs_history(user_id: int = 1, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    logs = db.query(FoodLogItem).filter(FoodLogItem.user_id == user.id).all()

    grouped = defaultdict(list)
    for log in logs:
        date_str = log.log_date.strftime("%Y-%m-%d") if log.log_date else datetime.utcnow().strftime("%Y-%m-%d")
        grouped[date_str].append(log)

    history = []
    for date_key, items in sorted(grouped.items(), reverse=True):
        tot_kcal = round(sum(i.calories_kcal for i in items), 1)
        tot_prot = round(sum(i.protein_g for i in items), 1)
        tot_iron = round(sum(i.iron_mg for i in items), 2)
        tot_calc = round(sum(i.calcium_mg for i in items), 1)
        tot_vitc = round(sum(i.vitamin_c_mg for i in items), 1)

        history.append({
            "date": date_key,
            "total_items": len(items),
            "calories_kcal": tot_kcal,
            "protein_g": tot_prot,
            "iron_mg": tot_iron,
            "calcium_mg": tot_calc,
            "vitamin_c_mg": tot_vitc,
            "items": items
        })

    return {
        "user_id": user.id,
        "total_days_logged": len(history),
        "history": history
    }

@app.delete("/api/logs/delete/{item_id}")
def delete_log(item_id: int, db: Session = Depends(get_db)):
    item = db.query(FoodLogItem).filter(FoodLogItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Log item not found")
    db.delete(item)
    db.commit()
    return {"message": "Item deleted successfully"}

# --- ML Risk Prediction & SHAP ---
@app.post("/api/predict/risk/{user_id}")
def predict_risk(user_id: int = 1, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    daily_data = get_daily_logs(user_id, db)
    totals = daily_data["daily_totals"]

    profile_dict = {
        "age": user.age,
        "gender": user.gender,
        "race": user.race,
        "weight_kg": user.weight_kg,
        "height_cm": user.height_cm,
        "bmi": user.bmi,
        "diet_type": user.diet_type
    }

    eval_output = ml_service.predict_risk_all(profile_dict, totals)

    if not eval_output["has_logged_data"]:
        return {
            "user_profile": profile_dict,
            "has_logged_data": False,
            "message": "No meals logged for today yet. Search & log your food items first!",
            "predictions": [],
            "timestamp": datetime.utcnow().isoformat()
        }

    predictions = eval_output["predictions"]

    for p in predictions:
        res = PredictionResult(
            user_id=user.id,
            nutrient=p["nutrient"],
            risk_probability=p["risk_probability"],
            risk_level=p["risk_level"],
            top_factor=p["top_factor"],
            explanation=p["explanation"],
            recommended_foods=", ".join(p["recommended_foods"])
        )
        db.add(res)
    db.commit()

    return {
        "user_profile": profile_dict,
        "has_logged_data": True,
        "predictions": predictions,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/recommendations/{user_id}")
def get_recommendations(user_id: int = 1, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    preds_response = predict_risk(user_id, db)
    
    if not preds_response.get("has_logged_data", False):
        return {
            "has_logged_data": False,
            "message": "Log your daily meals in the Food Logger tab to view AI-suggested Indian food replenishers!",
            "recommendations": []
        }

    predictions = preds_response["predictions"]

    risk_nutrients = [p for p in predictions if p["risk_level"] in ["High Risk", "Moderate Risk"]]
    if not risk_nutrients:
        risk_nutrients = predictions

    recs = []
    for nut_info in risk_nutrients:
        recs.append({
            "nutrient": nut_info["nutrient"],
            "display_name": nut_info["display_name"],
            "risk_level": nut_info["risk_level"],
            "risk_probability": nut_info["risk_probability"],
            "top_driving_factor": nut_info["top_factor"],
            "shap_explanation": nut_info["explanation"],
            "diet_type": user.diet_type,
            "recommended_indian_foods": nut_info["recommended_foods"]
        })

    return {
        "has_logged_data": True,
        "recommendations": recs
    }
