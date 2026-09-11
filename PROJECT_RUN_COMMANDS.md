# 🚀 NutriDetect AI - Complete Project Execution Guide

This document provides exact, copy-pasteable terminal commands to run the **NutriDetect AI** full-stack web application, database, and machine learning training pipeline.

---

## 📌 Project Overview & Prerequisites

- **Python Version**: Python 3.10+ / 3.12
- **Node.js Version**: Node.js 18+ / 20+
- **Project Root Directory**: `e:\ml`

---

## 1. 🌐 Running the Full-Stack Web Application

### A. Start Backend Server (FastAPI API)
Open Terminal 1 in project root `e:\ml`:

```powershell
# Activate virtual environment if applicable, then run FastAPI backend:
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend API URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Database Engine**: Automatic Dual-Engine (Attempts PostgreSQL on port 5432; falls back automatically to embedded `micronutrient_app.db` SQLite).

---

### B. Start Frontend Web Application (React + Vite)
Open Terminal 2 in project root `e:\ml`:

```powershell
# Run Vite Dev Server:
npx vite --host 127.0.0.1 --port 5173
```
- **Frontend App URL**: [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## 2. 🤖 Running Machine Learning Pipeline Scripts

If you wish to re-run data cleaning, feature engineering, model training, SHAP explainability, ablation, or report generation:

### Run Master Runner (Executes Modules 08 to 12 Sequentially)
```powershell
python run_final_modules.py
```

### Or Run Individual Pipeline Modules Step-by-Step:

1. **Data Cleaning & Standardization**:
   ```powershell
   python 01_Data_Cleaning.py
   ```
2. **Demographic & Dietary Merging**:
   ```powershell
   python 02_Data_Merging.py
   ```
3. **Nutrient Deficiency Labeling**:
   ```powershell
   python 03_Labeling.py
   ```
4. **Feature Engineering (50 Exact Features)**:
   ```powershell
   python 04_Feature_Engineering.py
   ```
5. **Preprocessing & Dataset Splitting**:
   ```powershell
   python 05_Preprocessing.py
   ```
6. **Model Training & Hyperparameter Tuning (8 Candidates x 7 Nutrients)**:
   ```powershell
   python 06_Model_Training.py
   ```
7. **Feature Ablation Study**:
   ```powershell
   python 08_Ablation_Study.py
   ```
8. **Deficiency Co-Occurrence Analysis**:
   ```powershell
   python 09_CoOccurrence_Analysis.py
   ```
9. **SHAP Tree/Linear Explainability & Recommender Test**:
   ```powershell
   python 10_Explainability_Recommender.py
   ```
10. **Statistical Significance Testing (McNemar & DeLong Tests)**:
    ```powershell
    python 11_Statistical_Testing.py
    ```
11. **Report Builder & Trained Models Saving**:
    ```powershell
    python 12_Model_Saving.py
    ```

---

## 3. 🗄️ Database Management & Schema Import

### SQLite (Default Embedded Database)
- Database File: `micronutrient_app.db` (auto-created in `e:\ml` when backend starts).

### PostgreSQL (Optional for pgAdmin Production Use)
1. Open pgAdmin or psql terminal.
2. Create database:
   ```sql
   CREATE DATABASE micronutrient_db;
   ```
3. Import DDL schema from `backend/schema.sql`:
   ```powershell
   psql -U postgres -d micronutrient_db -f backend/schema.sql
   ```

---

## 4. 🧪 API Verification & Testing Commands

### Test Food Search Endpoint (INDB Databank)
```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/food/search?q=Paneer').read().decode())"
```

### Test ML Risk Prediction Endpoint
```powershell
python -c "import urllib.request; req = urllib.request.Request('http://127.0.0.1:8000/api/predict/risk/1', data=b'{}', headers={'Content-Type': 'application/json'}); print(urllib.request.urlopen(req).read().decode())"
```

### Check Active Running Processes (Windows PowerShell)
```powershell
Get-Process -Name python, node -ErrorAction SilentlyContinue
```

---

## 📂 Key Generated Reports & Artifacts

- **Final Research Markdown Report**: `reports/final_research_report.md`
- **Ablation Study Results**: `reports/ablation_results.csv`
- **Deficiency Co-Occurrence Matrix**: `reports/deficiency_co_occurrence.csv`
- **Saved Trained Models**: `models/best_model_*.pkl`
