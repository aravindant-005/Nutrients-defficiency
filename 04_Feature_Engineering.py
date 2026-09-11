import os
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def safe_divide(a, b):
    with np.errstate(divide='ignore', invalid='ignore'):
        c = np.true_divide(a, b)
        c[~np.isfinite(c)] = np.nan
    return c

def engineer_features(df):
    logging.info(f"Engineering features for dataset of shape {df.shape}")
    engineered_df = pd.DataFrame()
    
    # Preserve IDs and Targets
    engineered_df['SEQN'] = df['SEQN']
    target_cols = [c for c in df.columns if c.startswith('target_')]
    for tc in target_cols:
        engineered_df[tc] = df[tc]
        
    # GROUP A: Demographics
    engineered_df['grpA_age'] = pd.to_numeric(df.get('RIDAGEYR'), errors='coerce')
    engineered_df['grpA_sex'] = pd.to_numeric(df.get('RIAGENDR'), errors='coerce')
    engineered_df['grpA_race'] = pd.to_numeric(df.get('RIDRETH1'), errors='coerce')
    
    # GROUP B: Anthropometrics
    engineered_df['grpB_weight'] = pd.to_numeric(df.get('BMXWT'), errors='coerce')
    engineered_df['grpB_height'] = pd.to_numeric(df.get('BMXHT'), errors='coerce')
    engineered_df['grpB_bmi'] = pd.to_numeric(df.get('BMXBMI'), errors='coerce')
    engineered_df['grpB_waist'] = pd.to_numeric(df.get('BMXWAIST'), errors='coerce')
    
    # Clean unreasonable body measurements
    engineered_df.loc[engineered_df['grpB_bmi'] > 100, 'grpB_bmi'] = np.nan
    engineered_df.loc[engineered_df['grpB_weight'] > 300, 'grpB_weight'] = np.nan
    engineered_df.loc[engineered_df['grpB_height'] > 250, 'grpB_height'] = np.nan
    
    # GROUP C: Dietary Energy & Macronutrients (Day 1)
    engineered_df['grpC_calories'] = pd.to_numeric(df.get('DR1TKCAL'), errors='coerce')
    engineered_df['grpC_protein'] = pd.to_numeric(df.get('DR1TPROT'), errors='coerce')
    engineered_df['grpC_carbohydrate'] = pd.to_numeric(df.get('DR1TCARB'), errors='coerce')
    engineered_df['grpC_fat'] = pd.to_numeric(df.get('DR1TTFAT'), errors='coerce')
    engineered_df['grpC_fiber'] = pd.to_numeric(df.get('DR1TFIBE'), errors='coerce')
    
    # GROUP D: Micronutrient Intake (Day 1)
    engineered_df['grpD_iron'] = pd.to_numeric(df.get('DR1TIRON'), errors='coerce')
    engineered_df['grpD_calcium'] = pd.to_numeric(df.get('DR1TCALC'), errors='coerce')
    engineered_df['grpD_vitamin_d'] = pd.to_numeric(df.get('DR1TVD'), errors='coerce')
    engineered_df['grpD_vitamin_b12'] = pd.to_numeric(df.get('DR1TB12'), errors='coerce')
    engineered_df['grpD_zinc'] = pd.to_numeric(df.get('DR1TZINC'), errors='coerce')
    engineered_df['grpD_magnesium'] = pd.to_numeric(df.get('DR1TMAGN'), errors='coerce')
    engineered_df['grpD_vitamin_c'] = pd.to_numeric(df.get('DR1TVC'), errors='coerce')
    engineered_df['grpD_folate'] = pd.to_numeric(df.get('DR1TFOLA'), errors='coerce')
    
    # GROUP E: Short-Term Dietary Dynamics (2-day mean & variability)
    nutrients = {
        'iron': ('DR1TIRON', 'DR2TIRON'),
        'calcium': ('DR1TCALC', 'DR2TCALC'),
        'vitamin_d': ('DR1TVD', 'DR2TVD'),
        'vitamin_b12': ('DR1TB12', 'DR2TB12'),
        'zinc': ('DR1TZINC', 'DR2TZINC'),
        'magnesium': ('DR1TMAGN', 'DR2TMAGN'),
        'vitamin_c': ('DR1TVC', 'DR2TVC'),
        'calories': ('DR1TKCAL', 'DR2TKCAL')
    }
    
    for nut, (d1, d2) in nutrients.items():
        if d1 in df.columns and d2 in df.columns:
            v1 = pd.to_numeric(df[d1], errors='coerce')
            v2 = pd.to_numeric(df[d2], errors='coerce')
            engineered_df[f'grpE_{nut}_abs_diff'] = (v1 - v2).abs()
            engineered_df[f'grpE_{nut}_mean'] = (v1 + v2) / 2.0
            std_val = pd.concat([v1, v2], axis=1).std(axis=1)
            mean_val = engineered_df[f'grpE_{nut}_mean']
            engineered_df[f'grpE_{nut}_cv'] = safe_divide(std_val, mean_val)
            
    # GROUP F: RDA Nutrient Adequacy Ratios
    rda_refs = {
        'iron': 18.0, 
        'calcium': 1000.0,
        'vitamin_d': 15.0,
        'vitamin_b12': 2.4,
        'zinc': 11.0,
        'magnesium': 400.0,
        'vitamin_c': 90.0
    }
    for nut, ref_val in rda_refs.items():
        d1_col = f'grpD_{nut}'
        if d1_col in engineered_df.columns:
            engineered_df[f'grpF_{nut}_adequacy'] = safe_divide(engineered_df[d1_col], ref_val)
            
    # GROUP G: Clinical, Lifestyle & Absorption Predictors (Numeric Encodings & Bio-Interactions)
    if 'DSDSUPP' in df.columns:
        engineered_df['grpG_supplement_use'] = pd.to_numeric(df['DSDSUPP'], errors='coerce')
    if 'LBXHSCRP' in df.columns:
        engineered_df['grpG_crp'] = pd.to_numeric(df['LBXHSCRP'], errors='coerce')
    if 'SMQ020' in df.columns:
        engineered_df['grpG_smoking_status'] = pd.to_numeric(df['SMQ020'], errors='coerce')
    if 'ALQ130' in df.columns:
        engineered_df['grpG_alcohol_use'] = pd.to_numeric(df['ALQ130'], errors='coerce')
    
    if 'grpD_iron' in engineered_df.columns and 'grpD_vitamin_c' in engineered_df.columns:
        engineered_df['grpG_interaction_iron_vitC'] = engineered_df['grpD_iron'] * engineered_df['grpD_vitamin_c']
        
    if 'grpD_calcium' in engineered_df.columns and 'grpD_vitamin_d' in engineered_df.columns:
        engineered_df['grpG_interaction_calc_vitD'] = engineered_df['grpD_calcium'] * engineered_df['grpD_vitamin_d']
        
    if 'grpC_protein' in engineered_df.columns and 'grpD_iron' in engineered_df.columns:
        engineered_df['grpG_interaction_protein_iron'] = engineered_df['grpC_protein'] * engineered_df['grpD_iron']
        
    if 'grpC_protein' in engineered_df.columns and 'grpD_zinc' in engineered_df.columns:
        engineered_df['grpG_interaction_protein_zinc'] = engineered_df['grpC_protein'] * engineered_df['grpD_zinc']
        
    # Strictly select numeric columns only
    numeric_cols = engineered_df.select_dtypes(include=[np.number]).columns
    engineered_df = engineered_df[numeric_cols]
    
    for c in numeric_cols:
        if c != 'SEQN' and not c.startswith('target_'):
            engineered_df[c] = engineered_df[c].replace([np.inf, -np.inf], np.nan)
            if c.startswith(('grpC', 'grpD', 'grpE_mean', 'grpF', 'grpG')):
                engineered_df.loc[engineered_df[c] < 0, c] = 0.0

    return engineered_df

def main():
    splits = ['train', 'val', 'test']
    for split in splits:
        file_path = f"processed_data/{split}.csv"
        if not os.path.exists(file_path):
            logging.error(f"Cannot find {file_path}")
            continue
            
        df = pd.read_csv(file_path)
        eng_df = engineer_features(df)
        
        out_path = f"processed_data/{split}_engineered.csv"
        eng_df.to_csv(out_path, index=False)
        logging.info(f"Saved engineered numeric features to {out_path}")
        
    logging.info("Feature Engineering Completed Successfully.")

if __name__ == "__main__":
    main()
