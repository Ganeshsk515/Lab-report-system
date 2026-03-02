from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

import os
from pathlib import Path
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    from app.models import User

    return db.session.get(User, int(user_id))


def _load_local_env():
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / ".env"
    fallback_path = base_dir / ".env.example"

    source_path = env_path if env_path.exists() else fallback_path
    if not source_path.exists():
        return

    for raw_line in source_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        os.environ.setdefault(key, value.strip())


def create_app(config_class=None):
    _load_local_env()
    from config import Config

    config_class = config_class or Config
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes import main

    app.register_blueprint(main)

    with app.app_context():
        _log_database_target(app)
        _fail_if_render_uses_sqlite()
        db.create_all()
        _ensure_sqlite_schema()
        _bootstrap_admin()

    return app


def _log_database_target(app):
    sanitized = db.engine.url.render_as_string(hide_password=True)
    app.logger.warning("Active DB: %s", sanitized)


def _fail_if_render_uses_sqlite():
    # Render sets RENDER=true for deployed services.
    is_render = os.getenv("RENDER", "").lower() == "true"
    if not is_render:
        return

    if db.engine.url.get_backend_name() == "sqlite":
        raise RuntimeError(
            "Render is using SQLite fallback. Set SUPABASE_DB_URL or DATABASE_URL in Render environment variables."
        )


def _bootstrap_admin():
    from app.models import User

    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL")
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
    admin_name = os.getenv("DEFAULT_ADMIN_NAME", "System Admin")

    if not admin_email or not admin_password:
        return

    try:
        existing_user = User.query.filter_by(email=admin_email.lower().strip()).first()
    except OperationalError:
        return

    if existing_user:
        return

    admin = User(
        username=admin_name,
        email=admin_email.lower().strip(),
        role="admin",
    )
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.commit()


def _ensure_sqlite_schema():
    if db.engine.url.get_backend_name() != "sqlite":
        return

    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    if not table_names:
        return

    needs_reset = False

    if "diagnostic_report" not in table_names:
        needs_reset = True

    if "patient" in table_names:
        patient_cols = {col["name"] for col in inspector.get_columns("patient")}
        if "patient_code" not in patient_cols or "full_name" not in patient_cols:
            needs_reset = True

    if "user" in table_names:
        user_cols = {col["name"] for col in inspector.get_columns("user")}
        if "created_at" not in user_cols or "patient_id" not in user_cols:
            needs_reset = True

    allow_reset = os.getenv("ALLOW_SQLITE_RESET", "true").lower() == "true"
    if needs_reset and allow_reset:
        db.drop_all()
        db.create_all()
