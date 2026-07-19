"""
ml/predict.py
-------------
Loads the best-performing model for each deficiency target and runs inference.
Auto-detects whether the saved model is XGBoost or sklearn via {nutrient}_model_type.txt.

7 Deficiency Targets:
  iron, calcium, vitamin_d, vitamin_b12, zinc, magnesium, vitamin_c

14 Feature Dimensions:
  age, gender, bmi, weight_kg, height_cm,
  calories_kcal, protein_g, carbs_g, fat_g, fiber_g,
  iron_mg, calcium_mg, vitamin_d_mcg, vitamin_b12_mcg,
  zinc_mg, magnesium_mg, vitamin_c_mg, vitamin_b6_mg, vitamin_a_mcg

Usage:
    from ml.predict import predict_deficiencies

    result = predict_deficiencies(
        age=28, gender=1, weight_kg=55.0, height_cm=160.0, bmi=21.5,
        nutrient_totals={"iron_mg": 6.0, "calcium_mg": 400.0, ...}
    )
    # -> {"iron": 0.72, "calcium": 0.35, "vitamin_d": 0.91, ...}
"""
import os
import json
import pickle
from typing import Dict, Optional

import numpy as np
import xgboost as xgb

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

DEFICIENCY_TARGETS = [
    "iron", "calcium", "vitamin_d", "vitamin_b12",
    "zinc", "magnesium", "vitamin_c"
]

# Feature columns must match the order used during training
FEATURE_COLS = [
    "age", "gender", "bmi", "weight_kg", "height_cm",
    "calories_kcal", "protein_g", "carbs_g", "fat_g", "fiber_g",
    "iron_mg", "calcium_mg", "vitamin_d_mcg", "vitamin_b12_mcg",
    "zinc_mg", "magnesium_mg", "vitamin_c_mg", "vitamin_b6_mg", "vitamin_a_mcg",
]

# Lazy caches
_model_cache:       Dict[str, object] = {}
_model_type_cache:  Dict[str, str]    = {}
_feature_names:     Optional[list]    = None


def get_feature_names() -> list:
    """Load and cache the ordered feature name list saved during training."""
    global _feature_names
    if _feature_names is None:
        path = os.path.join(MODELS_DIR, "feature_names.json")
        if os.path.exists(path):
            with open(path) as f:
                _feature_names = json.load(f)
        else:
            # fall back to compile-time defaults
            _feature_names = FEATURE_COLS
    return _feature_names


def get_available_model_types(nutrient: str) -> list[str]:
    """Return available model types for the given nutrient based on saved files."""
    types = []
    if os.path.exists(os.path.join(MODELS_DIR, f"{nutrient}_model.json")):
        types.append("xgboost")
    if os.path.exists(os.path.join(MODELS_DIR, f"{nutrient}_model.pkl")):
        types.append("random_forest")
    return types


def get_model_type(nutrient: str) -> str:
    """Return the saved model type string for the given nutrient."""
    if nutrient not in _model_type_cache:
        type_path = os.path.join(MODELS_DIR, f"{nutrient}_model_type.txt")
        if os.path.exists(type_path):
            with open(type_path) as f:
                _model_type_cache[nutrient] = f.read().strip()
        else:
            available = get_available_model_types(nutrient)
            if len(available) == 2:
                _model_type_cache[nutrient] = "ensemble"
            elif len(available) == 1:
                _model_type_cache[nutrient] = available[0]
            else:
                raise FileNotFoundError(
                    f"No model found for '{nutrient}'. Run `python ml/train.py` first."
                )
    return _model_type_cache[nutrient]


def load_xgboost_model(nutrient: str) -> xgb.XGBClassifier:
    path = os.path.join(MODELS_DIR, f"{nutrient}_model.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"XGBoost model file not found: {path}")
    model = xgb.XGBClassifier()
    model.load_model(path)
    return model


def load_sklearn_model(nutrient: str) -> object:
    path = os.path.join(MODELS_DIR, f"{nutrient}_model.pkl")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Sklearn model file not found: {path}")
    with open(path, "rb") as f:
        return pickle.load(f)


def load_models(nutrient: str) -> Dict[str, object]:
    """Load all available models for a nutrient and cache them."""
    if nutrient not in _model_cache:
        models = {}
        if os.path.exists(os.path.join(MODELS_DIR, f"{nutrient}_model.json")):
            models["xgboost"] = load_xgboost_model(nutrient)
        if os.path.exists(os.path.join(MODELS_DIR, f"{nutrient}_model.pkl")):
            models["random_forest"] = load_sklearn_model(nutrient)
        if not models:
            raise FileNotFoundError(
                f"No model found for '{nutrient}'. Run `python ml/train.py` first."
            )
        _model_cache[nutrient] = models
    return _model_cache[nutrient]


def load_model(nutrient: str, model_type: Optional[str] = None) -> object:
    """Load and cache a single model for the given nutrient."""
    if model_type is None:
        model_type = get_model_type(nutrient)

    if model_type == "xgboost":
        return load_xgboost_model(nutrient)
    if model_type == "random_forest":
        return load_sklearn_model(nutrient)
    if model_type == "ensemble":
        raise ValueError("Use load_models() to access ensemble models directly.")

    raise ValueError(f"Unsupported model type: {model_type}")


def predict_deficiencies(
    age: float,
    gender: int,
    weight_kg: float,
    height_cm: float,
    bmi: float,
    activity_level: Optional[str] = None,
    nutrient_totals: Optional[Dict[str, float]] = None,
) -> Dict[str, Optional[float]]:
    """
    Run deficiency risk predictions for all 7 targets.

    Returns:
        dict mapping nutrient name -> risk probability (0.0 – 1.0)
        Value is None if that model is not yet trained.
    """
    feature_names = get_feature_names()

    feature_map: Dict[str, float] = {
        "age":        age,
        "gender":     float(gender),
        "bmi":        bmi,
        "weight_kg":  weight_kg,
        "height_cm":  height_cm,
    }

    if nutrient_totals:
        feature_map.update(nutrient_totals)

    X = np.array([[feature_map.get(f, 0.0) for f in feature_names]], dtype=float)

    results: Dict[str, Optional[float]] = {}
    for nutrient in DEFICIENCY_TARGETS:
        try:
            models = load_models(nutrient)
            probabilities = []
            for model in models.values():
                probabilities.append(float(model.predict_proba(X)[0][1]))
            if not probabilities:
                raise FileNotFoundError()
            prob = round(float(sum(probabilities) / len(probabilities)), 4)
            results[nutrient] = prob
        except FileNotFoundError:
            results[nutrient] = None

    return results


def get_loaded_model_types() -> Dict[str, str]:
    """Return {nutrient: model_type} for all trained targets."""
    info = {}
    for n in DEFICIENCY_TARGETS:
        try:
            info[n] = get_model_type(n)
        except FileNotFoundError:
            info[n] = "not_trained"
    return info


# ── CLI smoke test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Model types:")
    for n, t in get_loaded_model_types().items():
        print(f"  {n:<14} -> {t}")

    print("\nSample prediction (Female, 28, BMI 21.5):")
    sample = predict_deficiencies(
        age=28, gender=1, weight_kg=55.0, height_cm=160.0, bmi=21.5,
        nutrient_totals={
            "iron_mg": 6.0, "calcium_mg": 400.0,
            "vitamin_d_mcg": 2.0, "vitamin_b12_mcg": 1.1,
            "zinc_mg": 4.0, "magnesium_mg": 150.0, "vitamin_c_mg": 30.0,
        }
    )
    for k, v in sample.items():
        tag = "!! HIGH" if v and v > 0.70 else ("~ MOD" if v and v > 0.45 else "OK")
        val_str = f"{v:.4f}" if v is not None else "N/A"
        print(f"  {k:<14}: {val_str}  {tag}")
