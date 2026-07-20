"""
shap_explain.py
---------------
Generates SHAP feature-contribution values for any trained model
(XGBoost or Random Forest) to explain deficiency predictions.

Uses:
  - shap.TreeExplainer  for both XGBoost and Random Forest
  - Model type is auto-detected from {nutrient}_model_type.txt

Usage:
    from ml.shap_explain import explain_prediction

    contributions = explain_prediction(
        nutrient="iron",
        age=35, gender=1, race_ethnicity=3,
        weight_kg=68.0, height_cm=165.0, bmi=24.9
    )
    # -> [{"feature": "gender", "value": 1.0, "contribution": +0.312}, ...]
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

# ── Lazy explainer cache ───────────────────────────────────────────────────────
_explainer_cache: Dict[str, shap.TreeExplainer] = {}


def _get_explainer(nutrient: str) -> shap.TreeExplainer:
    """Load and cache a SHAP TreeExplainer for the given nutrient's best model."""
    if nutrient not in _explainer_cache:
        model      = load_model(nutrient)
        model_type = get_model_type(nutrient)

        if model_type == "xgboost":
            # XGBoost: use interventional perturbation for clean additive explanations
            explainer = shap.TreeExplainer(
                model,
                feature_perturbation="interventional",
            )
        elif model_type == "random_forest":
            # Random Forest: TreeExplainer works natively; use tree_path_dependent
            explainer = shap.TreeExplainer(
                model,
                feature_perturbation="tree_path_dependent",
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        _explainer_cache[nutrient] = explainer

    return _explainer_cache[nutrient]


def explain_prediction(
    nutrient: str,
    age: float,
    gender: int,
    race_ethnicity: int,
    weight_kg: float,
    height_cm: float,
    bmi: float,
    activity_level: Optional[str] = None,
    nutrient_totals: Optional[Dict[str, float]] = None,
) -> Optional[List[Dict]]:
    """
    Returns SHAP feature-contribution values explaining a deficiency prediction.

    Parameters:
        nutrient       : One of 'iron', 'calcium', 'vitamin_d', 'vitamin_b12', 'zinc'
        age, gender, race_ethnicity, weight_kg, height_cm, bmi : Patient attributes
        activity_level : Optional physical activity description
        nutrient_totals: Optional dictionary of daily nutrient intakes

    Returns:
        List of dicts sorted by absolute contribution (descending):
        [
            {"feature": "gender",   "value": 1.0,  "contribution": +0.312},
            {"feature": "bmi",      "value": 24.9, "contribution": -0.087},
            {"feature": "age",      "value": 35.0, "contribution": +0.041},
            ...
        ]
        Returns None if the model for this nutrient is not yet trained.
    """
    try:
        feature_names = get_feature_names_for_nutrient(nutrient)
        raw_feature_names = get_raw_feature_names_for_nutrient(nutrient)
        preprocessor = load_preprocessor(nutrient)
        model_type    = get_model_type(nutrient)
        explainer     = _get_explainer(nutrient)
    except FileNotFoundError:
        return None

    feature_map = {
        "age":            age,
        "gender":         gender,
        "race_ethnicity": race_ethnicity,
        "weight_kg":      weight_kg,
        "height_cm":      height_cm,
        "bmi":            bmi,
    }
    if nutrient_totals:
        feature_map.update(nutrient_totals)
    X_raw = pd.DataFrame([{f: feature_map.get(f, 0.0) for f in raw_feature_names}])
    X = preprocessor.transform(X_raw)

    # Compute raw SHAP values
    shap_values = explainer.shap_values(X)

    # Unify SHAP output across model types and SHAP library versions:
    #
    #   XGBoost          -> ndarray (n_samples, n_features)           → take [0]
    #   RF (old SHAP)    -> list of [neg_class, pos_class]            → take [1][0]
    #   RF (new SHAP)    -> ndarray (n_samples, n_features, n_classes) → take [0, :, 1]

    if isinstance(shap_values, list):
        # Old-style list format: [neg_class_arr, pos_class_arr]
        shap_arr = np.asarray(shap_values[1][0], dtype=float)
    elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
        # New-style 3D array: (n_samples, n_features, n_classes) — take positive class
        shap_arr = shap_values[0, :, 1].astype(float)
    else:
        # XGBoost 2D array: (n_samples, n_features)
        shap_arr = np.asarray(shap_values[0], dtype=float)

    # Build and sort contribution list
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


def explain_all(
    age: float,
    gender: int,
    race_ethnicity: int,
    weight_kg: float,
    height_cm: float,
    bmi: float,
) -> Dict[str, Optional[List[Dict]]]:
    """
    Run SHAP explanations for all 5 deficiency targets in one call.

    Returns:
        {
            "iron":        [...contributions...],
            "calcium":     [...contributions...],
            ...
        }
    """
    targets = ["iron", "calcium", "vitamin_d", "vitamin_b12", "zinc"]
    return {
        nutrient: explain_prediction(
            nutrient=nutrient,
            age=age, gender=gender, race_ethnicity=race_ethnicity,
            weight_kg=weight_kg, height_cm=height_cm, bmi=bmi,
        )
        for nutrient in targets
    }


# ── CLI test ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from ml.predict import get_loaded_model_types

    model_types = get_loaded_model_types()
    print("SHAP Explanation Test\n" + "=" * 50)

    for nutrient in ["iron", "calcium", "vitamin_d", "vitamin_b12", "zinc"]:
        mtype = model_types.get(nutrient, "not_trained")
        print(f"\n{nutrient.upper()} [{mtype}]")
        try:
            contribs = explain_prediction(
                nutrient=nutrient,
                age=32, gender=1, race_ethnicity=3,
                weight_kg=60.0, height_cm=162.0, bmi=22.9
            )
            if contribs:
                for c in contribs:
                    direction = "risk+" if c["contribution"] > 0 else "risk-"
                    print(f"  {c['feature']:<15} = {c['value']:6.2f}  SHAP: {c['contribution']:+.4f}  ({direction})")
        except Exception as e:
            print(f"  ERROR: {e}")
