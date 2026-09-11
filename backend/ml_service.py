import os
import joblib
import pandas as pd
import numpy as np
import shap
import logging
from backend.indb_service import indb_service

logger = logging.getLogger("ml_service")
MODELS_DIR = "models"
NUTRIENTS = ["iron", "calcium", "vitamin_d", "vitamin_b12", "zinc", "magnesium", "vitamin_c"]

RDA_MAP = {
    'iron': 18.0,
    'calcium': 1000.0,
    'vitamin_d': 15.0,
    'vitamin_b12': 2.4,
    'zinc': 11.0,
    'magnesium': 400.0,
    'vitamin_c': 90.0
}

TRAINED_FEATURE_NAMES = [
    'grpA_age', 'grpA_sex', 'grpA_race', 'grpB_weight', 'grpB_height', 'grpB_bmi',
    'grpC_calories', 'grpC_protein', 'grpC_carbohydrate', 'grpC_fat', 'grpC_fiber',
    'grpD_iron', 'grpD_calcium', 'grpD_vitamin_d', 'grpD_vitamin_b12', 'grpD_zinc', 'grpD_magnesium', 'grpD_vitamin_c',
    'grpE_iron_abs_diff', 'grpE_iron_mean', 'grpE_iron_cv',
    'grpE_calcium_abs_diff', 'grpE_calcium_mean', 'grpE_calcium_cv',
    'grpE_vitamin_d_abs_diff', 'grpE_vitamin_d_mean', 'grpE_vitamin_d_cv',
    'grpE_zinc_abs_diff', 'grpE_zinc_mean', 'grpE_zinc_cv',
    'grpE_magnesium_abs_diff', 'grpE_magnesium_mean', 'grpE_magnesium_cv',
    'grpE_vitamin_c_abs_diff', 'grpE_vitamin_c_mean', 'grpE_vitamin_c_cv',
    'grpE_calories_abs_diff', 'grpE_calories_mean', 'grpE_calories_cv',
    'grpF_iron_adequacy', 'grpF_calcium_adequacy', 'grpF_vitamin_d_adequacy', 'grpF_vitamin_b12_adequacy',
    'grpF_zinc_adequacy', 'grpF_magnesium_adequacy', 'grpF_vitamin_c_adequacy',
    'grpG_interaction_iron_vitC', 'grpG_interaction_calc_vitD', 'grpG_interaction_protein_iron', 'grpG_interaction_protein_zinc'
]

class MLService:
    def __init__(self):
        self.models = {}
        self.load_models()

    def load_models(self):
        for nut in NUTRIENTS:
            model_path = os.path.join(MODELS_DIR, f"best_model_{nut}.pkl")
            if os.path.exists(model_path):
                try:
                    self.models[nut] = joblib.load(model_path)
                    logger.info(f"Loaded ML model for {nut}")
                except Exception as e:
                    logger.error(f"Error loading model for {nut}: {e}")

    def construct_features(self, profile, daily_totals):
        age = float(profile.get("age", 28.0))
        sex = float(profile.get("gender", 1.0))
        race = float(profile.get("race", 3.0))
        weight = float(profile.get("weight_kg", 70.0))
        height = float(profile.get("height_cm", 175.0))
        bmi = float(profile.get("bmi", weight / ((height / 100.0) ** 2)))

        kcals = float(daily_totals.get("calories_kcal", 0.0))
        prot = float(daily_totals.get("protein_g", 0.0))
        carb = float(daily_totals.get("carbs_g", 0.0))
        fat = float(daily_totals.get("fat_g", 0.0))
        fiber = float(daily_totals.get("fiber_g", 0.0))

        iron = float(daily_totals.get("iron_mg", 0.0))
        calc = float(daily_totals.get("calcium_mg", 0.0))
        vitd = float(daily_totals.get("vitamin_d_mcg", 0.0))
        vitb12 = float(daily_totals.get("vitamin_b12_mcg", 0.0))
        zinc = float(daily_totals.get("zinc_mg", 0.0))
        mag = float(daily_totals.get("magnesium_mg", 0.0))
        vitc = float(daily_totals.get("vitamin_c_mg", 0.0))

        row = {
            'grpA_age': age,
            'grpA_sex': sex,
            'grpA_race': race,
            'grpB_weight': weight,
            'grpB_height': height,
            'grpB_bmi': bmi,
            'grpC_calories': kcals,
            'grpC_protein': prot,
            'grpC_carbohydrate': carb,
            'grpC_fat': fat,
            'grpC_fiber': fiber,
            'grpD_iron': iron,
            'grpD_calcium': calc,
            'grpD_vitamin_d': vitd,
            'grpD_vitamin_b12': vitb12,
            'grpD_zinc': zinc,
            'grpD_magnesium': mag,
            'grpD_vitamin_c': vitc,

            'grpE_iron_abs_diff': 0.0, 'grpE_iron_mean': iron, 'grpE_iron_cv': 0.0,
            'grpE_calcium_abs_diff': 0.0, 'grpE_calcium_mean': calc, 'grpE_calcium_cv': 0.0,
            'grpE_vitamin_d_abs_diff': 0.0, 'grpE_vitamin_d_mean': vitd, 'grpE_vitamin_d_cv': 0.0,
            'grpE_zinc_abs_diff': 0.0, 'grpE_zinc_mean': zinc, 'grpE_zinc_cv': 0.0,
            'grpE_magnesium_abs_diff': 0.0, 'grpE_magnesium_mean': mag, 'grpE_magnesium_cv': 0.0,
            'grpE_vitamin_c_abs_diff': 0.0, 'grpE_vitamin_c_mean': vitc, 'grpE_vitamin_c_cv': 0.0,
            'grpE_calories_abs_diff': 0.0, 'grpE_calories_mean': kcals, 'grpE_calories_cv': 0.0,

            'grpF_iron_adequacy': iron / RDA_MAP['iron'],
            'grpF_calcium_adequacy': calc / RDA_MAP['calcium'],
            'grpF_vitamin_d_adequacy': vitd / RDA_MAP['vitamin_d'],
            'grpF_vitamin_b12_adequacy': vitb12 / RDA_MAP['vitamin_b12'],
            'grpF_zinc_adequacy': zinc / RDA_MAP['zinc'],
            'grpF_magnesium_adequacy': mag / RDA_MAP['magnesium'],
            'grpF_vitamin_c_adequacy': vitc / RDA_MAP['vitamin_c'],

            'grpG_supplement_use': float(profile.get("supplement_use", 1.0)),
            'grpG_crp': float(profile.get("crp", 1.0)),
            'grpG_smoking_status': float(profile.get("smoking_status", 0.0)),
            'grpG_alcohol_use': float(profile.get("alcohol_use", 0.0)),
            'grpG_interaction_iron_vitC': iron * vitc,
            'grpG_interaction_calc_vitD': calc * vitd,
            'grpG_interaction_protein_iron': prot * iron,
            'grpG_interaction_protein_zinc': prot * zinc
        }

        fn_path = os.path.join(MODELS_DIR, "feature_names.json")
        if os.path.exists(fn_path):
            try:
                with open(fn_path) as f:
                    saved_cols = json.load(f)
                res_df = pd.DataFrame([row])
                for c in saved_cols:
                    if c not in res_df.columns:
                        res_df[c] = 0.0
                return res_df[saved_cols]
            except Exception:
                pass

        cols = [c for c in TRAINED_FEATURE_NAMES if c in row]
        return pd.DataFrame([row])[cols]

    def predict_risk_all(self, profile, daily_totals):
        total_calories = float(daily_totals.get("calories_kcal", 0.0))
        has_logged = total_calories > 0.0

        if not has_logged:
            return {
                "has_logged_data": False,
                "message": "No meals logged for today. Please search & log your food items first!",
                "predictions": []
            }

        features_df = self.construct_features(profile, daily_totals)
        diet_type = profile.get("diet_type", "Vegetarian")
        results = []

        for nut in NUTRIENTS:
            model = self.models.get(nut)
            risk_prob = 0.35
            
            if model is not None:
                try:
                    if hasattr(model, "predict_proba"):
                        risk_prob = float(model.predict_proba(features_df)[0][1])
                    else:
                        risk_prob = float(model.predict(features_df)[0])
                except Exception as e:
                    logger.error(f"Prediction failed for {nut}: {e}")

            if risk_prob < 0.40:
                risk_level = "Low Risk"
            elif risk_prob < 0.60:
                risk_level = "Moderate Risk"
            else:
                risk_level = "High Risk"

            top_factor = f"grpD_{nut}"
            explanation = f"Intake of {nut.replace('_', ' ').title()} is currently below standard dietary baseline."

            if model is not None:
                try:
                    classifier = getattr(model, 'named_steps', {}).get('classifier', model)
                    imputer = getattr(model, 'named_steps', {}).get('imputer', None)
                    scaler = getattr(model, 'named_steps', {}).get('scaler', None)

                    X_proc = features_df.copy()
                    if imputer:
                        X_proc = imputer.transform(X_proc)
                    if scaler:
                        X_proc = scaler.transform(X_proc)

                    active_cols = features_df.columns.tolist()
                    if imputer and hasattr(imputer, 'get_feature_names_out'):
                        active_cols = imputer.get_feature_names_out(features_df.columns).tolist()

                    X_proc_df = pd.DataFrame(X_proc, columns=active_cols)
                    explainer = shap.TreeExplainer(classifier) if "Forest" in type(classifier).__name__ or "Tree" in type(classifier).__name__ or "XGB" in type(classifier).__name__ else shap.LinearExplainer(classifier, X_proc_df)
                    shap_vals = explainer.shap_values(X_proc_df)

                    if isinstance(shap_vals, list):
                        shap_vals = shap_vals[1]

                    top_idx = int(np.argmax(shap_vals[0]))
                    top_factor = active_cols[top_idx]
                    explanation = f"Deficiency prediction driven by key feature '{top_factor}' (SHAP score: {shap_vals[0][top_idx]:.4f})."
                except Exception as e:
                    logger.debug(f"SHAP extraction simplified for {nut}: {e}")

            recommended = indb_service.get_top_foods_for_nutrient(nut, diet_type=diet_type, top_n=5)

            results.append({
                "nutrient": nut,
                "display_name": nut.replace("_", " ").title(),
                "risk_probability": round(risk_prob * 100, 1),
                "risk_level": risk_level,
                "top_factor": top_factor,
                "explanation": explanation,
                "recommended_foods": recommended,
                "current_intake": round(float(daily_totals.get(f"{nut}_mg", daily_totals.get(f"{nut}_mcg", daily_totals.get(f"{nut}", 0.0)))), 2),
                "rda_target": RDA_MAP.get(nut, 100.0)
            })

        return {
            "has_logged_data": True,
            "predictions": results
        }

ml_service = MLService()
