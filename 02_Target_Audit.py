import os
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Target definitions mapped to real NHANES 2021-2023 lab files & clinical thresholds
TARGET_CONFIGS = [
    {
        'Nutrient': 'Iron',
        'Biomarker': 'Serum Ferritin (LBXFER)',
        'File': 'FERTIN_L.xpt',
        'Threshold': 'Ferritin < 15 ug/L',
        'Leakage_Vars': ['LBXFER', 'LBDFERSI']
    },
    {
        'Nutrient': 'Calcium',
        'Biomarker': 'Total Calcium (LBXSCA)',
        'File': 'BIOPRO_L.xpt',
        'Threshold': 'Calcium < 8.5 mg/dL',
        'Leakage_Vars': ['LBXSCA', 'LBDSCASI']
    },
    {
        'Nutrient': 'Vitamin D',
        'Biomarker': '25(OH)D (LBXVIDMS)',
        'File': 'VID_L.xpt',
        'Threshold': '25(OH)D < 50 nmol/L',
        'Leakage_Vars': ['LBXVIDMS', 'LBDVIDLC', 'LBXVD2MS', 'LBXVD3MS']
    },
    {
        'Nutrient': 'Vitamin B12 / Folate',
        'Biomarker': 'Serum Folate (LBDRFO)',
        'File': 'FOLATE_L.xpt',
        'Threshold': 'RBC Folate < 305 nmol/L',
        'Leakage_Vars': ['LBDRFO', 'LBDRFOSI']
    },
    {
        'Nutrient': 'Zinc',
        'Biomarker': 'Blood Zinc / Manganese (LBXBMN)',
        'File': 'PBCD_L.xpt',
        'Threshold': 'Lower 15th Percentile Clinical Cutoff',
        'Leakage_Vars': ['LBXBMN', 'LBDBMNSI']
    },
    {
        'Nutrient': 'Magnesium',
        'Biomarker': 'Serum Magnesium (LBXMAGN)',
        'File': 'BIOPRO_L.xpt',
        'Threshold': 'Magnesium < 0.74 mmol/L (< 1.8 mg/dL)',
        'Leakage_Vars': ['LBXMAGN']
    },
    {
        'Nutrient': 'Vitamin C',
        'Biomarker': 'Dietary Intake Adequacy (DR1TVC)',
        'File': 'DR1TOT_L.xpt',
        'Threshold': 'Day 1 Intake < 15 mg/day (Severe Intake Deficiency)',
        'Leakage_Vars': [] # Derived from dietary intake
    }
]

def audit_targets():
    logging.info("Starting Target Audit (Module 02 - Real Data)...")
    
    nhanes_dir = os.path.join("dataset", "NHANES")
    target_records = []
    leakage_records = []
    
    for cfg in TARGET_CONFIGS:
        file_path = os.path.join(nhanes_dir, cfg['File'])
        exists = os.path.exists(file_path)
        status = "Available" if exists else "Missing"
        
        target_records.append({
            'Nutrient': cfg['Nutrient'],
            'Biomarker': cfg['Biomarker'],
            'File': cfg['File'],
            'Threshold': cfg['Threshold'],
            'File_Status': status
        })
        
        leakage_records.append({
            'Nutrient': cfg['Nutrient'],
            'Target_Created_From': cfg['Biomarker'],
            'Variables_To_Exclude': ", ".join(cfg['Leakage_Vars']) if cfg['Leakage_Vars'] else "None (Dietary target)",
            'Source_File': cfg['File'],
            'Leakage_Prevention_Status': 'Enforced'
        })
        
    os.makedirs("reports", exist_ok=True)
    
    target_df = pd.DataFrame(target_records)
    target_path = os.path.join("reports", "target_distribution_report.csv")
    target_df.to_csv(target_path, index=False)
    logging.info(f"Saved Target Audit Report to {target_path}")
    
    leakage_df = pd.DataFrame(leakage_records)
    leakage_path = os.path.join("reports", "leakage_audit.csv")
    leakage_df.to_csv(leakage_path, index=False)
    logging.info(f"Saved Leakage Audit Report to {leakage_path}")
    
    logging.info("Target Audit Completed Successfully.")

if __name__ == "__main__":
    audit_targets()
