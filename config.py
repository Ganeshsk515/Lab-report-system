import os
from pathlib import Path
from urllib.parse import quote_plus


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"


def _normalize_postgres_scheme(url):
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def _clean_env_value(value):
    if not value:
        return value
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in ("'", '"'):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def _resolve_database_url():
    # 1) Full Supabase URL (highest priority)
    supabase_db_url = _normalize_postgres_scheme(_clean_env_value(os.getenv("SUPABASE_DB_URL")))
    if supabase_db_url:
        return supabase_db_url

    # 2) Supabase components (safe for special chars in password)
    project_ref = _clean_env_value(os.getenv("SUPABASE_PROJECT_REF"))
    db_password = _clean_env_value(os.getenv("SUPABASE_DB_PASSWORD"))
    if project_ref and db_password:
        encoded_password = quote_plus(db_password)
        return (
            f"postgresql+psycopg2://postgres:{encoded_password}"
            f"@db.{project_ref}.supabase.co:5432/postgres?sslmode=require"
        )

    # 3) Explicit DATABASE_URL
    database_url = _normalize_postgres_scheme(_clean_env_value(os.getenv("DATABASE_URL")))
    if database_url:
        return database_url

    # 4) Local SQLite fallback
    return f"sqlite:///{(INSTANCE_DIR / 'database.db').as_posix()}"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    SQLALCHEMY_DATABASE_URI = _resolve_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = _clean_env_value(os.getenv("MAIL_SERVER"))
    MAIL_PORT = int(_clean_env_value(os.getenv("MAIL_PORT")) or 587)
    MAIL_USE_TLS = _clean_env_value(os.getenv("MAIL_USE_TLS", "true")).lower() == "true"
    MAIL_USE_SSL = _clean_env_value(os.getenv("MAIL_USE_SSL", "false")).lower() == "true"
    MAIL_USERNAME = _clean_env_value(os.getenv("MAIL_USERNAME"))
    MAIL_PASSWORD = _clean_env_value(os.getenv("MAIL_PASSWORD"))
    MAIL_FROM = _clean_env_value(os.getenv("MAIL_FROM"))
    EMAIL_VERIFY_TOKEN_MAX_AGE = int(_clean_env_value(os.getenv("EMAIL_VERIFY_TOKEN_MAX_AGE")) or 86400)
    PASSWORD_RESET_TOKEN_MAX_AGE = int(
        _clean_env_value(os.getenv("PASSWORD_RESET_TOKEN_MAX_AGE")) or 3600
    )
