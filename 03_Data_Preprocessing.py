import os
import pandas as pd
import numpy as np
import logging
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import joblib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_preprocessing_pipeline():
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    return pipeline

def preprocess_data():
    logging.info("Starting Data Preprocessing (Module 03 - Real NHANES Data)...")
    
    nhanes_dir = os.path.join("dataset", "NHANES")
    
    files = {
        'DEMO': 'DEMO_L.xpt',
        'BMX': 'BMX_L.xpt',
        'DR1TOT': 'DR1TOT_L.xpt',
        'DR2TOT': 'DR2TOT_L.xpt',
        'DSQIDS': 'DSQIDS_L.xpt',
        'FERTIN': 'FERTIN_L.xpt',
        'BIOPRO': 'BIOPRO_L.xpt',
        'VID': 'VID_L.xpt',
        'PBCD': 'PBCD_L.xpt',
        'HSCRP': 'HSCRP_L.xpt',
        'FOLATE': 'FOLATE_L.xpt',
        'CBC': 'CBC_L.xpt'
    }
    
    loaded_dfs = {}
    for key, f in files.items():
        path = os.path.join(nhanes_dir, f)
        if os.path.exists(path):
            df = pd.read_sas(path, format='xport')
            # Deduplicate by SEQN if needed
            if 'SEQN' in df.columns:
                df = df.drop_duplicates(subset=['SEQN']).reset_index(drop=True)
            wt_cols = [c for c in df.columns if c.startswith('WT')]
            df = df.drop(columns=wt_cols)
            loaded_dfs[key] = df
            
    if 'DEMO' not in loaded_dfs or 'DR1TOT' not in loaded_dfs:
        logging.error("Core NHANES files missing.")
        return

    logging.info("Merging participant-level datasets on SEQN...")
    merged_df = loaded_dfs['DEMO']
    for key, df_other in loaded_dfs.items():
        if key == 'DEMO':
            continue
        overlap_cols = set(merged_df.columns).intersection(set(df_other.columns))
        overlap_cols.discard('SEQN')
        df_right = df_other.drop(columns=list(overlap_cols))
        merged_df = pd.merge(merged_df, df_right, on='SEQN', how='left')
        
    logging.info(f"Unique Participant Master Shape: {merged_df.shape}")

    # Construct Real Clinical Deficiency Targets (WHO / NIH / IOM Standards)
    logging.info("Constructing clinical deficiency target labels from real biomarkers...")
    
    # Iron Deficiency: Serum Ferritin < 15.0 ug/L (WHO / CDC standard)
    if 'LBXFER' in merged_df.columns:
        merged_df['target_iron'] = (merged_df['LBXFER'] < 15.0).astype(int)
    else:
        merged_df['target_iron'] = (merged_df['DR1TIRON'] < 8.0).astype(int)
        
    # Calcium Deficiency: Total Serum Calcium < 8.5 mg/dL (Clinical Hypocalcemia)
    if 'LBXSCA' in merged_df.columns:
        merged_df['target_calcium'] = (merged_df['LBXSCA'] < 8.5).astype(int)
    else:
        merged_df['target_calcium'] = (merged_df['DR1TCALC'] < 500.0).astype(int)
        
    # Vitamin D Deficiency: 25(OH)D < 50.0 nmol/L (Endocrine Society / IOM Standard)
    if 'LBXVIDMS' in merged_df.columns:
        merged_df['target_vitamin_d'] = (merged_df['LBXVIDMS'] < 50.0).astype(int)
    else:
        merged_df['target_vitamin_d'] = (merged_df['DR1TVD'] < 10.0).astype(int)
        
    # Vitamin B12 / Folate Deficiency: RBC Folate < 305 nmol/L (WHO Standard)
    if 'LBDRFO' in merged_df.columns:
        merged_df['target_vitamin_b12'] = (merged_df['LBDRFO'] < 305.0).astype(int)
    else:
        merged_df['target_vitamin_b12'] = (merged_df['DR1TB12'] < 2.0).astype(int)
        
    # Zinc Deficiency: Blood Manganese / Zinc < lower 20th percentile
    if 'LBXBMN' in merged_df.columns:
        zinc_cutoff = merged_df['LBXBMN'].quantile(0.20)
        merged_df['target_zinc'] = (merged_df['LBXBMN'] < zinc_cutoff).astype(int)
    else:
        merged_df['target_zinc'] = (merged_df['DR1TZINC'] < 6.0).astype(int)
        
    # Magnesium Deficiency: Serum Magnesium < 1.82 mg/dL (~0.75 mmol/L, Hypomagnesemia)
    if 'LBXMAGN' in merged_df.columns:
        merged_df['target_magnesium'] = (merged_df['LBXMAGN'] < 1.82).astype(int)
    else:
        merged_df['target_magnesium'] = (merged_df['DR1TMAGN'] < 200.0).astype(int)
        
    # Vitamin C Deficiency: Day 1 Dietary Intake < 45.0 mg/day (WHO RNI Inadequacy Cutoff)
    if 'DR1TVC' in merged_df.columns:
        merged_df['target_vitamin_c'] = (merged_df['DR1TVC'] < 45.0).astype(int)
    else:
        merged_df['target_vitamin_c'] = 0

    # Drop Biomarker/Lab columns to prevent target leakage into features
    biomarker_cols = [c for c in merged_df.columns if c.startswith(('LBX', 'LBD'))]
    logging.info(f"Removing {len(biomarker_cols)} laboratory biomarker variables to enforce leakage prevention...")
    merged_df = merged_df.drop(columns=biomarker_cols)

    target_cols = [c for c in merged_df.columns if c.startswith('target_')]
    dist_records = []
    for tc in target_cols:
        nut = tc.replace('target_', '')
        pos_cnt = merged_df[tc].sum()
        total_cnt = len(merged_df)
        prev_pct = (pos_cnt / total_cnt) * 100
        dist_records.append({
            'Nutrient': nut.upper(),
            'Total_Participants': total_cnt,
            'Deficient_Cases': pos_cnt,
            'Prevalence_Pct': round(prev_pct, 2)
        })
        logging.info(f"Prevalence {nut.upper()}: {pos_cnt}/{total_cnt} ({prev_pct:.2f}%)")
        
    dist_df = pd.DataFrame(dist_records)
    os.makedirs("reports", exist_ok=True)
    dist_df.to_csv("reports/target_distribution_report.csv", index=False)
    logging.info("Saved Target Prevalence Distribution Report to 'reports/target_distribution_report.csv'")

    logging.info("Performing Stratified 70/15/15 Data Split...")
    train_val_df, test_df = train_test_split(
        merged_df, test_size=0.15, random_state=42, stratify=merged_df['target_iron']
    )
    train_df, val_df = train_test_split(
        train_val_df, test_size=0.1764, random_state=42, stratify=train_val_df['target_iron']
    )
    
    logging.info(f"Train Set: {train_df.shape[0]} rows | Validation Set: {val_df.shape[0]} rows | Test Set: {test_df.shape[0]} rows")
    
    os.makedirs("processed_data", exist_ok=True)
    train_df.to_csv("processed_data/train.csv", index=False)
    val_df.to_csv("processed_data/val.csv", index=False)
    test_df.to_csv("processed_data/test.csv", index=False)
    logging.info("Saved raw train, val, and test splits to 'processed_data/'")
    
    os.makedirs("models", exist_ok=True)
    pipeline_template = create_preprocessing_pipeline()
    joblib.dump(pipeline_template, "models/preprocessing_template.pkl")
    logging.info("Saved preprocessing pipeline template to 'models/'")
    
    logging.info("Data Preprocessing Completed Successfully.")

if __name__ == "__main__":
    preprocess_data()
