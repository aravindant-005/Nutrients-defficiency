import os
import pandas as pd
import numpy as np
import logging
import joblib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_interactions():
    logging.info("Starting Interaction Analysis (Module 09)...")
    
    val_file = "processed_data/val_engineered.csv"
    if not os.path.exists(val_file):
        logging.error("Validation data file missing.")
        return
        
    val_df = pd.read_csv(val_file)
    targets = [c for c in val_df.columns if c.startswith('target_')]
    
    co_occur_matrix = val_df[targets].corr()
    
    os.makedirs("reports", exist_ok=True)
    co_occur_matrix.to_csv("reports/deficiency_co_occurrence.csv")
    logging.info("Saved deficiency co-occurrence correlation matrix to 'reports/deficiency_co_occurrence.csv'")
    logging.info("Interaction Analysis Completed Successfully.")

if __name__ == "__main__":
    analyze_interactions()
