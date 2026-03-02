import os
from pathlib import Path
from urllib.parse import quote_plus


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"


def _normalize_postgres_scheme(url):
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def _resolve_database_url():
    # 1) Explicit DATABASE_URL (highest priority)
    database_url = _normalize_postgres_scheme(os.getenv("DATABASE_URL"))
    if database_url:
        return database_url

    # 2) Full Supabase URL
    supabase_db_url = _normalize_postgres_scheme(os.getenv("SUPABASE_DB_URL"))
    if supabase_db_url:
        return supabase_db_url

    # 3) Supabase components (safe for special chars in password)
    project_ref = os.getenv("SUPABASE_PROJECT_REF")
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    if project_ref and db_password:
        encoded_password = quote_plus(db_password)
        return (
            f"postgresql+psycopg2://postgres:{encoded_password}"
            f"@db.{project_ref}.supabase.co:5432/postgres?sslmode=require"
        )

    # 4) Local SQLite fallback
    return f"sqlite:///{(INSTANCE_DIR / 'database.db').as_posix()}"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    SQLALCHEMY_DATABASE_URI = _resolve_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
