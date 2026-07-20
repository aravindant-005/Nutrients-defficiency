"""
ml/shap_explain.py
------------------
Generates SHAP feature-contribution values for any trained model
(XGBoost, Random Forest, Gradient Boosting, LightGBM) to explain
deficiency predictions.

Usage:
    from ml.shap_explain import explain_prediction

    contribs = explain_prediction(
        nutrient="iron",
        age=28, gender=1, weight_kg=55.0, height_cm=160.0, bmi=21.5,
        nutrient_totals={"iron_mg": 6.0, ...}
    )
    # -> [{"feature": "iron_mg", "value": 6.0, "contribution": -0.312}, ...]
"""
import os
import json
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import shap

from ml.predict import (
    load_model,
    load_preprocessor,
    get_feature_names_for_nutrient,
    get_raw_feature_names_for_nutrient,
    get_model_type,
)
from ml.predict import load_models, get_feature_names, get_model_type

# Lazy explainer cache
_explainer_cache: Dict[str, object] = {}


def _build_explainer(model, model_type: str):
    if model_type == "xgboost":
        return shap.TreeExplainer(model, feature_perturbation="auto")
    return shap.TreeExplainer(model, feature_perturbation="tree_path_dependent")


def _get_explainer(nutrient: str) -> object:
    """Load and cache SHAP explainers for the given nutrient's available models."""
    if nutrient not in _explainer_cache:
        model_type = get_model_type(nutrient)
        models = load_models(nutrient)

        if model_type == "ensemble":
            explainers = {
                name: _build_explainer(model, name)
                for name, model in models.items()
            }
        else:
            explainers = {
                model_type: _build_explainer(models[model_type], model_type)
            }

        _explainer_cache[nutrient] = explainers
    return _explainer_cache[nutrient]


def _extract_shap_array(shap_values):
    if isinstance(shap_values, list):
        return np.asarray(shap_values[1][0], dtype=float)
    if isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
        return shap_values[0, :, 1].astype(float)
    return np.asarray(shap_values[0], dtype=float)


def explain_prediction(
    nutrient: str,
    age: float,
    gender: int,
    weight_kg: float,
    height_cm: float,
    bmi: float,
    activity_level: Optional[str] = None,
    nutrient_totals: Optional[Dict[str, float]] = None,
) -> Optional[List[Dict]]:
    """
    Returns SHAP feature-contribution values sorted by absolute impact.

    Returns:
        [{"feature": "iron_mg", "value": 6.0, "contribution": -0.312}, ...]
        or None if the model is not yet trained.
    """
    try:
        feature_names = get_feature_names_for_nutrient(nutrient)
        raw_feature_names = get_raw_feature_names_for_nutrient(nutrient)
        preprocessor = load_preprocessor(nutrient)
        model_type    = get_model_type(nutrient)
        feature_names = get_feature_names()
        explainer     = _get_explainer(nutrient)
    except (FileNotFoundError, Exception):
        return None

    feature_map: Dict[str, float] = {
        "age":       age,
        "gender":    float(gender),
        "bmi":       bmi,
        "weight_kg": weight_kg,
        "height_cm": height_cm,
    }
    if nutrient_totals:
        feature_map.update(nutrient_totals)
    X_raw = pd.DataFrame([{f: feature_map.get(f, 0.0) for f in raw_feature_names}])
    X = preprocessor.transform(X_raw)

    X = np.array([[feature_map.get(f, 0.0) for f in feature_names]], dtype=float)

    try:
        if isinstance(explainer, dict):
            shap_arrs = []
            for expl in explainer.values():
                shap_values = expl.shap_values(X)
                shap_arrs.append(_extract_shap_array(shap_values))
            shap_arr = np.mean(np.stack(shap_arrs), axis=0)
        else:
            shap_values = explainer.shap_values(X)
            shap_arr = _extract_shap_array(shap_values)
    except Exception:
        return None

    contributions = [
        {
            "feature":      feature_names[i],
            "value":        round(float(X[0][i]), 4),
            "contribution": round(float(shap_arr[i]), 6),
        }
        for i in range(len(feature_names))
    ]
    contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
    return contributions


def explain_all(age, gender, weight_kg, height_cm, bmi, nutrient_totals=None):
    """Run SHAP for all 7 deficiency targets in one call."""
    targets = ["iron", "calcium", "vitamin_d", "vitamin_b12", "zinc", "magnesium", "vitamin_c"]
    return {
        t: explain_prediction(t, age, gender, weight_kg, height_cm, bmi,
                              nutrient_totals=nutrient_totals)
        for t in targets
    }
