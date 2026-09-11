import os
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MODULES = [
    "01_Data_Audit.py",
    "02_Target_Audit.py",
    "03_Data_Preprocessing.py",
    "04_Feature_Engineering.py",
    "05_Leakage_Check.py",
    "06_Model_Training.py",
    "07_Model_Comparison.py",
    "13_Generate_Plots.py",
    "08_Ablation_Study.py",
    "09_Interaction_Analysis.py",
    "10_Explainability_Recommender.py",
    "11_Final_Evaluation.py",
    "12_Model_Saving.py"
]

def run_all():
    logging.info("Executing End-to-End Micronutrient ML Pipeline...")
    for mod in MODULES:
        logging.info(f"\n==========================================")
        logging.info(f" RUNNING MODULE: {mod}")
        logging.info(f"==========================================")
        cmd = [sys.executable, mod]
        res = subprocess.run(cmd, cwd=os.getcwd())
        if res.returncode != 0:
            logging.error(f"Module {mod} failed with exit code {res.returncode}. Aborting pipeline.")
            sys.exit(res.returncode)
            
    logging.info("\n==========================================")
    logging.info(" PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    logging.info("==========================================")

if __name__ == "__main__":
    run_all()
