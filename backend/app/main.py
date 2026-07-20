from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router

# Import all models so SQLAlchemy can discover and create the tables
import app.models.deficiency  # noqa: F401

# Create all PostgreSQL tables on startup (idempotent — skips existing tables)
try:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                ALTER TABLE prediction_histories
                ADD COLUMN IF NOT EXISTS magnesium_risk FLOAT NOT NULL DEFAULT 0.0;
                ALTER TABLE prediction_histories
                ADD COLUMN IF NOT EXISTS vitamin_c_risk FLOAT NOT NULL DEFAULT 0.0;
                """
            )
        )

    print("✓ PostgreSQL tables verified/created.")
except Exception as e:
    print(f"⚠ Database schema init warning: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description=(
        "AI-powered Micronutrient Deficiency Detection System. "
        "Predicts Iron, Calcium, Vitamin D, Vitamin B12, Zinc, Magnesium, and Vitamin C deficiency risks "
        "using XGBoost / Random Forest ML models with SHAP explanations."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    print(f"✓ CORS enabled for: {settings.BACKEND_CORS_ORIGINS}")


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint — returns ok when the server is running."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": "2.0.0",
        "database": "PostgreSQL",
    }


# Mount versioned API
app.include_router(api_router, prefix=settings.API_V1_STR)
