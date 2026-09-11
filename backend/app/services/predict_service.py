"""
predict_service.py
------------------
Orchestrates the full ML prediction pipeline:
  1. Resolve user demographics from DB profile or request payload
  2. Aggregate today's food log nutrient totals (14 feature dimensions)
  3. Call ML model (best of XGBoost / Random Forest per target)
  4. Generate SHAP explanations for each of the 7 deficiency targets
  5. Persist prediction history to PostgreSQL
  6. Generate personalized recommendations
"""
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

# All 7 deficiency targets
NUTRIENT_TARGETS = ["iron", "calcium", "vitamin_d", "vitamin_b12", "zinc", "magnesium", "vitamin_c"]


class PredictionService:

    @staticmethod
    def get_user_profile(user: User, data: Optional[PredictInput] = None) -> Dict[str, Any]:
        """
        Resolve patient demographics — request payload takes priority over stored profile.
        Gender strings are normalised to 0 (Male) / 1 (Female).
        BMI is auto-computed if missing but height/weight are available.
        """
        age            = (data.age if data and data.age is not None else user.age)
        gender_raw     = (data.gender if data and data.gender is not None else user.gender)
        weight_kg      = (data.weight_kg if data and data.weight_kg is not None else user.weight)
        height_cm      = (data.height_cm if data and data.height_cm is not None else user.height)
        bmi            = (data.bmi if data and data.bmi is not None else user.bmi)
        activity_level = (data.activity_level if data and data.activity_level is not None else user.activity_level)

        # Validate required fields
        missing = []
        if age is None:       missing.append("age")
        if gender_raw is None: missing.append("gender")
        if weight_kg is None:  missing.append("weight")
        if height_cm is None:  missing.append("height")

        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required profile fields: {', '.join(missing)}. "
                       f"Update your profile at PUT /api/v1/auth/profile."
            )

        # Normalise gender → 0 (Male) / 1 (Female)
        gender_val: int
        if isinstance(gender_raw, (int, float)):
            gender_val = int(gender_raw)
        elif isinstance(gender_raw, str):
            g = gender_raw.strip().lower()
            if g in ("male", "m", "0"):
                gender_val = 0
            elif g in ("female", "f", "1"):
                gender_val = 1
            else:
                gender_val = 0  # default for Other/Unknown
        else:
            gender_val = 0

        # Auto-compute BMI
        if not bmi or bmi <= 0.0:
            if height_cm and height_cm > 0:
                bmi = round(weight_kg / ((height_cm / 100.0) ** 2), 2)
            else:
                bmi = 22.0

        return {
            "age":            float(age),
            "gender":         gender_val,
            "weight_kg":      float(weight_kg),
            "height_cm":      float(height_cm),
            "bmi":            float(bmi),
            "activity_level": activity_level,
        }

    @staticmethod
    def calculate_daily_nutrient_totals(db: Session, user_id: int, target_date: date) -> Dict[str, float]:
        """
        Aggregate all 14+ nutrient dimensions from today's food log entries.
        Returns a flat dict with ML-ready column names.
        """
        start_dt = datetime.combine(target_date, time.min)
        end_dt   = datetime.combine(target_date, time.max)

        r = db.query(
            func.coalesce(func.sum(FoodLog.calories), 0.0).label('calories'),
            func.coalesce(func.sum(FoodLog.protein), 0.0).label('protein'),
            func.coalesce(func.sum(FoodLog.carbohydrates), 0.0).label('carbs'),
            func.coalesce(func.sum(FoodLog.fat), 0.0).label('fat'),
            func.coalesce(func.sum(FoodLog.fiber), 0.0).label('fiber'),
            func.coalesce(func.sum(FoodLog.iron), 0.0).label('iron'),
            func.coalesce(func.sum(FoodLog.calcium), 0.0).label('calcium'),
            func.coalesce(func.sum(FoodLog.magnesium), 0.0).label('magnesium'),
            func.coalesce(func.sum(FoodLog.zinc), 0.0).label('zinc'),
            func.coalesce(func.sum(FoodLog.vitamin_c), 0.0).label('vitamin_c'),
            func.coalesce(func.sum(FoodLog.vitamin_d), 0.0).label('vitamin_d'),
            func.coalesce(func.sum(FoodLog.vitamin_b12), 0.0).label('vitamin_b12'),
            func.coalesce(func.sum(FoodLog.vitamin_b6), 0.0).label('vitamin_b6'),
            func.coalesce(func.sum(FoodLog.vitamin_a), 0.0).label('vitamin_a'),
        ).filter(
            FoodLog.user_id == user_id,
            FoodLog.logged_at >= start_dt,
            FoodLog.logged_at <= end_dt
        ).first()

        return {
            "calories_kcal":    float(r.calories),
            "protein_g":        float(r.protein),
            "carbs_g":          float(r.carbs),
            "fat_g":            float(r.fat),
            "fiber_g":          float(r.fiber),
            "iron_mg":          float(r.iron),
            "calcium_mg":       float(r.calcium),
            "magnesium_mg":     float(r.magnesium),
            "zinc_mg":          float(r.zinc),
            "vitamin_c_mg":     float(r.vitamin_c),
            "vitamin_d_mcg":    float(r.vitamin_d),
            "vitamin_b12_mcg":  float(r.vitamin_b12),
            "vitamin_b6_mg":    float(r.vitamin_b6),
            "vitamin_a_mcg":    float(r.vitamin_a),
        }

    @classmethod
    def execute_prediction(
        cls,
        db: Session,
        current_user: User,
        data: Optional[PredictInput] = None
    ) -> PredictResponse:
        """Full ML prediction pipeline — resolves profile, runs models, saves history, returns results."""

        # 1. Resolve demographics
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

        # 2. Aggregate food log (using current UTC date)
        today = datetime.utcnow().date()
        nutrient_totals = cls.calculate_daily_nutrient_totals(db, current_user.id, today)

        # 3. Run ML prediction
        try:
            predictions = run_prediction(
                age=profile["age"],
                gender=profile["gender"],
                weight_kg=profile["weight_kg"],
                height_cm=profile["height_cm"],
                bmi=profile["bmi"],
                activity_level=profile["activity_level"],
                nutrient_totals=nutrient_totals,
            )
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"ML models not ready. Run `python ml/train.py` first. ({e})"
            )

        # 4. Generate SHAP explanations per nutrient
        include_shap = data.include_shap if data is not None else True
        results: Dict[str, NutrientRisk] = {}

        for nutrient in NUTRIENT_TARGETS:
            pred = predictions.get(nutrient, {"risk_score": 0.0, "risk_label": "Unknown"})
            shap_items = None

            if include_shap:
                try:
                    raw_shap = run_explanation(
                        nutrient=nutrient,
                        age=profile["age"],
                        gender=profile["gender"],
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
                except Exception:
                    pass  # SHAP is best-effort, don't fail the request

            results[nutrient] = NutrientRisk(
                risk_score=pred["risk_score"],
                risk_label=pred["risk_label"],
                explanation=shap_items,
            )

        # 5. Persist to DB
        now = datetime.now(timezone.utc)
        history = PredictionHistory(
            user_id=current_user.id,
            iron_risk=results["iron"].risk_score,
            calcium_risk=results["calcium"].risk_score,
            vitamin_d_risk=results["vitamin_d"].risk_score,
            vitamin_b12_risk=results["vitamin_b12"].risk_score,
            zinc_risk=results["zinc"].risk_score,
            magnesium_risk=results["magnesium"].risk_score,
            vitamin_c_risk=results["vitamin_c"].risk_score,
            prediction_date=now,
        )
        db.add(history)
        db.commit()
        db.refresh(history)

        # 6. Generate recommendations
        risk_dict = {n: results[n].risk_score for n in NUTRIENT_TARGETS}
        recs = RecommendationService.generate_recommendations(db, current_user, risk_dict)

        return PredictResponse(
            user_id=current_user.id,
            prediction_date=now,
            results=results,
            iron_risk=results["iron"].risk_score,
            calcium_risk=results["calcium"].risk_score,
            vitamin_d_risk=results["vitamin_d"].risk_score,
            vitamin_b12_risk=results["vitamin_b12"].risk_score,
            zinc_risk=results["zinc"].risk_score,
            magnesium_risk=results["magnesium"].risk_score,
            vitamin_c_risk=results["vitamin_c"].risk_score,
            recommendations=recs,
        )
