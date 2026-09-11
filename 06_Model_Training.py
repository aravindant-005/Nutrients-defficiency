import os
import json
import logging
import pandas as pd
import numpy as np
import joblib
import warnings

from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, roc_auc_score
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

import xgboost as xgb
from catboost import CatBoostClassifier

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_candidate_models():
    models = {
        'LogisticRegression': {
            'model': LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42),
            'params': {'classifier__C': [0.01, 0.1, 1.0, 10.0]},
            'needs_scaling': True
        },
        'RandomForest': {
            'model': RandomForestClassifier(class_weight='balanced', random_state=42),
            'params': {
                'classifier__n_estimators': [100, 200],
                'classifier__max_depth': [4, 6, 8, 12],
                'classifier__min_samples_leaf': [2, 5, 10]
            },
            'needs_scaling': False
        },
        'ExtraTrees': {
            'model': ExtraTreesClassifier(class_weight='balanced', random_state=42),
            'params': {
                'classifier__n_estimators': [100, 150],
                'classifier__max_depth': [4, 6, 8],
                'classifier__min_samples_leaf': [2, 5]
            },
            'needs_scaling': False
        },
        'XGBoost': {
            'model': xgb.XGBClassifier(eval_metric='logloss', random_state=42, scale_pos_weight=1.0),
            'params': {
                'classifier__n_estimators': [100, 200],
                'classifier__max_depth': [3, 5, 7],
                'classifier__learning_rate': [0.01, 0.05, 0.1],
                'classifier__subsample': [0.7, 0.9]
            },
            'needs_scaling': False
        },
        'CatBoost': {
            'model': CatBoostClassifier(random_state=42, verbose=0, auto_class_weights='Balanced'),
            'params': {'classifier__iterations': [100, 200], 'classifier__depth': [4, 6]},
            'needs_scaling': False
        }
    }
    return models

def get_target_masked_features(features, target_name):
    """
    Mask out any feature that directly leaks or overlaps with the target definition.
    """
    masked = list(features)
    nut = target_name.replace('target_', '').lower()
    
    if nut == 'vitamin_c':
        # Remove Vitamin C intake features when predicting Vitamin C target
        leaky_terms = ['grpD_vitamin_c', 'grpE_vitamin_c', 'grpF_vitamin_c', 'grpG_interaction_iron_vitC']
        masked = [f for f in masked if not any(term in f for term in leaky_terms)]
    elif nut == 'iron':
        leaky_terms = ['LBXFER', 'LBDFERSI']
        masked = [f for f in masked if not any(term in f for term in leaky_terms)]
    elif nut == 'calcium':
        leaky_terms = ['LBXSCA', 'LBDSCASI']
        masked = [f for f in masked if not any(term in f for term in leaky_terms)]
    elif nut == 'vitamin_d':
        leaky_terms = ['LBXVIDMS', 'LBDVIDLC']
        masked = [f for f in masked if not any(term in f for term in leaky_terms)]
        
    return masked

def train_models():
    logging.info("Starting Model Training & Overfitting Diagnostics (Module 06 - Research Grade)...")
    
    train_file = "processed_data/train_engineered.csv"
    val_file = "processed_data/val_engineered.csv"
    
    if not os.path.exists(train_file) or not os.path.exists(val_file):
        logging.error("Engineered data files not found in 'processed_data/'")
        return
        
    train_df = pd.read_csv(train_file)
    val_df = pd.read_csv(val_file)
    
    targets = [c for c in train_df.columns if c.startswith('target_')]
    all_features = [c for c in train_df.columns if not c.startswith('target_') and c != 'SEQN']
    
    X_train_raw = train_df[all_features].select_dtypes(include=[np.number])
    valid_cols = X_train_raw.columns[X_train_raw.notna().any()].tolist()
    
    os.makedirs("models", exist_ok=True)
    with open("models/feature_names.json", "w") as f:
        json.dump(valid_cols, f, indent=2)
        
    models_config = get_candidate_models()
    os.makedirs("models/tuning", exist_ok=True)
    cv_results_list = []
    
    cv_strategy = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    
    for target in targets:
        y_train = train_df[target]
        y_val = val_df[target]
        nutrient = target.replace('target_', '').upper()
        
        target_features = get_target_masked_features(valid_cols, target)
        X_train = train_df[target_features]
        X_val = val_df[target_features]
        
        pos_pct = y_train.mean() * 100
        logging.info(f"\n==================================================")
        logging.info(f" TRAINING CANDIDATE MODELS FOR {nutrient} (Prevalence: {pos_pct:.2f}% Deficient)")
        logging.info(f" Target Features Count: {len(target_features)} / {len(valid_cols)}")
        logging.info(f"==================================================")
        
        for model_name, config in models_config.items():
            if model_name == 'XGBoost':
                neg_count = (y_train == 0).sum()
                pos_count = (y_train == 1).sum()
                scale_weight = neg_count / max(1, pos_count)
                config['model'].set_params(scale_pos_weight=scale_weight)
                
            steps = [('imputer', SimpleImputer(strategy='median'))]
            if config['needs_scaling']:
                steps.append(('scaler', StandardScaler()))
                
            steps.append(('classifier', config['model']))
            pipeline = ImbPipeline(steps)
            
            search = RandomizedSearchCV(
                pipeline, 
                param_distributions=config['params'], 
                n_iter=3, 
                scoring='roc_auc', 
                cv=cv_strategy, 
                random_state=42,
                error_score=0.5,
                n_jobs=1
            )
            
            try:
                search.fit(X_train, y_train)
                best_pipeline = search.best_estimator_
                
                train_pred = best_pipeline.predict(X_train)
                val_pred = best_pipeline.predict(X_val)
                
                train_acc = accuracy_score(y_train, train_pred)
                val_acc = accuracy_score(y_val, val_pred)
                acc_gap = train_acc - val_acc
                
                try:
                    val_prob = best_pipeline.predict_proba(X_val)[:, 1]
                    val_auc = roc_auc_score(y_val, val_prob)
                except:
                    val_auc = roc_auc_score(y_val, val_pred)
                    
                fit_status = "Well-Fitted"
                if train_acc > 0.85 and acc_gap > 0.10:
                    fit_status = "OVERFITTING DETECTED (High Train Acc, lower Val Acc)"
                elif train_acc < 0.60 and val_acc < 0.60:
                    fit_status = "UNDERFITTING DETECTED (Low Train & Val Acc)"
                    
                # Highlight Random Forest and XGBoost diagnostics explicitly
                if model_name in ['RandomForest', 'XGBoost']:
                    logging.info(f"*** DIAGNOSTIC CHECK: [{model_name} - {nutrient}] ***")
                    logging.info(f"    -> Training Accuracy  : {train_acc:.4f} ({train_acc*100:.2f}%)")
                    logging.info(f"    -> Validation Accuracy: {val_acc:.4f} ({val_acc*100:.2f}%)")
                    logging.info(f"    -> Accuracy Gap       : {acc_gap:+.4f}")
                    logging.info(f"    -> Validation ROC-AUC : {val_auc:.4f}")
                    logging.info(f"    -> Diagnostic Result  : {fit_status}")
                else:
                    logging.info(f"[{model_name:20s} - {nutrient:10s}] Best CV ROC-AUC: {search.best_score_:.4f} | Train Acc: {train_acc:.4f} | Val Acc: {val_acc:.4f} | Gap: {acc_gap:+.4f}")
                
                model_path = f"models/tuning/best_{model_name}_{target.replace('target_', '')}.pkl"
                joblib.dump(best_pipeline, model_path)
                
                cv_results_list.append({
                    'Nutrient': target.replace('target_', ''),
                    'Model': model_name,
                    'Train_Accuracy': round(train_acc, 4),
                    'Validation_Accuracy': round(val_acc, 4),
                    'Accuracy_Gap': round(acc_gap, 4),
                    'Validation_ROC_AUC': round(val_auc, 4),
                    'Fit_Diagnostic': fit_status,
                    'Best_Params': str(search.best_params_)
                })
            except Exception as e:
                logging.error(f"Training failed for {model_name} on {nutrient}: {e}")
                
    os.makedirs("reports", exist_ok=True)
    results_df = pd.DataFrame(cv_results_list)
    results_df.to_csv("reports/cross_validation_results.csv", index=False)
    logging.info("\nSaved model training & overfitting diagnostics report to 'reports/cross_validation_results.csv'")
    logging.info("Model Training Completed Successfully.")

if __name__ == "__main__":
    train_models()
