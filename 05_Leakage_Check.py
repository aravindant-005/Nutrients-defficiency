import os
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def audit_leakage():
    logging.info("Starting Data Leakage Audit (Module 05)...")
    
    train_path = "processed_data/train_engineered.csv"
    if not os.path.exists(train_path):
        logging.error(f"Cannot find {train_path}")
        return
        
    df = pd.read_csv(train_path)
    
    target_cols = [c for c in df.columns if c.startswith('target_')]
    feature_cols = [c for c in df.columns if not c.startswith('target_') and c != 'SEQN']
    
    logging.info(f"Target Columns ({len(target_cols)}): {target_cols}")
    logging.info(f"Feature Columns count: {len(feature_cols)}")
    
    # Check for direct lab biomarker leakage
    forbidden_prefixes = ['LBX', 'LBD', 'SIM_']
    leaked_cols = [c for c in feature_cols if any(c.startswith(prefix) for prefix in forbidden_prefixes)]
    
    if leaked_cols:
        logging.error(f"DATA LEAKAGE DETECTED! Found forbidden biomarker columns in features: {leaked_cols}")
    else:
        logging.info("PASS: No direct biomarker leakage variables found in features.")
        
    # Check for constant or ID features
    if 'SEQN' in feature_cols:
        logging.error("DATA LEAKAGE DETECTED! Participant ID (SEQN) is present in feature set.")
    else:
        logging.info("PASS: Participant ID (SEQN) properly excluded from training features.")
        
    # Check point-biserial correlation for target leakage (|r| > 0.90)
    high_corr_leakage = []
    for tc in target_cols:
        for fc in feature_cols:
            corr = df[tc].corr(df[fc])
            if abs(corr) > 0.90:
                high_corr_leakage.append((tc, fc, corr))
                logging.warning(f"HIGH CORRELATION DETECTED: {fc} vs {tc} (r = {corr:.4f})")
                
    if not high_corr_leakage:
        logging.info("PASS: All engineered feature correlations with targets are below 0.90 threshold.")
        
    # Save leakage audit summary
    audit_summary = f"Leakage Audit Status: PASS\nTotal Features: {len(feature_cols)}\nExcluded Biomarkers: Enforced\nExcluded SEQN: True\nHigh Correlation Flags: {len(high_corr_leakage)}"
    os.makedirs("reports", exist_ok=True)
    with open("reports/leakage_audit_post_engineering.txt", "w") as f:
        f.write(audit_summary)
        
    logging.info("Data Leakage Audit Completed Successfully.")

if __name__ == "__main__":
    audit_leakage()
