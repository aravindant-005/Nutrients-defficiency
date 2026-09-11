import os
import pandas as pd
import numpy as np
import logging
import joblib
from sklearn.metrics import roc_auc_score

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_ablation():
    logging.info("Starting Ablation Study (Module 08)...")
    
    train_file = "processed_data/train_engineered.csv"
    val_file = "processed_data/val_engineered.csv"
    
    if not os.path.exists(train_file) or not os.path.exists(val_file):
        logging.error("Engineered data files missing.")
        return
        
    train_df = pd.read_csv(train_file)
    val_df = pd.read_csv(val_file)
    
    targets = [c for c in train_df.columns if c.startswith('target_')]
    
    import json
    valid_features = [c for c in train_df.columns if not c.startswith('target_') and c != 'SEQN']
    if os.path.exists("models/feature_names.json"):
        with open("models/feature_names.json") as f:
            valid_features = json.load(f)
            
    # Feature Subsets
    feature_subsets = {
        'Full_Feature_Set': valid_features,
        'No_Interactions': [c for c in valid_features if not c.startswith(('target_', 'grpG_interaction'))],
        'Demographics_Diet_Only': [c for c in valid_features if c.startswith(('grpA', 'grpC', 'grpD'))]
    }
    
    ablation_records = []
    
    for target in targets:
        y_train = train_df[target]
        y_val = val_df[target]
        nutrient = target.replace('target_', '')
        
        best_model_path = f"models/best_model_{nutrient}.pkl"
        if not os.path.exists(best_model_path):
            continue
            
        base_pipeline = joblib.load(best_model_path)
        classifier = base_pipeline.named_steps['classifier']
        
        logging.info(f"Ablation testing for {nutrient.upper()}...")
        
        for subset_name, cols in feature_subsets.items():
            X_tr = train_df[cols]
            X_va = val_df[cols]
            
            # Clone and fit pipeline steps
            from sklearn.base import clone
            clf_clone = clone(base_pipeline)
            
            try:
                clf_clone.fit(X_tr, y_train)
                y_prob = clf_clone.predict_proba(X_va)[:, 1]
                auc = roc_auc_score(y_val, y_prob)
            except Exception as e:
                auc = np.nan
                
            ablation_records.append({
                'Nutrient': nutrient,
                'Feature_Subset': subset_name,
                'Num_Features': len(cols),
                'Validation_ROC_AUC': auc
            })
            logging.info(f"   Subset: {subset_name:25s} | Features: {len(cols):2d} | ROC-AUC: {auc:.4f}")
            
    os.makedirs("reports", exist_ok=True)
    ablation_df = pd.DataFrame(ablation_records)
    ablation_df.to_csv("reports/ablation_results.csv", index=False)
    logging.info("Saved ablation study results to 'reports/ablation_results.csv'")
    logging.info("Ablation Study Completed Successfully.")

if __name__ == "__main__":
    run_ablation()
