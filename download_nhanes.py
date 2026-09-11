import os
import urllib.request
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

FILES = {
    # Core Feature Files
    'DEMO_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/DEMO_J.xpt',
    'BMX_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/BMX_J.xpt',
    'DR1TOT_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/DR1TOT_J.xpt',
    'DR2TOT_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/DR2TOT_J.xpt',
    
    # Real Biomarker Lab Files
    'FETIN_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/FETIN_J.xpt',  # Ferritin (Iron)
    'PBCD_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/PBCD_J.xpt',    # Lead, Cadmium, Zinc
    'BIOPRO_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/BIOPRO_J.xpt',  # Calcium, Magnesium
    'VID_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/VID_J.xpt',      # Vitamin D
    'B12_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/B12_J.xpt',      # Vitamin B12
    'VIC_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/VIC_J.xpt',      # Vitamin C
    
    # Clinical & Lifestyle Predictors
    'HSCRP_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/HSCRP_J.xpt',  # High-sensitivity CRP
    'DSQIDS_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/DSQIDS_J.xpt', # Supplement use
    'SMQ_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/SMQ_J.xpt',      # Smoking
    'ALQ_J.xpt': 'https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/ALQ_J.xpt'       # Alcohol
}

def download_all():
    target_dir = os.path.join("dataset", "NHANES")
    os.makedirs(target_dir, exist_ok=True)
    
    for filename, url in FILES.items():
        filepath = os.path.join(target_dir, filename)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            logging.info(f"{filename} already exists ({os.path.getsize(filepath)} bytes). Skipping download.")
            continue
            
        logging.info(f"Downloading {filename} from {url}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req) as resp, open(filepath, 'wb') as out_f:
                out_f.write(resp.read())
            logging.info(f"Successfully saved {filename} ({os.path.getsize(filepath)} bytes).")
        except Exception as e:
            logging.error(f"Failed to download {filename}: {e}")

if __name__ == "__main__":
    download_all()
