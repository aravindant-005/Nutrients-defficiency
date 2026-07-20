import os
from urllib.parse import urlparse, urlunparse

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine

from app.core.config import settings
from app.core.database import Base
import app.models.deficiency  # noqa: F401


def create_database_if_missing(database_url: str) -> None:
    parsed = urlparse(database_url)
    if parsed.scheme not in ("postgresql", "postgres"):
        raise ValueError(f"Unsupported database scheme: {parsed.scheme}")

    db_name = parsed.path.lstrip("/")
    if not db_name:
        raise ValueError("Database URL must include a database name")

    default_db = "postgres"
    default_netloc = parsed.netloc
    default_path = f"/{default_db}"
    default_url = urlunparse((parsed.scheme, default_netloc, default_path, "", "", ""))

    print(f"Checking database existence for '{db_name}' using default connection to '{default_db}'... ")

    conn = psycopg2.connect(default_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cursor.fetchone() is not None
            if exists:
                print(f"Database '{db_name}' already exists.")
            else:
                print(f"Creating database '{db_name}'...")
                cursor.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(db_name)))
                print(f"Database '{db_name}' created.")
    finally:
        conn.close()


def create_tables(database_url: str) -> None:
    engine = create_engine(database_url)
    print("Creating tables in database...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")


if __name__ == "__main__":
    db_url = settings.DATABASE_URL
    print(f"Using DATABASE_URL: {db_url}")
    create_database_if_missing(db_url)
    create_tables(db_url)
