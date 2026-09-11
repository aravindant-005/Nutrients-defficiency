import os
import urllib.request
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles"

LAB_FILES = {
    'FERTIN_L.xpt': f"{BASE_URL}/FERTIN_L.xpt",  # Serum Ferritin (Iron)
    'BIOPRO_L.xpt': f"{BASE_URL}/BIOPRO_L.xpt",  # Total Calcium, Magnesium, Biochemistry
    'VID_L.xpt': f"{BASE_URL}/VID_L.xpt",        # Vitamin D 25(OH)D
    'PBCD_L.xpt': f"{BASE_URL}/PBCD_L.xpt",      # Blood Zinc, Lead, Cadmium
    'HSCRP_L.xpt': f"{BASE_URL}/HSCRP_L.xpt",    # High-sensitivity C-Reactive Protein
    'FOLATE_L.xpt': f"{BASE_URL}/FOLATE_L.xpt",  # Serum Folate / B12 related
    'CBC_L.xpt': f"{BASE_URL}/CBC_L.xpt"         # Complete Blood Count (Hemoglobin, Hematocrit)
}

def download_and_verify():
    target_dir = os.path.join("dataset", "NHANES")
    os.makedirs(target_dir, exist_ok=True)
    
    for filename, url in LAB_FILES.items():
        filepath = os.path.join(target_dir, filename)
        need_download = True
        if os.path.exists(filepath):
            try:
                df = pd.read_sas(filepath, format='xport')
                if len(df) > 100:
                    logging.info(f"Verified {filename}: Valid XPT file (Shape: {df.shape})")
                    need_download = False
            except Exception as e:
                logging.warning(f"File {filename} is corrupt ({e}). Redownloading...")
                
        if need_download:
            logging.info(f"Downloading {filename} from {url}...")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req) as resp, open(filepath, 'wb') as out_f:
                    out_f.write(resp.read())
                df = pd.read_sas(filepath, format='xport')
                logging.info(f"Successfully downloaded and verified {filename} (Shape: {df.shape}).")
            except Exception as e:
                logging.error(f"Failed to download/verify {filename}: {e}")

if __name__ == "__main__":
    download_and_verify()
