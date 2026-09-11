"""
ml/train.py
-----------
Trains Random Forest and XGBoost classifiers for each of 7 micronutrient deficiency targets
using real engineered NHANES dataset (processed_data/train_engineered.csv and val_engineered.csv).

Deficiency Targets (7):
  iron, calcium, vitamin_d, vitamin_b12, zinc, magnesium, vitamin_c

Calculates and displays Training Accuracy and Testing (Validation) Accuracy for Random Forest and XGBoost
to diagnose Overfitting vs Underfitting. Automatically selects the best model based on ROC-AUC score.
"""
import os
import sys
import json
import pickle
import logging
import warnings

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, classification_report
)
import joblib
import xgboost as xgb

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

TARGET_MAP = {
    "iron": "target_iron",
    "calcium": "target_calcium",
    "vitamin_d": "target_vitamin_d",
    "vitamin_b12": "target_vitamin_b12",
    "zinc": "target_zinc",
    "magnesium": "target_magnesium",
    "vitamin_c": "target_vitamin_c",
}

RANDOM_STATE = 42

def train_backend_models():
    logging.info("Starting Backend Model Training on Real Engineered NHANES Dataset...")
    
    # Locate processed data files
    train_path = os.path.join(os.path.dirname(BASE_DIR), "processed_data", "train_engineered.csv")
    val_path   = os.path.join(os.path.dirname(BASE_DIR), "processed_data", "val_engineered.csv")
    
    if not os.path.exists(train_path) or not os.path.exists(val_path):
        train_path = "processed_data/train_engineered.csv"
        val_path   = "processed_data/val_engineered.csv"
        
    if not os.path.exists(train_path) or not os.path.exists(val_path):
        logging.error(f"Cannot find engineered datasets at {train_path} and {val_path}. Run Modules 01-04 first.")
        return

    train_df = pd.read_csv(train_path)
    val_df   = pd.read_csv(val_path)
    
    features = [c for c in train_df.columns if not c.startswith('target_') and c != 'SEQN']
    X_train_raw = train_df[features].select_dtypes(include=[np.number])
    X_val_raw   = val_df[features].select_dtypes(include=[np.number])
    
    valid_cols = X_train_raw.columns[X_train_raw.notna().any()].tolist()
    X_train = X_train_raw[valid_cols]
    X_val   = X_val_raw[valid_cols]
    
    # Save feature names for inference
    with open(os.path.join(MODELS_DIR, "feature_names.json"), "w") as f:
        json.dump(valid_cols, f, indent=2)
        
    comparison_rows = []
    best_summary = {}

    for nut, target_col in TARGET_MAP.items():
        if target_col not in train_df.columns:
            continue
            
        y_train = train_df[target_col].values
        y_val   = val_df[target_col].values
        
        n_pos = int(y_train.sum())
        n_neg = len(y_train) - n_pos
        scale_pos_weight = max(1.0, n_neg / max(1, n_pos))
        
        logging.info(f"\n=================================================================")
        logging.info(f" TRAINING MODELS FOR {nut.upper()} (Prevalence: {n_pos/len(y_train):.2%})")
        logging.info(f"=================================================================")
        
        # 1. Random Forest Classifier
        rf_pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(
                n_estimators=150, max_depth=8, min_samples_leaf=3,
                class_weight='balanced', random_state=RANDOM_STATE, n_jobs=-1
            ))
        ])
        
        # 2. XGBoost Classifier
        xgb_pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler()),
            ('classifier', xgb.XGBClassifier(
                n_estimators=150, max_depth=5, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, scale_pos_weight=scale_pos_weight,
                eval_metric='logloss', random_state=RANDOM_STATE, n_jobs=-1
            ))
        ])
        
        candidates = {
            "random_forest": rf_pipeline,
            "xgboost": xgb_pipeline
        }
        
        best_auc = -1.0
        best_model_name = None
        best_pipeline = None
        
        for m_name, pipeline in candidates.items():
            pipeline.fit(X_train, y_train)
            
            train_pred = pipeline.predict(X_train)
            val_pred   = pipeline.predict(X_val)
            val_prob   = pipeline.predict_proba(X_val)[:, 1]
            
            train_acc = accuracy_score(y_train, train_pred)
            val_acc   = accuracy_score(y_val, val_pred)
            acc_gap   = train_acc - val_acc
            
            prec  = precision_score(y_val, val_pred, zero_division=0)
            rec   = recall_score(y_val, val_pred, zero_division=0)
            f1    = f1_score(y_val, val_pred, zero_division=0)
            auc   = roc_auc_score(y_val, val_prob)
            
            tn, fp, fn, tp = confusion_matrix(y_val, val_pred, labels=[0, 1]).ravel()
            
            fit_status = "Well-Fitted"
            if train_acc > 0.88 and acc_gap > 0.10:
                fit_status = "Overfitting Detected"
            elif train_acc < 0.60 and val_acc < 0.60:
                fit_status = "Underfitting Detected"
                
            logging.info(f"[{m_name.upper():15s} - {nut.upper()}]")
            logging.info(f"   -> Training Accuracy  : {train_acc:.4f} ({train_acc*100:.2f}%)")
            logging.info(f"   -> Testing Accuracy   : {val_acc:.4f} ({val_acc*100:.2f}%)")
            logging.info(f"   -> Accuracy Gap       : {acc_gap:+.4f} ({fit_status})")
            logging.info(f"   -> Precision: {prec:.4f} | Recall: {rec:.4f} | F1: {f1:.4f} | ROC-AUC: {auc:.4f}")
            logging.info(f"   -> Confusion Matrix   : TN={tn}, FP={fp}, FN={fn}, TP={tp}")
            
            comparison_rows.append({
                "nutrient": nut,
                "model": m_name,
                "train_accuracy": round(train_acc, 4),
                "test_accuracy": round(val_acc, 4),
                "accuracy_gap": round(acc_gap, 4),
                "fit_status": fit_status,
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(auc, 4),
                "confusion_matrix": f"TN={tn}, FP={fp}, FN={fn}, TP={tp}"
            })
            
            # Save individual candidate model
            model_file = os.path.join(MODELS_DIR, f"{nut}_{m_name}.pkl")
            joblib.dump(pipeline, model_file)
            
            if auc > best_auc:
                best_auc = auc
                best_model_name = m_name
                best_pipeline = pipeline

        # Save winner model for nutrient
        winner_path = os.path.join(MODELS_DIR, f"{nut}_model.pkl")
        joblib.dump(best_pipeline, winner_path)
        
        # Also copy to root models/ directory for root scripts
        root_models_dir = os.path.join(os.path.dirname(BASE_DIR), "models")
        os.makedirs(root_models_dir, exist_ok=True)
        joblib.dump(best_pipeline, os.path.join(root_models_dir, f"best_model_{nut}.pkl"))
        
        with open(os.path.join(MODELS_DIR, f"{nut}_model_type.txt"), "w") as f:
            f.write(best_model_name)
            
        logging.info(f"---> SELECTED BEST MODEL FOR {nut.upper()}: {best_model_name} (ROC-AUC = {best_auc:.4f})")
        best_summary[nut] = {"best_model": best_model_name, "roc_auc": round(best_auc, 4)}

    # Save metrics and comparison table CSV
    comp_df = pd.DataFrame(comparison_rows)
    comp_df.to_csv(os.path.join(MODELS_DIR, "comparison_table.csv"), index=False)
    
    reports_dir = os.path.join(os.path.dirname(BASE_DIR), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    comp_df.to_csv(os.path.join(reports_dir, "model_comparison.csv"), index=False)
    
    with open(os.path.join(MODELS_DIR, "metrics.json"), "w") as f:
        json.dump(best_summary, f, indent=2)
        
    logging.info("\nBackend Model Training Completed Successfully. All models saved.")

if __name__ == "__main__":
    train_backend_models()
