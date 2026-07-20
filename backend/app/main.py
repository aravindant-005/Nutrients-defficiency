from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router

# Autocreate database tables if they do not exist
# Note: For production architectures, migration systems like Alembic are preferred.
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
except Exception as e:
    print(f"Skipping database schema initialization: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Apply CORS middleware config
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

# Bind version 1 master router routes
app.include_router(api_router, prefix=settings.API_V1_STR)
