"""
ml/train.py
-----------
Trains Random Forest and XGBoost classifiers for each of 7 micronutrient deficiency targets
using synthetic NHANES-augmented training data.

Deficiency Targets (7):
  iron, calcium, vitamin_d, vitamin_b12, zinc, magnesium, vitamin_c

Feature Dimensions (14+5 = 19 total):
  Demographic  : age, gender, bmi, weight_kg, height_cm
  Nutrient log : calories_kcal, protein_g, carbs_g, fat_g, fiber_g,
                 iron_mg, calcium_mg, vitamin_d_mcg, vitamin_b12_mcg,
                 zinc_mg, magnesium_mg, vitamin_c_mg, vitamin_b6_mg, vitamin_a_mcg

Models Trained:
  1. Random Forest
  2. XGBoost

Selection: best ROC-AUC + 5-fold Cross Validation
Inference: ensemble average of RF + XGBoost when both models are available
Saved to : ml/models/{nutrient}_model.json  (XGBoost)
           ml/models/{nutrient}_model.pkl   (Random Forest)
           ml/models/feature_names.json
           ml/models/metrics.json
           ml/models/comparison_table.csv

Run:
    cd e:/nutrients/backend
    python ml/train.py
"""
import os
import sys
import json
import pickle
import warnings
import textwrap

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Scikit-learn imports ───────────────────────────────────────────────────────
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report
)
from sklearn.pipeline import Pipeline

import xgboost as xgb
from typing import Dict

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    print("⚠  LightGBM not installed — skipping LGBMClassifier")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR   = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# ── Feature / Target config ────────────────────────────────────────────────────
FEATURE_COLS = [
    "age", "gender", "bmi", "weight_kg", "height_cm",
    "calories_kcal", "protein_g", "carbs_g", "fat_g", "fiber_g",
    "iron_mg", "calcium_mg", "vitamin_d_mcg", "vitamin_b12_mcg",
    "zinc_mg", "magnesium_mg", "vitamin_c_mg", "vitamin_b6_mg", "vitamin_a_mcg",
]

# NHANES serum biomarker deficiency thresholds → binary label columns
TARGETS = {
    "iron":        "label_iron",
    "calcium":     "label_calcium",
    "vitamin_d":   "label_vitamin_d",
    "vitamin_b12": "label_vitamin_b12",
    "zinc":        "label_zinc",
    "magnesium":   "label_magnesium",
    "vitamin_c":   "label_vitamin_c",
}

RANDOM_STATE = 42
TEST_SIZE    = 0.20
CV_FOLDS     = 5

# ── Helpers ────────────────────────────────────────────────────────────────────

def evaluate(y_true, y_pred, y_prob):
    """Compute Accuracy, Precision, Recall, F1, ROC-AUC, and CV-AUC."""
    return {
        "accuracy":  round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall":    round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1":        round(f1_score(y_true, y_pred, zero_division=0), 4),
        "roc_auc":   round(roc_auc_score(y_true, y_prob), 4),
    }


def save_model(nutrient, model, model_type):
    """Persist a trained model to disk."""
    if model_type == "xgboost":
        path = os.path.join(MODELS_DIR, f"{nutrient}_model.json")
        model.save_model(path)
    else:
        path = os.path.join(MODELS_DIR, f"{nutrient}_model.pkl")
        with open(path, "wb") as f:
            pickle.dump(model, f)
    return path


def write_model_type(nutrient, model_type):
    """Persist the current model type for a nutrient."""
    with open(os.path.join(MODELS_DIR, f"{nutrient}_model_type.txt"), "w") as f:
        f.write(model_type)


def add_nutrient_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Augment NHANES demographic data with synthetic nutrient intake columns
    using realistic RDA-based distributions correlated with deficiency labels.
    """
    rng = np.random.default_rng(RANDOM_STATE)
    n = len(df)

    def _noisy(mean, std, low=0.0):
        return np.clip(rng.normal(mean, std, n), low, None)

    # ── Nutrient intake columns (simulated from dietary surveys) ──────────────
    # Iron: RDA ~17mg women, ~8mg men. Deficient individuals consume less.
    if "label_iron" in df.columns:
        iron_deficient = df["label_iron"].values
        df["iron_mg"] = np.where(
            iron_deficient,
            _noisy(6.0, 2.5, 0.5),    # deficient: low intake
            _noisy(14.0, 4.0, 1.0)    # adequate: near/above RDA
        )
    else:
        df["iron_mg"] = _noisy(10.0, 4.0, 0.5)

    # Calcium: RDA 1000mg
    if "label_calcium" in df.columns:
        cal_def = df["label_calcium"].values
        df["calcium_mg"] = np.where(cal_def, _noisy(450, 150, 50), _noisy(900, 200, 100))
    else:
        df["calcium_mg"] = _noisy(750, 200, 50)

    # Vitamin D: RDA 15 mcg
    if "label_vitamin_d" in df.columns:
        vd_def = df["label_vitamin_d"].values
        df["vitamin_d_mcg"] = np.where(vd_def, _noisy(2.5, 1.5, 0.0), _noisy(9.0, 4.0, 0.5))
    else:
        df["vitamin_d_mcg"] = _noisy(6.0, 3.5, 0.0)

    # Vitamin B12: RDA 2.4 mcg
    if "label_vitamin_b12" in df.columns:
        b12_def = df["label_vitamin_b12"].values
        df["vitamin_b12_mcg"] = np.where(b12_def, _noisy(0.8, 0.5, 0.0), _noisy(3.5, 1.5, 0.2))
    else:
        df["vitamin_b12_mcg"] = _noisy(2.5, 1.5, 0.0)

    # Zinc: RDA 11mg men, 8mg women
    if "label_zinc" in df.columns:
        zn_def = df["label_zinc"].values
        df["zinc_mg"] = np.where(zn_def, _noisy(4.0, 1.5, 0.5), _noisy(9.5, 2.5, 1.0))
    else:
        df["zinc_mg"] = _noisy(7.5, 2.5, 0.5)

    # Magnesium: RDA 400mg men, 310mg women
    if "label_magnesium" not in df.columns:
        # Derive magnesium label from low intake
        df["magnesium_mg"] = _noisy(250, 80, 30)
        df["label_magnesium"] = (df["magnesium_mg"] < 200).astype(int)
    else:
        mg_def = df["label_magnesium"].values
        df["magnesium_mg"] = np.where(mg_def, _noisy(150, 50, 20), _noisy(320, 80, 80))

    # Vitamin C: RDA 75-90mg
    if "label_vitamin_c" not in df.columns:
        df["vitamin_c_mg"] = _noisy(50, 30, 0.0)
        df["label_vitamin_c"] = (df["vitamin_c_mg"] < 40).astype(int)
    else:
        vc_def = df["label_vitamin_c"].values
        df["vitamin_c_mg"] = np.where(vc_def, _noisy(20, 15, 0.0), _noisy(80, 30, 10))

    # Macro / other nutrients — correlated loosely with overall diet quality
    df["calories_kcal"] = _noisy(1900, 400, 800)
    df["protein_g"]     = _noisy(65, 20, 20)
    df["carbs_g"]       = _noisy(220, 60, 50)
    df["fat_g"]         = _noisy(75, 25, 10)
    df["fiber_g"]       = _noisy(18, 7, 2)
    df["vitamin_b6_mg"] = _noisy(1.4, 0.5, 0.1)
    df["vitamin_a_mcg"] = _noisy(600, 250, 50)

    # Rename NHANES columns to match expected feature names
    rename_map = {}
    if "RIDAGEYR" in df.columns:  rename_map["RIDAGEYR"] = "age"
    if "RIAGENDR" in df.columns:  rename_map["RIAGENDR"] = "gender"
    if "BMXBMI"  in df.columns:   rename_map["BMXBMI"]   = "bmi"
    if "BMXWT"   in df.columns:   rename_map["BMXWT"]    = "weight_kg"
    if "BMXHT"   in df.columns:   rename_map["BMXHT"]    = "height_cm"
    # Legacy nhanes_master columns
    if "weight_kg" not in df.columns and "weight" in df.columns:
        rename_map["weight"] = "weight_kg"
    if "height_cm" not in df.columns and "height" in df.columns:
        rename_map["height"] = "height_cm"

    if rename_map:
        df = df.rename(columns=rename_map)

    # gender: NHANES uses 1=Male, 2=Female → convert to 0=Male, 1=Female
    if "gender" in df.columns:
        df["gender"] = df["gender"].apply(lambda x: 0 if x in (1, "1", "Male", "male") else 1)

    return df


def build_models(scale_pos_weight: float):
    """
    Return dict of (name, model_type_key, model_object) for the two production models.
    Only Random Forest and XGBoost are trained for the final deficiency risk system.
    """
    return {
        "random_forest": (
            "random_forest",
            RandomForestClassifier(
                n_estimators=200, max_depth=12, min_samples_leaf=5,
                class_weight="balanced", n_jobs=-1, random_state=RANDOM_STATE
            )
        ),
        "xgboost": (
            "xgboost",
            xgb.XGBClassifier(
                n_estimators=300, max_depth=6, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8,
                scale_pos_weight=scale_pos_weight,
                eval_metric="logloss",
                n_jobs=-1, random_state=RANDOM_STATE,
                verbosity=0,
            )
        ),
    }


# ── Main Training ──────────────────────────────────────────────────────────────
print("=" * 65)
print("  Food Log-Based Micronutrient Deficiency Detection System")
print("  ML Training Pipeline — 2 Models (Random Forest + XGBoost) × 7 Deficiency Targets")
print("=" * 65)

# Load NHANES master CSV
nhanes_path = os.path.join(PROC_DIR, "nhanes_master.csv")
if not os.path.exists(nhanes_path):
    print(f"\n⚠  nhanes_master.csv not found at {nhanes_path}")
    print("   Generating synthetic training dataset instead...")
    np.random.seed(RANDOM_STATE)
    n_samples = 12000
    master = pd.DataFrame({
        "age":    np.random.randint(18, 80, n_samples).astype(float),
        "gender": np.random.choice([0, 1], n_samples).astype(float),
        "bmi":    np.random.normal(25.5, 5.0, n_samples).clip(14, 50),
        "weight_kg": np.random.normal(70, 15, n_samples).clip(35, 150),
        "height_cm": np.random.normal(168, 10, n_samples).clip(140, 200),
    })
    # Derive labels
    master["label_iron"]        = (np.random.rand(n_samples) < 0.22).astype(int)
    master["label_calcium"]     = (np.random.rand(n_samples) < 0.35).astype(int)
    master["label_vitamin_d"]   = (np.random.rand(n_samples) < 0.41).astype(int)
    master["label_vitamin_b12"] = (np.random.rand(n_samples) < 0.19).astype(int)
    master["label_zinc"]        = (np.random.rand(n_samples) < 0.17).astype(int)
    # magnesium + vitamin_c labels will be derived in add_nutrient_features
else:
    print(f"\nLoading nhanes_master.csv ...")
    master = pd.read_csv(nhanes_path)

print(f"  Raw shape: {master.shape}")

# Augment with synthetic nutrient intake columns (food log features)
print("\nAugmenting with nutrient intake features ...")
master = add_nutrient_features(master)

# Determine available feature columns and targets
feature_cols = [c for c in FEATURE_COLS if c in master.columns]
print(f"  Features ({len(feature_cols)}): {feature_cols}")

# Save final feature names
with open(os.path.join(MODELS_DIR, "feature_names.json"), "w") as f:
    json.dump(feature_cols, f, indent=2)
print(f"  Saved feature_names.json")

all_metrics     = {}
comparison_rows = []

for nutrient, label_col in TARGETS.items():
    if label_col not in master.columns:
        print(f"\n⚠  {label_col} not found — skipping {nutrient}")
        continue

    df = master[feature_cols + [label_col]].dropna()
    if len(df) < 100:
        print(f"\n⚠  Too few samples for {nutrient} ({len(df)}) — skipping")
        continue

    X = df[feature_cols].astype(float).values
    y = df[label_col].astype(int).values

    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    spw   = max(n_neg / n_pos, 1.0) if n_pos > 0 else 1.0

    print(f"\n{'='*65}")
    print(f"  TARGET: {nutrient.upper().replace('_', ' ')}  |  samples={len(y)}  pos={n_pos}  neg={n_neg}")
    print(f"{'='*65}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    model_pool  = build_models(spw)
    best_name   = None
    best_type   = None
    best_model  = None
    best_auc    = -1.0
    model_metrics: Dict[str, dict] = {}
    trained_models: Dict[str, object] = {}

    for m_key, (m_type, clf) in model_pool.items():
        try:
            clf.fit(X_train, y_train)
            y_prob = clf.predict_proba(X_test)[:, 1]
            y_pred = clf.predict(X_test)
            m = evaluate(y_test, y_pred, y_prob)

            # 5-fold CV AUC (on train set, using stratified split)
            try:
                cv_scores = cross_val_score(
                    clf, X_train, y_train,
                    cv=CV_FOLDS, scoring="roc_auc", n_jobs=-1
                )
                m["cv_auc"] = round(float(cv_scores.mean()), 4)
                m["cv_std"] = round(float(cv_scores.std()), 4)
            except Exception:
                m["cv_auc"] = m["roc_auc"]
                m["cv_std"] = 0.0

            model_metrics[m_key] = m
            trained_models[m_type] = clf
            print(f"  {m_key:<22}  AUC={m['roc_auc']:.4f}  CV={m['cv_auc']:.4f}±{m['cv_std']:.4f}  F1={m['f1']:.4f}")

            # Select best by CV AUC (tie-break by roc_auc)
            score = m["cv_auc"]
            if score > best_auc:
                best_auc   = score
                best_name  = m_key
                best_type  = m_type
                best_model = clf

        except Exception as e:
            print(f"  {m_key:<22}  ERROR: {e}")

    if not trained_models:
        print(f"  ✗ All models failed for {nutrient}")
        continue

    # Save both Random Forest and XGBoost for ensemble inference
    for model_type, model_obj in trained_models.items():
        saved = save_model(nutrient, model_obj, model_type)
        print(f"  ✓ Saved {model_type} model → {os.path.basename(saved)}")

    ensemble_type = "ensemble" if len(trained_models) > 1 else best_type
    write_model_type(nutrient, ensemble_type)
    print(f"\n  ✓ Best model: {best_name.upper()}  →  ensemble stored as {ensemble_type}")

    # Classification report for the winner
    best_pred = best_model.predict(X_test)
    print(classification_report(y_test, best_pred, zero_division=0))

    all_metrics[nutrient] = {
        "winner":       best_name,
        "winner_type":  best_type,
        "models":       model_metrics,
    }

    for mk, mm in model_metrics.items():
        comparison_rows.append({
            "nutrient":    nutrient,
            "model":       mk,
            "accuracy":    mm["accuracy"],
            "precision":   mm["precision"],
            "recall":      mm["recall"],
            "f1":          mm["f1"],
            "roc_auc":     mm["roc_auc"],
            "cv_auc":      mm.get("cv_auc", 0),
            "cv_std":      mm.get("cv_std", 0),
            "winner":      "YES" if mk == best_name else "",
        })

# ── Save metrics ───────────────────────────────────────────────────────────────
metrics_path = os.path.join(MODELS_DIR, "metrics.json")
with open(metrics_path, "w") as f:
    json.dump(all_metrics, f, indent=2)
print(f"\nMetrics → {metrics_path}")

csv_path = os.path.join(MODELS_DIR, "comparison_table.csv")
pd.DataFrame(comparison_rows).to_csv(csv_path, index=False)
print(f"Comparison table → {csv_path}")

# ── Final Summary ──────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  FINAL SUMMARY — Best Models Selected")
print("=" * 65)
fmt = "  {:<14} {:<22} {:>8} {:>8} {:>8}"
print(fmt.format("Nutrient", "Best Model", "CV-AUC", "AUC", "F1"))
print("  " + "-" * 60)
for nut, data in all_metrics.items():
    w  = data["winner"]
    mm = data["models"].get(w, {})
    print(fmt.format(
        nut, w,
        f"{mm.get('cv_auc', 0):.4f}",
        f"{mm.get('roc_auc', 0):.4f}",
        f"{mm.get('f1', 0):.4f}"
    ))
print("=" * 65)
print("\n✓ Training complete. Models saved to ml/models/")
print("  Start the API: uvicorn app.main:app --reload")
