import os
import json
import logging
import pandas as pd
import numpy as np
import joblib
import shutil
import warnings

from sklearn.metrics import (
    roc_auc_score, average_precision_score, accuracy_score, balanced_accuracy_score,
    precision_score, recall_score, f1_score, matthews_corrcoef, brier_score_loss,
    confusion_matrix, classification_report
)

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def evaluate_model(model, X, y, threshold=0.5):
    try:
        y_prob = model.predict_proba(X)[:, 1]
    except AttributeError:
        y_prob = model.predict(X)
        
    y_pred = (y_prob >= threshold).astype(int)
    
    tn, fp, fn, tp = confusion_matrix(y, y_pred, labels=[0, 1]).ravel()
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    cls_report = classification_report(y, y_pred, target_names=['Normal', 'Deficient'], zero_division=0)
    
    metrics = {
        'Accuracy': round(accuracy_score(y, y_pred), 4),
        'Balanced_Accuracy': round(balanced_accuracy_score(y, y_pred), 4),
        'Precision': round(precision_score(y, y_pred, zero_division=0), 4),
        'Recall': round(recall_score(y, y_pred, zero_division=0), 4),
        'Specificity': round(specificity, 4),
        'F1_Score': round(f1_score(y, y_pred, zero_division=0), 4),
        'ROC_AUC': round(roc_auc_score(y, y_prob), 4),
        'PR_AUC': round(average_precision_score(y, y_prob), 4),
        'MCC': round(matthews_corrcoef(y, y_pred), 4),
        'Brier': round(brier_score_loss(y, y_prob), 4),
        'Confusion_Matrix': f"TN={tn}, FP={fp}, FN={fn}, TP={tp}",
        'Classification_Report': cls_report
    }
    return metrics, y_prob, y_pred

def compare_models():
    logging.info("Starting Model Comparison & Automated Model Selection (Module 07)...")
    
    train_file = "processed_data/train_engineered.csv"
    val_file = "processed_data/val_engineered.csv"
    
    if not os.path.exists(train_file) or not os.path.exists(val_file):
        logging.error("Engineered data files missing.")
        return
        
    train_df = pd.read_csv(train_file)
    val_df = pd.read_csv(val_file)
    
    targets = [c for c in train_df.columns if c.startswith('target_')]
    
    valid_features = [c for c in train_df.columns if not c.startswith('target_') and c != 'SEQN']
    if os.path.exists("models/feature_names.json"):
        with open("models/feature_names.json") as f:
            valid_features = json.load(f)
            
    models = ['LogisticRegression', 'RandomForest', 'ExtraTrees', 'XGBoost', 'CatBoost']
    
    comparison_records = []
    best_models_records = []
    
    os.makedirs("models", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    for target in targets:
        y_train = train_df[target]
        y_val = val_df[target]
        nutrient = target.replace('target_', '')
        
        logging.info(f"\n==================================================")
        logging.info(f" EVALUATING CANDIDATES FOR {nutrient.upper()}")
        logging.info(f"==================================================")
        
        nutrient_results = []
        for model_name in models:
            model_path = f"models/tuning/best_{model_name}_{nutrient}.pkl"
            if not os.path.exists(model_path):
                continue
                
            model = joblib.load(model_path)
            
            # Align features for target if model expects specific subset
            X_train = train_df[valid_features].select_dtypes(include=[np.number])
            X_val = val_df[valid_features].select_dtypes(include=[np.number])
            
            # If pipeline step has feature names out, subset accordingly
            try:
                train_acc = accuracy_score(y_train, model.predict(X_train))
                val_metrics, val_prob, val_pred = evaluate_model(model, X_val, y_val)
            except Exception as e:
                # Handle feature mismatch if target feature masking was applied
                try:
                    if hasattr(model, 'feature_names_in_'):
                        cols = model.feature_names_in_
                    else:
                        cols = [c for c in X_train.columns if not c.startswith('grpD_' + nutrient) and not c.startswith('grpE_' + nutrient)]
                    X_tr_sub = X_train[[c for c in cols if c in X_train.columns]]
                    X_va_sub = X_val[[c for c in cols if c in X_val.columns]]
                    train_acc = accuracy_score(y_train, model.predict(X_tr_sub))
                    val_metrics, val_prob, val_pred = evaluate_model(model, X_va_sub, y_val)
                except Exception as e2:
                    logging.warning(f"Evaluation failed for {model_name} on {nutrient}: {e2}")
                    continue
            
            overfit_gap = train_acc - val_metrics['Accuracy']
            
            record = {
                'Nutrient': nutrient.upper(),
                'Model': model_name,
                'Train_Accuracy': round(train_acc, 4),
                'Validation_Accuracy': val_metrics['Accuracy'],
                'Accuracy_Gap': round(overfit_gap, 4),
                'Precision': val_metrics['Precision'],
                'Recall_Sensitivity': val_metrics['Recall'],
                'Specificity': val_metrics['Specificity'],
                'F1_Score': val_metrics['F1_Score'],
                'ROC_AUC_Score': val_metrics['ROC_AUC'],
                'PR_AUC_Score': val_metrics['PR_AUC'],
                'MCC': val_metrics['MCC'],
                'Brier_Score': val_metrics['Brier'],
                'Confusion_Matrix': val_metrics['Confusion_Matrix']
            }
            comparison_records.append(record)
            nutrient_results.append(record)
            
            logging.info(f"Model: {model_name:20s} | ROC-AUC: {val_metrics['ROC_AUC']:.4f} | F1: {val_metrics['F1_Score']:.4f} | Rec: {val_metrics['Recall']:.4f} | Acc: {val_metrics['Accuracy']:.4f}")
        
        # AUTOMATICALLY SELECT BEST MODEL BASED ON HIGHEST ROC-AUC SCORE
        if nutrient_results:
            df_nut = pd.DataFrame(nutrient_results)
            best_row = df_nut.sort_values(by='ROC_AUC_Score', ascending=False).iloc[0]
            best_model_name = best_row['Model']
            best_auc = best_row['ROC_AUC_Score']
            
            best_models_records.append(best_row.to_dict())
            logging.info(f"\n---> AUTOMATIC BEST MODEL SELECTION FOR {nutrient.upper()}: {best_model_name} (Highest ROC-AUC Score: {best_auc:.4f})")
            
            src = f"models/tuning/best_{best_model_name}_{nutrient}.pkl"
            dst = f"models/best_model_{nutrient}.pkl"
            shutil.copy(src, dst)
            logging.info(f"Saved best model object to '{dst}'")

    # Save Comparison Reports to CSV
    comp_df = pd.DataFrame(comparison_records)
    comp_df.to_csv("reports/model_comparison.csv", index=False)
    logging.info("Saved all model comparison metrics to 'reports/model_comparison.csv'")
    
    best_df = pd.DataFrame(best_models_records)
    best_df.to_csv("reports/best_models.csv", index=False)
    logging.info("Saved automatically selected best models table to 'reports/best_models.csv'")
    
    logging.info("Model Comparison & Automated Selection Completed Successfully.")

if __name__ == "__main__":
    compare_models()
