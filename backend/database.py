import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database")

POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/micronutrient_db")
SQLITE_URL = "sqlite:///./micronutrient_app.db"

engine = None
db_type = "postgresql"

try:
    # Try PostgreSQL first
    test_engine = create_engine(POSTGRES_URL, connect_args={"connect_timeout": 3})
    with test_engine.connect() as conn:
        logger.info("Connected to PostgreSQL successfully.")
    engine = test_engine
    db_type = "postgresql"
except Exception as e:
    logger.warning(f"PostgreSQL not reachable ({e}). Falling back to SQLite database.")
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
    db_type = "sqlite"

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
