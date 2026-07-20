Project Summary — Nutrient Deficiency Predictor
===============================================

Overview
--------
This repository provides a FastAPI backend, a Vite + React frontend, and an ML pipeline that predicts risk of five micronutrient deficiencies (iron, calcium, vitamin D, vitamin B12, zinc) from a user's demographics and their daily nutrient intake.

Key components
--------------
- Backend: `backend/` — FastAPI app, SQLAlchemy models, authentication, endpoints, and runtime ML wrappers.
- Frontend: `frontend/` — React + TypeScript client, login/register, food search, prediction UI.
- Data & ETL: `backend/scripts/load_database.py` — builds `data/processed/food_database.csv` from USDA and OpenFoodFacts and can seed `food_catalog` into Postgres.
- ML training: `backend/ml/train.py` — trains Random Forest and XGBoost models using processed NHANES-derived features and saves best models to disk.

Why there are two `ml/` folders
-------------------------------
- `backend/ml/` (runtime): model wrappers, prediction and explainer utilities used directly by the backend service in production.
- `ml/` (development/data): training scripts, exploratory notebooks, and the model artifact outputs (models, metrics) used during development. The separation keeps training code and heavy dependencies separate from the backend runtime code.

What changed (latest work)
--------------------------
- ETL: Added a name-cluster-based imputation step in `backend/scripts/load_database.py` to fill missing micronutrient values using TF-IDF + MiniBatchKMeans cluster medians, then global medians as fallback. This improves coverage for foods missing some micronutrients.
- Predict API: Added `date_str` override and `nutrient_totals` optional payload in `backend/app/schemas/predict.py` and updated `PredictionService` to honor these. This helps testing and avoids zero-aggregation problems due to timezone or missing logs.
- Models: Retrained RandomForest + XGBoost models using processed data and saved winners to `backend/ml/models/`.

How the ML models work
----------------------
- Input features: basic demographics (age, gender, race_ethnicity, weight_kg, height_cm, bmi, activity_level) and daily nutrient totals (calories_kcal, protein_g, carbs_g, fat_g, iron_mg, calcium_mg, vitamin_d_mcg, vitamin_b12_mcg, zinc_mg).
- Targets: binary labels per nutrient (deficient / not deficient) derived from NHANES thresholds.
- Training: For each nutrient, both XGBoost and RandomForest are trained on the same train/test split. The model with better ROC-AUC is saved.
- Runtime prediction: The backend loads the saved model(s), runs predict_proba to get risk scores, and uses SHAP (when requested) to generate local explanations for each prediction.

APIs (brief)
------------
- POST /api/v1/predict/  — Run prediction for authenticated user.
  - Body: partial or full `PredictInput` (demographics optional, `date_str` optional, or `nutrient_totals` optional).
  - Returns: `PredictResponse` with per-nutrient risk scores, labels, optional SHAP explanations, and dietary recommendations.
- GET /api/v1/predict/history — Retrieve past predictions for the authenticated user.
- Other endpoints: auth, user profile, food catalog search, food logs (see `backend/app/api/v1/` for full list).

Runbook (essential commands)
----------------------------
- Build processed food CSV (skip OpenFoodFacts on low-memory machines):
```
# PowerShell
$env:SKIP_OFF='1'; $env:DB_LOAD='0'; python .\backend\scripts\load_database.py
```
- Seed Postgres (when ready and DB configured):
```
# Requires DATABASE_URL set in backend/.env
$env:DB_LOAD='1'; python .\backend\scripts\load_database.py
```
- Train models:
```
python .\backend\ml\train.py
```
- Run backend locally:
```
# from backend/ folder
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Next steps and recommendations
------------------------------
- Full OpenFoodFacts ingestion: implement streaming ingestion and batch DB inserts (recommended for large datasets) or run on a machine with sufficient memory/disk.
- Better imputation: augment name-cluster imputation with nutrient lookup from authoritative sources (USDA FDC API) for higher fidelity.
- Model improvements: add nutritional feature engineering (ratios, density per 100kcal), perform hyperparameter tuning (Grid/Optuna), and consider calibration for better probability estimates.
- Frontend: ensure food logs include nutrient fields and that the client stores/sends JWT tokens; use `date_str` when testing predictions to avoid timezone mismatches.

Contact
-------
If you'd like, I can:
- Run the full OpenFoodFacts ingestion with chunked inserts.
- Seed the Postgres DB now.
- Update the frontend to include `date_str` and `nutrient_totals` controls and show SHAP explanations clearly.

*** End of summary
