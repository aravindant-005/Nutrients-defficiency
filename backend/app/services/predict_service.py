from datetime import datetime, timezone, date, time
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.deficiency import User, FoodLog, PredictionHistory
from app.schemas.predict import PredictInput, PredictResponse, NutrientRisk, ShapFeature
from app.ml.model import run_prediction
from app.ml.explainer import run_explanation
from app.services.recommendation_service import RecommendationService

class PredictionService:
    @staticmethod
    def get_user_profile(user: User, data: Optional[PredictInput] = None) -> Dict[str, Any]:
        """
        Extract user profile fields, prioritizing request payload (if provided)
        and falling back to the database user profile. Converts gender strings to binary format.
        """
        # Read from input payload or DB User model
        age = (data.age if data and data.age is not None else user.age)
        gender_raw = (data.gender if data and data.gender is not None else user.gender)
        weight_kg = (data.weight_kg if data and data.weight_kg is not None else user.weight)
        height_cm = (data.height_cm if data and data.height_cm is not None else user.height)
        bmi = (data.bmi if data and data.bmi is not None else user.bmi)
        activity_level = (data.activity_level if data and data.activity_level is not None else user.activity_level)
        race_ethnicity = (data.race_ethnicity if data and data.race_ethnicity is not None else 3) # default NHANES category

        # Validate that all required demographics are present
        missing = []
        if age is None: missing.append("age")
        if gender_raw is None: missing.append("gender")
        if weight_kg is None: missing.append("weight")
        if height_cm is None: missing.append("height")

        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The following profile fields are missing: {', '.join(missing)}. "
                       f"Please update your profile or provide them in the request body."
            )

        # Convert raw gender string/int to integer index (0 = Male, 1 = Female)
        gender_val: int
        if isinstance(gender_raw, int) or isinstance(gender_raw, float):
            gender_raw_int = int(gender_raw)
            if gender_raw_int not in (0, 1):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Gender value must be 0 (Male) or 1 (Female)"
                )
            gender_val = gender_raw_int
        elif isinstance(gender_raw, str):
            g_lower = gender_raw.strip().lower()
            if g_lower in ("male", "m", "0"):
                gender_val = 0
            elif g_lower in ("female", "f", "1"):
                gender_val = 1
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Could not parse gender string '{gender_raw}'. Expected 'Male' or 'Female'."
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid type for gender field."
            )

        # Auto-compute BMI if missing but height and weight are provided
        if bmi is None or bmi <= 0.0:
            if height_cm > 0:
                bmi = weight_kg / ((height_cm / 100.0) ** 2)
            else:
                bmi = 22.0 # fallback default

        return {
            "age": float(age),
            "gender": gender_val,
            "weight_kg": float(weight_kg),
            "height_cm": float(height_cm),
            "bmi": float(bmi),
            "activity_level": activity_level,
            "race_ethnicity": int(race_ethnicity),
        }

    @staticmethod
    def calculate_daily_nutrient_totals(db: Session, user_id: int, target_date: date) -> Dict[str, float]:
        """
        Aggregate total nutrient amounts consumed by the user today (UTC).
        """
        start_datetime = datetime.combine(target_date, time.min)
        end_datetime = datetime.combine(target_date, time.max)

        summary = db.query(
            func.sum(FoodLog.calories).label('calories'),
            func.sum(FoodLog.protein).label('protein'),
            func.sum(FoodLog.carbohydrates).label('carbohydrates'),
            func.sum(FoodLog.fat).label('fat'),
            func.sum(FoodLog.iron).label('iron'),
            func.sum(FoodLog.calcium).label('calcium'),
            func.sum(FoodLog.vitamin_d).label('vitamin_d'),
            func.sum(FoodLog.vitamin_b12).label('vitamin_b12'),
            func.sum(FoodLog.zinc).label('zinc')
        ).filter(
            FoodLog.user_id == user_id,
            FoodLog.logged_at >= start_datetime,
            FoodLog.logged_at <= end_datetime
        ).first()

        # Map to raw NHANES feature formats & units
        return {
            "calories_kcal": float(summary.calories or 0.0),
            "protein_g": float(summary.protein or 0.0),
            "carbs_g": float(summary.carbohydrates or 0.0),
            "fat_g": float(summary.fat or 0.0),
            "iron_mg": float(summary.iron or 0.0),
            "calcium_mg": float(summary.calcium or 0.0),
            "vitamin_d_mcg": float(summary.vitamin_d or 0.0),
            "vitamin_b12_mcg": float(summary.vitamin_b12 or 0.0),
            "zinc_mg": float(summary.zinc or 0.0),
        }

    @classmethod
    def execute_prediction(
        cls,
        db: Session,
        current_user: User,
        data: Optional[PredictInput] = None
    ) -> PredictResponse:
        """
        Run the ML forecasting pipeline.
        Calculates today's food log totals, resolves user profile, runs model, and stores history.
        """
        # 1. Resolve patient profile
        profile = cls.get_user_profile(current_user, data)

        # 2. Get daily nutrient totals: allow payload override or date override
        if data and getattr(data, "nutrient_totals", None):
            nutrient_totals = data.nutrient_totals
        else:
            if data and getattr(data, "date_str", None):
                try:
                    target_date = datetime.strptime(data.date_str, "%Y-%m-%d").date()
                except Exception:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="date_str must be in YYYY-MM-DD format"
                    )
            else:
                target_date = datetime.utcnow().date()

            nutrient_totals = cls.calculate_daily_nutrient_totals(db, current_user.id, target_date)

        # 3. Call prediction model
        try:
            predictions = run_prediction(
                age=profile["age"],
                gender=profile["gender"],
                race_ethnicity=profile["race_ethnicity"],
                weight_kg=profile["weight_kg"],
                height_cm=profile["height_cm"],
                bmi=profile["bmi"],
                activity_level=profile["activity_level"],
                nutrient_totals=nutrient_totals,
            )
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Model files not configured. Please run training script first. ({e})"
            )

        # 4. Generate SHAP feature importances if requested
        include_shap = data.include_shap if data is not None else True
        results = {}
        nutrients_list = ["iron", "calcium", "vitamin_d", "vitamin_b12", "zinc"]

        for nutrient in nutrients_list:
            pred = predictions.get(nutrient, {"risk_score": 0.0, "risk_label": "Unknown"})

            shap_items = None
            if include_shap:
                raw_shap = run_explanation(
                    nutrient=nutrient,
                    age=profile["age"],
                    gender=profile["gender"],
                    race_ethnicity=profile["race_ethnicity"],
                    weight_kg=profile["weight_kg"],
                    height_cm=profile["height_cm"],
                    bmi=profile["bmi"],
                    activity_level=profile["activity_level"],
                    nutrient_totals=nutrient_totals,
                )
                if raw_shap:
                    shap_items = [
                        ShapFeature(
                            feature=s["feature"],
                            value=s["value"],
                            contribution=s["contribution"]
                        )
                        for s in raw_shap
                    ]

            results[nutrient] = NutrientRisk(
                risk_score=pred["risk_score"],
                risk_label=pred["risk_label"],
                explanation=shap_items,
            )

        # 5. Persist prediction to the database
        now = datetime.now(timezone.utc)
        history = PredictionHistory(
            user_id=current_user.id,
            iron_risk=results["iron"].risk_score,
            calcium_risk=results["calcium"].risk_score,
            vitamin_d_risk=results["vitamin_d"].risk_score,
            vitamin_b12_risk=results["vitamin_b12"].risk_score,
            zinc_risk=results["zinc"].risk_score,
            magnesium_risk=0.0,
            vitamin_c_risk=0.0,
            prediction_date=now,
        )
        db.add(history)
        db.commit()
        db.refresh(history)

        # 6. Generate dietary recommendations
        risk_dict = {
            "iron": results["iron"].risk_score,
            "calcium": results["calcium"].risk_score,
            "vitamin_d": results["vitamin_d"].risk_score,
            "vitamin_b12": results["vitamin_b12"].risk_score,
            "zinc": results["zinc"].risk_score,
        }
        recs = RecommendationService.generate_recommendations(db, current_user, risk_dict)

        return PredictResponse(
            user_id=current_user.id,
            prediction_date=now,
            results=results,
            iron_risk=results["iron"].risk_score,
            vitamin_d_risk=results["vitamin_d"].risk_score,
            vitamin_b12_risk=results["vitamin_b12"].risk_score,
            calcium_risk=results["calcium"].risk_score,
            zinc_risk=results["zinc"].risk_score,
            recommendations=recs,
        )
