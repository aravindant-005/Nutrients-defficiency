"""
app/ml/model.py
---------------
Bridge: wraps ml/predict.py for use inside FastAPI.
Adds risk-label classification for 7 deficiency targets.
"""
import sys
import os

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from ml.predict import predict_deficiencies
from typing import Dict, Optional


def _risk_label(score: Optional[float]) -> str:
    """Convert probability score to human-readable risk label."""
    if score is None:
        return "Unknown"
    if score >= 0.70:
        return "High"
    if score >= 0.45:
        return "Moderate"
    return "Low"


def run_prediction(
    age: float,
    gender: int,
    weight_kg: float,
    height_cm: float,
    bmi: float,
    activity_level: Optional[str] = None,
    nutrient_totals: Optional[Dict[str, float]] = None,
) -> Dict[str, Dict]:
    """
    Call the ML models and return risk scores + labels for all 7 deficiency targets.
    """
    raw_scores = predict_deficiencies(
        age=age,
        gender=gender,
        weight_kg=weight_kg,
        height_cm=height_cm,
        bmi=bmi,
        activity_level=activity_level,
        nutrient_totals=nutrient_totals,
    )

    return {
        nutrient: {
            "risk_score": score if score is not None else 0.0,
            "risk_label": _risk_label(score),
        }
        for nutrient, score in raw_scores.items()
    }
