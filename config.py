import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{(INSTANCE_DIR / 'database.db').as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
