"""
dashboard_service.py
--------------------
Builds the complete dashboard response:
  - Today's macro and micro nutrient totals
  - RDA % for each of the 7 tracked micronutrients
  - Latest deficiency risk scores from most recent prediction
  - 7-day nutrient intake trend (one data point per day)
  - Meal type breakdown for today
"""
from datetime import datetime, timedelta, time
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.deficiency import User, FoodLog, PredictionHistory
from app.schemas.dashboard import DashboardOut, NutrientSummary, WeeklyTrendPoint, MealTypeSummary
from app.services.recommendation_service import RecommendationService

# ICMR/WHO micronutrient RDA defaults (adult, 30-year-old male baseline)
DEFAULT_RDA = {
    "Iron":        (17.0, "mg"),
    "Calcium":     (1000.0, "mg"),
    "Vitamin D":   (15.0, "mcg"),
    "Vitamin B12": (2.4, "mcg"),
    "Zinc":        (11.0, "mg"),
    "Magnesium":   (400.0, "mg"),
    "Vitamin C":   (90.0, "mg"),
}


class DashboardService:

    @staticmethod
    def get_dashboard(db: Session, user: User) -> DashboardOut:
        today = datetime.utcnow().date()
        start_dt = datetime.combine(today, time.min)
        end_dt   = datetime.combine(today, time.max)

        # ── 1. Today's aggregate ─────────────────────────────────────────────
        agg = db.query(
            func.coalesce(func.sum(FoodLog.calories),      0.0).label("calories"),
            func.coalesce(func.sum(FoodLog.protein),       0.0).label("protein"),
            func.coalesce(func.sum(FoodLog.carbohydrates), 0.0).label("carbs"),
            func.coalesce(func.sum(FoodLog.fat),           0.0).label("fat"),
            func.coalesce(func.sum(FoodLog.fiber),         0.0).label("fiber"),
            func.coalesce(func.sum(FoodLog.iron),          0.0).label("iron"),
            func.coalesce(func.sum(FoodLog.calcium),       0.0).label("calcium"),
            func.coalesce(func.sum(FoodLog.vitamin_d),     0.0).label("vitamin_d"),
            func.coalesce(func.sum(FoodLog.vitamin_b12),   0.0).label("vitamin_b12"),
            func.coalesce(func.sum(FoodLog.zinc),          0.0).label("zinc"),
            func.coalesce(func.sum(FoodLog.magnesium),     0.0).label("magnesium"),
            func.coalesce(func.sum(FoodLog.vitamin_c),     0.0).label("vitamin_c"),
            func.count(FoodLog.id).label("count"),
        ).filter(
            FoodLog.user_id == user.id,
            FoodLog.logged_at >= start_dt,
            FoodLog.logged_at <= end_dt,
        ).first()

        total_calories = float(agg.calories)
        total_protein  = float(agg.protein)
        total_carbs    = float(agg.carbs)
        total_fat      = float(agg.fat)
        total_fiber    = float(agg.fiber)
        n_items        = int(agg.count)

        # ── 2. Micronutrient summary vs RDA ─────────────────────────────────
        rda_map = RecommendationService._get_rda(user)

        micro_actuals = {
            "iron":       float(agg.iron),
            "calcium":    float(agg.calcium),
            "vitamin_d":  float(agg.vitamin_d),
            "vitamin_b12":float(agg.vitamin_b12),
            "zinc":       float(agg.zinc),
            "magnesium":  float(agg.magnesium),
            "vitamin_c":  float(agg.vitamin_c),
        }
        label_map = {
            "iron": "Iron", "calcium": "Calcium", "vitamin_d": "Vitamin D",
            "vitamin_b12": "Vitamin B12", "zinc": "Zinc",
            "magnesium": "Magnesium", "vitamin_c": "Vitamin C",
        }

        nutrient_summary: List[NutrientSummary] = []
        for nut, actual in micro_actuals.items():
            rda_val  = rda_map[nut]["value"]
            rda_unit = rda_map[nut]["unit"]
            pct      = min(round((actual / rda_val) * 100, 1), 200.0) if rda_val > 0 else 0.0
            if pct >= 80:
                status = "Adequate"
            elif pct >= 50:
                status = "Low"
            else:
                status = "Deficient"

            nutrient_summary.append(NutrientSummary(
                nutrient=label_map[nut],
                current=round(actual, 2),
                target=rda_val,
                unit=rda_unit,
                percentage=pct,
                status=status,
            ))

        # ── 3. Latest deficiency risks ───────────────────────────────────────
        latest_pred = (
            db.query(PredictionHistory)
            .filter(PredictionHistory.user_id == user.id)
            .order_by(PredictionHistory.prediction_date.desc())
            .first()
        )
        last_pred_date = None
        if latest_pred:
            last_pred_date = latest_pred.prediction_date
            deficiency_risks = {
                "iron":        {"risk_score": latest_pred.iron_risk,       "risk_label": _label(latest_pred.iron_risk)},
                "calcium":     {"risk_score": latest_pred.calcium_risk,    "risk_label": _label(latest_pred.calcium_risk)},
                "vitamin_d":   {"risk_score": latest_pred.vitamin_d_risk,  "risk_label": _label(latest_pred.vitamin_d_risk)},
                "vitamin_b12": {"risk_score": latest_pred.vitamin_b12_risk,"risk_label": _label(latest_pred.vitamin_b12_risk)},
                "zinc":        {"risk_score": latest_pred.zinc_risk,       "risk_label": _label(latest_pred.zinc_risk)},
                "magnesium":   {"risk_score": latest_pred.magnesium_risk,  "risk_label": _label(latest_pred.magnesium_risk)},
                "vitamin_c":   {"risk_score": latest_pred.vitamin_c_risk,  "risk_label": _label(latest_pred.vitamin_c_risk)},
            }
        else:
            deficiency_risks = {n: {"risk_score": 0.0, "risk_label": "Unknown"}
                                for n in ["iron","calcium","vitamin_d","vitamin_b12","zinc","magnesium","vitamin_c"]}

        # ── 4. 7-day weekly trend ────────────────────────────────────────────
        weekly_trend: List[WeeklyTrendPoint] = []
        for offset in range(6, -1, -1):
            day_date = today - timedelta(days=offset)
            day_start = datetime.combine(day_date, time.min)
            day_end   = datetime.combine(day_date, time.max)

            day_row = db.query(
                func.coalesce(func.sum(FoodLog.calories),   0.0).label("calories"),
                func.coalesce(func.sum(FoodLog.iron),       0.0).label("iron"),
                func.coalesce(func.sum(FoodLog.calcium),    0.0).label("calcium"),
                func.coalesce(func.sum(FoodLog.vitamin_d),  0.0).label("vitamin_d"),
                func.coalesce(func.sum(FoodLog.vitamin_b12),0.0).label("vitamin_b12"),
                func.coalesce(func.sum(FoodLog.zinc),       0.0).label("zinc"),
                func.coalesce(func.sum(FoodLog.magnesium),  0.0).label("magnesium"),
                func.coalesce(func.sum(FoodLog.vitamin_c),  0.0).label("vitamin_c"),
            ).filter(
                FoodLog.user_id == user.id,
                FoodLog.logged_at >= day_start,
                FoodLog.logged_at <= day_end,
            ).first()

            weekly_trend.append(WeeklyTrendPoint(
                date=day_date.strftime("%Y-%m-%d"),
                calories=round(float(day_row.calories), 1),
                iron=round(float(day_row.iron), 2),
                calcium=round(float(day_row.calcium), 1),
                vitamin_d=round(float(day_row.vitamin_d), 2),
                vitamin_b12=round(float(day_row.vitamin_b12), 3),
                zinc=round(float(day_row.zinc), 2),
                magnesium=round(float(day_row.magnesium), 1),
                vitamin_c=round(float(day_row.vitamin_c), 1),
            ))

        # ── 5. Meal type breakdown ───────────────────────────────────────────
        meal_rows = db.query(
            FoodLog.meal_type,
            func.count(FoodLog.id).label("cnt"),
            func.coalesce(func.sum(FoodLog.calories), 0.0).label("cals"),
        ).filter(
            FoodLog.user_id == user.id,
            FoodLog.logged_at >= start_dt,
            FoodLog.logged_at <= end_dt,
        ).group_by(FoodLog.meal_type).all()

        meal_breakdown = [
            MealTypeSummary(meal_type=r.meal_type, count=r.cnt, calories=round(float(r.cals), 1))
            for r in meal_rows
        ]

        return DashboardOut(
            user_id=user.id,
            date=today.strftime("%Y-%m-%d"),
            total_calories=round(total_calories, 1),
            total_protein=round(total_protein, 1),
            total_carbohydrates=round(total_carbs, 1),
            total_fat=round(total_fat, 1),
            total_fiber=round(total_fiber, 1),
            nutrient_summary=nutrient_summary,
            deficiency_risks=deficiency_risks,
            weekly_trend=weekly_trend,
            meal_breakdown=meal_breakdown,
            total_food_items_today=n_items,
            last_prediction_date=last_pred_date,
        )


def _label(score: float) -> str:
    if score >= 0.70: return "High"
    if score >= 0.45: return "Moderate"
    return "Low"
