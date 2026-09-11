import os
import json
import logging
import joblib
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def save_pipeline_manifest():
    logging.info("Starting Model Serialization & Manifest Packaging (Module 12)...")
    
    os.makedirs("models", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    test_results_path = "reports/test_results.csv"
    best_models_path = "reports/best_models.csv"
    
    manifest = {
        'project_name': 'Micronutrient Deficiency Risk Screening System',
        'dataset_source': 'CDC NHANES 2021-2023 (August 2021 - August 2023 Cycle)',
        'recommender_source': 'Indian Nutrient Databank (INDB)',
        'nutrients_covered': ['Iron', 'Calcium', 'Vitamin D', 'Vitamin B12', 'Zinc', 'Magnesium', 'Vitamin C'],
        'models_saved': []
    }
    
    if os.path.exists(best_models_path):
        best_df = pd.read_csv(best_models_path)
        for idx, row in best_df.iterrows():
            nut = row['Nutrient']
            mname = row['Model']
            model_file = f"models/best_model_{nut}.pkl"
            if os.path.exists(model_file):
                manifest['models_saved'].append({
                    'nutrient': nut,
                    'selected_model': mname,
                    'validation_roc_auc': float(row.get('ROC_AUC_Score', 0.0)),
                    'model_path': model_file
                })
                
    manifest_path = "models/model_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=4)
        
    logging.info(f"Saved pipeline manifest to '{manifest_path}'")
    logging.info("Model Serialization & Packaging Completed Successfully.")

if __name__ == "__main__":
    save_pipeline_manifest()
