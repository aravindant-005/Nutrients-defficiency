import os
import pandas as pd
import numpy as np
import logging
import joblib

from sklearn.metrics import (
    roc_auc_score, average_precision_score, accuracy_score, balanced_accuracy_score,
    precision_score, recall_score, f1_score, matthews_corrcoef, brier_score_loss,
    confusion_matrix, classification_report
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def compute_bootstrapped_ci(y_true, y_prob, y_pred, n_bootstraps=1000, seed=42):
    np.random.seed(seed)
    n_samples = len(y_true)
    auc_list = []
    f1_list = []
    rec_list = []
    
    for _ in range(n_bootstraps):
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        if len(np.unique(y_true[indices])) < 2:
            continue
        auc = roc_auc_score(y_true[indices], y_prob[indices])
        f1 = f1_score(y_true[indices], y_pred[indices], zero_division=0)
        rec = recall_score(y_true[indices], y_pred[indices], zero_division=0)
        auc_list.append(auc)
        f1_list.append(f1)
        rec_list.append(rec)
        
    auc_ci = (np.percentile(auc_list, 2.5), np.percentile(auc_list, 97.5)) if auc_list else (0.5, 0.5)
    f1_ci = (np.percentile(f1_list, 2.5), np.percentile(f1_list, 97.5)) if f1_list else (0.0, 0.0)
    rec_ci = (np.percentile(rec_list, 2.5), np.percentile(rec_list, 97.5)) if rec_list else (0.0, 0.0)
    return auc_ci, f1_ci, rec_ci

def evaluate_final():
    logging.info("Starting Final Evaluation & Bootstrapped Confidence Intervals (Module 11)...")
    
    test_file = "processed_data/test_engineered.csv"
    if not os.path.exists(test_file):
        logging.error(f"Test data file missing: {test_file}")
        return
        
    test_df = pd.read_csv(test_file)
    
    import json
    targets = [c for c in test_df.columns if c.startswith('target_')]
    features = [c for c in test_df.columns if not c.startswith('target_') and c != 'SEQN']
    if os.path.exists("models/feature_names.json"):
        with open("models/feature_names.json") as f:
            features = json.load(f)
            
    X_test = test_df[features].select_dtypes(include=[np.number])
    
    final_results = []
    
    for target in targets:
        y_test = test_df[target].values
        nutrient = target.replace('target_', '')
        
        model_path = f"models/best_model_{nutrient}.pkl"
        if not os.path.exists(model_path):
            logging.warning(f"No best model found for {nutrient}")
            continue
            
        best_model = joblib.load(model_path)
        
        target_features = features
        if hasattr(best_model, 'feature_names_in_'):
            target_features = [c for c in best_model.feature_names_in_ if c in X_test.columns]
        elif hasattr(best_model.named_steps.get('classifier'), 'feature_names_in_'):
            target_features = [c for c in best_model.named_steps['classifier'].feature_names_in_ if c in X_test.columns]
            
        X_sub = X_test[target_features]
        
        try:
            y_prob = best_model.predict_proba(X_sub)[:, 1]
        except AttributeError:
            y_prob = best_model.predict(X_sub)
            
        y_pred = (y_prob >= 0.5).astype(int)
        
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        
        auc = roc_auc_score(y_test, y_prob)
        pr_auc = average_precision_score(y_test, y_prob)
        acc = accuracy_score(y_test, y_pred)
        bal_acc = balanced_accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        mcc = matthews_corrcoef(y_test, y_pred)
        brier = brier_score_loss(y_test, y_prob)
        
        cls_report = classification_report(y_test, y_pred, target_names=['Normal', 'Deficient'], zero_division=0)
        
        # 1000 Bootstrapped 95% Confidence Intervals
        auc_ci, f1_ci, rec_ci = compute_bootstrapped_ci(y_test, y_prob, y_pred, n_bootstraps=1000)
        
        auc_ci_str = f"[{auc_ci[0]:.4f} - {auc_ci[1]:.4f}]"
        f1_ci_str = f"[{f1_ci[0]:.4f} - {f1_ci[1]:.4f}]"
        
        logging.info(f"\n==========================================")
        logging.info(f" FINAL TEST EVALUATION: {nutrient.upper()}")
        logging.info(f"==========================================")
        logging.info(f"Test ROC-AUC         : {auc:.4f} (95% CI: {auc_ci_str})")
        logging.info(f"Test PR-AUC          : {pr_auc:.4f}")
        logging.info(f"Test Accuracy        : {acc:.4f}")
        logging.info(f"Test Balanced Acc    : {bal_acc:.4f}")
        logging.info(f"Test Precision       : {prec:.4f}")
        logging.info(f"Test Recall (Sens.)  : {rec:.4f}")
        logging.info(f"Test Specificity     : {specificity:.4f}")
        logging.info(f"Test F1-Score        : {f1:.4f} (95% CI: {f1_ci_str})")
        logging.info(f"Test Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")
        logging.info(f"Classification Report:\n{cls_report}")
        
        final_results.append({
            'Nutrient': nutrient.upper(),
            'Test_ROC_AUC': round(auc, 4),
            'ROC_AUC_95_CI': auc_ci_str,
            'Test_PR_AUC': round(pr_auc, 4),
            'Accuracy': round(acc, 4),
            'Balanced_Accuracy': round(bal_acc, 4),
            'Precision': round(prec, 4),
            'Recall_Sensitivity': round(rec, 4),
            'Specificity': round(specificity, 4),
            'F1_Score': round(f1, 4),
            'F1_Score_95_CI': f1_ci_str,
            'MCC': round(mcc, 4),
            'Brier_Score': round(brier, 4),
            'Confusion_Matrix': f"TN={tn}, FP={fp}, FN={fn}, TP={tp}"
        })
        
    os.makedirs("reports", exist_ok=True)
    results_df = pd.DataFrame(final_results)
    results_df.to_csv("reports/test_results.csv", index=False)
    logging.info("Saved final test evaluation report to 'reports/test_results.csv'")
    logging.info("Final Evaluation Completed Successfully.")

if __name__ == "__main__":
    evaluate_final()
