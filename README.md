# 🥗 Nutrition Deficiency Prediction System

A full-stack, AI-powered web application that predicts potential **nutrition deficiencies** based on user-provided inputs — symptoms, dietary habits, and blood marker data — and explains *why* the model made each prediction using **SHAP (SHapley Additive exPlanations)**.

The goal of this system is to bridge the gap between raw health data and actionable insight: instead of just telling a user "you may be deficient in Vitamin D," it shows *which factors* (e.g., low sun exposure, specific blood markers, reported fatigue) drove that prediction, making the output interpretable and trustworthy for both users and healthcare-adjacent applications.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Directory Structure](#-directory-structure)
- [How It Works](#-how-it-works)
- [Prerequisites](#-prerequisites)
- [Local Development Setup](#-local-development-setup)
  - [Backend (FastAPI)](#backend-fastapi)
  - [Frontend (React/Vite)](#frontend-reactvite)
- [Running with Docker Compose](#-running-with-docker-compose)
- [Environment Variables](#-environment-variables)
- [API Overview](#-api-overview)
- [Machine Learning Pipeline](#-machine-learning-pipeline)
- [Authentication](#-authentication)
- [Testing](#-testing)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

- **Symptom & Diet-Based Prediction** — Users submit structured inputs (symptoms checklist, dietary habits, optional lab/blood markers) and receive a predicted likelihood of specific nutrient deficiencies (e.g., Iron, Vitamin D, B12, Calcium).
- **Explainable AI (XAI)** — Every prediction is paired with a SHAP-based explanation showing which input features contributed most, and in which direction, to the model's output.
- **User Accounts & History** — Secure JWT-based authentication lets users register, log in, and view a history of their past predictions over time.
- **Interactive Dashboard** — A React-based dashboard visualizes prediction results, trends, and feature-importance breakdowns.
- **RESTful API** — A cleanly versioned FastAPI backend (`/api/v1/...`) exposes endpoints for authentication, prediction, and history retrieval, with auto-generated OpenAPI docs.
- **Containerized Deployment** — One-command startup for the entire stack (database, backend, frontend) via Docker Compose.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React (Vite + TypeScript), Tailwind CSS, React Router, Axios |
| **Backend** | FastAPI, SQLAlchemy (ORM), Uvicorn (ASGI server), JWT Authentication |
| **Database** | PostgreSQL |
| **Machine Learning** | Scikit-Learn, XGBoost, SHAP |
| **Infrastructure** | Docker, Docker Compose |

---

## 🏗 System Architecture

At a high level, the system follows a classic three-tier architecture:

```
┌─────────────────┐        HTTPS/JSON        ┌──────────────────┐        SQL        ┌──────────────┐
│  React Frontend │ ───────────────────────▶ │  FastAPI Backend │ ─────────────────▶│  PostgreSQL  │
│  (Vite + TS)    │ ◀─────────────────────── │  (REST API)      │ ◀─────────────────│   Database   │
└─────────────────┘      JWT-authenticated    └──────────────────┘                    └──────────────┘
                                                        │
                                                        ▼
                                          ┌───────────────────────────┐
                                          │  ML Layer (in-process)    │
                                          │  XGBoost model + SHAP     │
                                          │  explainer                │
                                          └───────────────────────────┘
```

1. The **frontend** collects user input through guided forms (symptoms, diet, optional blood markers) and sends it to the backend.
2. The **backend** validates the request (via Pydantic schemas), authenticates the user (JWT), and passes the data to the **ML layer**.
3. The **ML layer** runs the trained XGBoost classifier to produce deficiency predictions and uses SHAP to compute per-feature contribution scores.
4. Results are persisted to **PostgreSQL** (for history) and returned to the frontend, which renders the prediction alongside a SHAP explanation chart.

---

## 📁 Directory Structure

```
d:\nutrients/
├── backend/                          # FastAPI application
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints/        # auth.py, predict.py, history.py
│   │   ├── core/                     # config.py, database.py, security.py (JWT)
│   │   ├── models/                   # SQLAlchemy ORM models (User, Prediction, etc.)
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── ml/                       # XGBoost model + SHAP explainer wrappers
│   │   └── tests/                    # Pytest test suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── components/               # Layout, Navbar, Route guards
│   │   ├── context/                  # AuthContext (JWT state management)
│   │   ├── pages/                    # Dashboard, Prediction, Login, Register
│   │   ├── services/                 # Axios API client
│   │   └── router.tsx                # React Router configuration
│   ├── Dockerfile
│   ├── tailwind.config.js
│   └── package.json
├── docker-compose.yml                # Orchestrates Postgres + backend + frontend
└── README.md                         # You are here
```

---

## ⚙️ How It Works

1. **User Registration/Login** — Users create an account or log in; the backend issues a JWT access token stored client-side and attached to subsequent requests.
2. **Data Collection** — On the Prediction page, the user fills out a form covering:
   - Reported symptoms (fatigue, brittle nails, hair loss, etc.)
   - Dietary patterns (e.g., meat consumption, dairy intake, vegetable variety)
   - Optional lab values (hemoglobin, ferritin, vitamin D levels, etc., if the user has them)
3. **Prediction Request** — The frontend POSTs this payload to `/api/v1/predict`.
4. **Model Inference** — The backend loads the pre-trained XGBoost model and generates a probability score for each tracked deficiency category.
5. **Explanation Generation** — SHAP values are computed for the same input, quantifying how much each feature pushed the prediction up or down.
6. **Response & Storage** — The prediction, along with its SHAP explanation, is saved to the user's history in PostgreSQL and returned to the frontend for visualization.
7. **History & Trends** — Users can revisit `/api/v1/history` to see past predictions and track how their risk factors change over time.

---

## ✅ Prerequisites

Before you begin, make sure you have the following installed:

- **Python** 3.10+
- **Node.js** 18+ and npm
- **PostgreSQL** 14+ (if running without Docker)
- **Docker** & **Docker Compose** (if running the containerized stack)

---

## 🚀 Local Development Setup

### Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv

   # On Windows:
   .\venv\Scripts\activate

   # On Unix/macOS:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   > Edit `.env` to set your PostgreSQL connection string, JWT secret key, and any ML model paths.

5. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`, with interactive Swagger docs at `http://localhost:8000/docs`.

### Frontend (React/Vite)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install npm packages:
   ```bash
   npm install
   ```

3. Set environment parameters:
   ```bash
   cp .env.example .env
   ```
   > Edit `.env` to point `VITE_API_BASE_URL` to your backend (e.g., `http://localhost:8000/api/v1`).

4. Start the dev server:
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:5173` by default (Vite's default port).

---

## 🐳 Running with Docker Compose

To build and spin up the entire stack — PostgreSQL, FastAPI backend, and React frontend — in one step:

```bash
docker-compose up --build
```

Once the containers are running:

| Service | URL |
|---|---|
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **Frontend Client** | http://localhost |
| **PostgreSQL** | `localhost:5432` (internal to Docker network by default) |

To stop and remove containers:
```bash
docker-compose down
```

To also wipe the database volume (full reset):
```bash
docker-compose down -v
```

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/nutrients` |
| `SECRET_KEY` | Secret key used to sign JWT tokens | `super-secret-random-string` |
| `ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `60` |
| `MODEL_PATH` | Path to the trained XGBoost model artifact | `app/ml/model.pkl` |

### Frontend (`frontend/.env`)

| Variable | Description | Example |
|---|---|---|
| `VITE_API_BASE_URL` | Base URL for backend API calls | `http://localhost:8000/api/v1` |

> ⚠️ Never commit real `.env` files. Only `.env.example` files with placeholder values should be tracked in version control.

---

## 🔌 API Overview

All endpoints are versioned under `/api/v1`.

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/auth/register` | Create a new user account | No |
| `POST` | `/auth/login` | Authenticate and receive a JWT token | No |
| `GET` | `/auth/me` | Get the currently authenticated user's profile | Yes |
| `POST` | `/predict` | Submit symptoms/diet/blood data and receive a deficiency prediction with SHAP explanation | Yes |
| `GET` | `/history` | Retrieve the authenticated user's past predictions | Yes |
| `GET` | `/history/{id}` | Retrieve a specific past prediction by ID | Yes |

Full interactive documentation (with request/response schemas) is auto-generated by FastAPI and available at `/docs` (Swagger UI) or `/redoc` (ReDoc) once the backend is running.

---

## 🤖 Machine Learning Pipeline

- **Model**: An `XGBoost` classifier (or multi-output classifier for multi-label deficiency prediction) trained on a dataset combining symptom checklists, dietary features, and blood marker values.
- **Preprocessing**: Handled via Scikit-Learn pipelines (imputation for missing lab values, encoding for categorical symptoms/diet fields, scaling for numeric markers).
- **Explainability**: `SHAP`'s `TreeExplainer` is used against the trained XGBoost model to compute per-prediction feature attributions, which are serialized and returned alongside the prediction so the frontend can render a waterfall or bar chart of contributing factors.
- **Model Artifacts**: Stored under `backend/app/ml/` and loaded once at application startup for efficient inference (rather than reloading per-request).

> 📌 Note: The `app/ml/` directory currently contains scaffolding for the model and SHAP explainer. Replace the placeholder logic with your trained model artifact and matching preprocessing pipeline before deploying to production.

---

## 🔐 Authentication

- Authentication uses **JSON Web Tokens (JWT)**.
- On login, the backend issues a signed access token containing the user's identity and an expiration claim.
- The frontend stores this token (e.g., in memory or `localStorage`, depending on implementation) and attaches it as a `Bearer` token in the `Authorization` header for all protected requests.
- Protected routes on the frontend are wrapped in a route guard component that redirects unauthenticated users to the login page.
- Passwords are never stored in plaintext — they are hashed (e.g., via `passlib`/`bcrypt`) before being persisted to the database.

---

## 🧪 Testing

Backend tests live under `backend/app/tests/` and use `pytest`.

```bash
cd backend
pytest
```

Recommended test coverage areas:
- Auth flows (registration, login, token validation)
- Prediction endpoint input validation
- ML pipeline output shape/consistency
- Database model constraints

---

## 🗺 Roadmap

- [ ] Expand the model to support additional deficiency categories (e.g., Magnesium, Zinc, Folate)
- [ ] Add data visualization for historical trend analysis across multiple predictions
- [ ] Support CSV/PDF export of prediction history
- [ ] Add rate limiting and refresh-token support for improved auth security
- [ ] CI/CD pipeline for automated testing and deployment

---



## 📄 License

This project is provided as-is for educational and development purposes. Add your preferred license (e.g., MIT, Apache 2.0) here before public release.

---

## ⚕️ Disclaimer

This application is intended for **informational and educational purposes only** and does not constitute medical advice, diagnosis, or treatment. Predictions generated by the model should not be used as a substitute for professional medical consultation. Always consult a qualified healthcare provider regarding nutrition or health concerns.
