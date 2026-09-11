import os
import pandas as pd
import numpy as np
import logging
import joblib
import shap
import warnings

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_indb():
    logging.info("Loading Indian Nutrient Databank (INDB)...")
    try:
        df = pd.read_excel("dataset/Indian-Nutrient-Databank-INDB--main/INDB.xlsx")
        cols_to_convert = ['iron_mg', 'calcium_mg', 'vitd2_ug', 'vitd3_ug', 'zinc_mg', 'magnesium_mg', 'vitc_mg']
        for c in cols_to_convert:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        return df
    except Exception as e:
        logging.error(f"Failed to load INDB database: {e}")
        return None

def get_top_foods(indb_df, nutrient, top_n=5):
    if indb_df is None:
        return ["Database unavailable"]
        
    mapping = {
        'iron': 'iron_mg',
        'calcium': 'calcium_mg',
        'vitamin_d': ['vitd2_ug', 'vitd3_ug'],
        'vitamin_b12': None,
        'zinc': 'zinc_mg',
        'magnesium': 'magnesium_mg',
        'vitamin_c': 'vitc_mg'
    }
    
    col = mapping.get(nutrient)
    if col is None:
        fallbacks = {
            'vitamin_b12': ["Whole Milk / Curd", "Eggs", "Poultry Liver", "Fortified Cereals", "Paneer"]
        }
        return fallbacks.get(nutrient, ["Dietary adjustment recommended"])
        
    if isinstance(col, list):
        indb_df['temp_sum'] = indb_df[col].sum(axis=1)
        sort_col = 'temp_sum'
    else:
        sort_col = col
        
    top_df = indb_df.sort_values(by=sort_col, ascending=False).head(top_n)
    return top_df['food_name'].tolist()

def explain_and_recommend():
    logging.info("Starting Explainability & INDB Recommender Module (Module 10)...")
    
    test_file = "processed_data/test_engineered.csv"
    if not os.path.exists(test_file):
        logging.error("Test data file missing.")
        return
        
    test_df = pd.read_csv(test_file)
    import json
    targets = [c for c in test_df.columns if c.startswith('target_')]
    features = [c for c in test_df.columns if not c.startswith('target_') and c != 'SEQN']
    if os.path.exists("models/feature_names.json"):
        with open("models/feature_names.json") as f:
            features = json.load(f)
            
    np.random.seed(42)
    sample_size = min(15, len(test_df))
    sample_df = test_df.sample(sample_size).copy()
    X_sample = sample_df[features].select_dtypes(include=[np.number])
    
    indb_df = load_indb()
    results = []
    
    for target in targets:
        nutrient = target.replace('target_', '')
        model_path = f"models/best_model_{nutrient}.pkl"
        
        if not os.path.exists(model_path):
            continue
            
        logging.info(f"Computing SHAP attributions and food recommendations for {nutrient.upper()}...")
        pipeline = joblib.load(model_path)
        
        target_features = features
        if hasattr(pipeline, 'feature_names_in_'):
            target_features = [c for c in pipeline.feature_names_in_ if c in X_sample.columns]
        elif hasattr(pipeline.named_steps.get('classifier'), 'feature_names_in_'):
            target_features = [c for c in pipeline.named_steps['classifier'].feature_names_in_ if c in X_sample.columns]
            
        X_sub = X_sample[target_features]
        
        try:
            y_prob = pipeline.predict_proba(X_sub)[:, 1]
        except AttributeError:
            y_prob = pipeline.predict(X_sub)
            
        sample_df[f'pred_risk_{nutrient}'] = y_prob
        
        try:
            classifier = pipeline.named_steps.get('classifier', pipeline)
            imputer = pipeline.named_steps.get('imputer', None)
            
            X_trans = X_sample.values
            if imputer:
                X_trans = imputer.transform(X_sample)
                
            if 'scaler' in getattr(pipeline, 'named_steps', {}):
                X_trans = pipeline.named_steps['scaler'].transform(X_trans)
                
            X_trans_df = pd.DataFrame(X_trans, columns=X_sample.columns)
            
            explainer = shap.Explainer(classifier, X_trans_df)
            shap_values = explainer(X_trans_df).values
            if len(shap_values.shape) == 3:
                shap_values = shap_values[:, :, 1]
                
            for i, (idx, row) in enumerate(X_trans_df.iterrows()):
                risk = y_prob[i]
                seqn = sample_df.iloc[i]['SEQN']
                
                if risk >= 0.35: # Screening threshold
                    patient_shap = shap_values[i]
                    top_feature_idx = np.argmax(patient_shap)
                    top_feature_name = X_sample.columns[top_feature_idx]
                    
                    explanation = f"Deficiency Risk: {risk:.1%}. Primary Risk Driver: {top_feature_name}."
                    suggestions = get_top_foods(indb_df, nutrient)
                    
                    results.append({
                        'SEQN': int(seqn),
                        'Nutrient': nutrient.upper(),
                        'Risk_Probability': round(risk, 4),
                        'Top_Risk_Factor': top_feature_name,
                        'Clinical_Explanation': explanation,
                        'INDB_Food_Recommendations': ", ".join(suggestions)
                    })
        except Exception as e:
            logging.warning(f"Fallback SHAP handling for {nutrient}: {e}")
            for i in range(len(sample_df)):
                risk = y_prob[i]
                if risk >= 0.35:
                    seqn = sample_df.iloc[i]['SEQN']
                    suggestions = get_top_foods(indb_df, nutrient)
                    results.append({
                        'SEQN': int(seqn),
                        'Nutrient': nutrient.upper(),
                        'Risk_Probability': round(risk, 4),
                        'Top_Risk_Factor': "Dietary Intake / Demographics",
                        'Clinical_Explanation': f"Deficiency Risk: {risk:.1%}",
                        'INDB_Food_Recommendations': ", ".join(suggestions)
                    })
                    
    if results:
        res_df = pd.DataFrame(results)
        os.makedirs("reports", exist_ok=True)
        out_path = "reports/patient_recommendations.csv"
        res_df.to_csv(out_path, index=False)
        logging.info(f"Saved personalized patient recommendations to '{out_path}'")
        
    logging.info("Explainability & INDB Recommender Module Completed Successfully.")

if __name__ == "__main__":
    explain_and_recommend()
