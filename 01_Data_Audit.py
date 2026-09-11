import os
import pandas as pd
import numpy as np
import glob
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def audit_dataset():
    logging.info("Starting Data Audit (Module 01 - Real Data)...")
    
    nhanes_dir = os.path.join("dataset", "NHANES")
    if not os.path.exists(nhanes_dir):
        logging.error(f"NHANES directory not found at {nhanes_dir}")
        return
        
    xpt_files = glob.glob(os.path.join(nhanes_dir, "*.xpt"))
    if not xpt_files:
        logging.error("No .xpt files found in NHANES directory.")
        return

    logging.info(f"Found {len(xpt_files)} .xpt files.")
    
    dfs = []
    loaded_files = []
    for file in xpt_files:
        fname = os.path.basename(file)
        # Exclude IFF files (individual food item records) to keep participant-level granularity
        if 'IFF' in fname:
            continue
        try:
            df = pd.read_sas(file, format='xport')
            if 'SEQN' in df.columns and len(df) > 0:
                dfs.append(df)
                loaded_files.append(fname)
                logging.info(f"Loaded {fname} with shape {df.shape}")
        except Exception as e:
            logging.warning(f"Skipping {fname}: {e}")
            
    if not dfs:
        logging.error("No valid dataframes loaded.")
        return
        
    logging.info(f"Merging {len(dfs)} participant-level datasets on SEQN...")
    merged_df = dfs[0]
    for i in range(1, len(dfs)):
        overlap_cols = set(merged_df.columns).intersection(set(dfs[i].columns))
        overlap_cols.discard('SEQN')
        df_right = dfs[i].drop(columns=list(overlap_cols))
        merged_df = pd.merge(merged_df, df_right, on='SEQN', how='outer')
            
    logging.info(f"Merged Participant-Level Dataset Shape: {merged_df.shape}")
    
    num_rows, num_cols = merged_df.shape
    duplicate_rows = merged_df.duplicated().sum()
    duplicate_seqn = merged_df['SEQN'].duplicated().sum() if 'SEQN' in merged_df.columns else "N/A"
    
    logging.info(f"Duplicate Rows: {duplicate_rows}")
    logging.info(f"Duplicate Participant IDs (SEQN): {duplicate_seqn}")
    
    # Column-level audit
    audit_records = []
    for col in merged_df.columns:
        col_data = merged_df[col]
        dtype = str(col_data.dtype)
        num_unique = col_data.nunique()
        missing_count = col_data.isnull().sum()
        missing_pct = (missing_count / num_rows) * 100
        is_constant = (num_unique <= 1)
        
        extreme_outliers = 0
        if pd.api.types.is_numeric_dtype(col_data):
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            extreme_outliers = ((col_data < lower_bound) | (col_data > upper_bound)).sum()
            
        audit_records.append({
            'Column': col,
            'DataType': dtype,
            'Unique_Values': num_unique,
            'Missing_Count': missing_count,
            'Missing_Pct': round(missing_pct, 2),
            'Is_Constant': is_constant,
            'Extreme_Outliers': extreme_outliers
        })
        
    audit_df = pd.DataFrame(audit_records)
    os.makedirs("reports", exist_ok=True)
    report_path = os.path.join("reports", "data_quality_report.csv")
    audit_df.to_csv(report_path, index=False)
    logging.info(f"Data quality report saved to {report_path}")
    
    # Identify highly correlated feature pairs (>0.90)
    logging.info("Calculating correlation matrix...")
    numeric_cols = merged_df.select_dtypes(include=[np.number]).columns
    cols_for_corr = [c for c in numeric_cols if c != 'SEQN' and not c.startswith('WT')]
    
    corr_matrix = merged_df[cols_for_corr].corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    high_corr_pairs = [(c1, c2) for c1 in upper.columns for c2 in upper.index if upper.loc[c2, c1] > 0.90]
    
    if high_corr_pairs:
        corr_df = pd.DataFrame(high_corr_pairs, columns=['Feature_1', 'Feature_2'])
        corr_path = os.path.join("reports", "highly_correlated_features.csv")
        corr_df.to_csv(corr_path, index=False)
        logging.info(f"Saved {len(high_corr_pairs)} highly correlated feature pairs to {corr_path}")

    # Create Feature Dictionary
    feature_dict_records = []
    for col in merged_df.columns:
        source = "NHANES 2021-2023"
        reason = ""
        allowed = "Yes"
        
        if col == "SEQN":
            allowed = "No"
            reason = "Participant ID"
        elif col.startswith("WT"):
            allowed = "No"
            reason = "Survey Weight"
        elif col.startswith(('LBX', 'LBD')):
            allowed = "No"
            reason = "Lab Biomarker - Reserved for Target Generation or Leakage Exclusion"
            
        feature_dict_records.append({
            'Column': col,
            'Source': source,
            'Type': str(merged_df[col].dtype),
            'Allowed_for_ML': allowed,
            'Reason': reason
        })
        
    dict_df = pd.DataFrame(feature_dict_records)
    dict_path = os.path.join("reports", "feature_dictionary.csv")
    dict_df.to_csv(dict_path, index=False)
    logging.info(f"Feature dictionary template saved to {dict_path}")

    logging.info("Data Audit Completed Successfully.")

if __name__ == "__main__":
    audit_dataset()
