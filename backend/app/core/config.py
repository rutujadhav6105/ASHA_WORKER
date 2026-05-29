"""
app/core/config.py
==================
Centralised configuration – PostgreSQL only.

The application now requires a reachable PostgreSQL instance. No SQLite fallback is provided.
"""

import logging
import os
import socket
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file's directory)
_HERE = Path(__file__).resolve().parent          # app/core/
_ROOT = _HERE.parent.parent                      # backend/
load_dotenv(_ROOT / ".env")

logger = logging.getLogger(__name__)

def _is_pg_reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False

# Compute once at import time so all Config classes share the same decision
def _get_database_url() -> str:
    """
    Determine the database URL:
    1. DATABASE_URL env var override
    2. PostgreSQL (if reachable)
    3. SQLite fallback at backend/app/database/asha_seva.db
    """
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        if explicit_url.startswith("postgres://"):
            explicit_url = explicit_url.replace("postgres://", "postgresql+psycopg://", 1)
        logger.info("🗄️  Using DATABASE_URL override.")
        return explicit_url

    user     = os.getenv("DB_USER",     "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    host     = os.getenv("DB_HOST",     "localhost")
    port     = int(os.getenv("DB_PORT", "5432"))
    db_name  = os.getenv("DB_NAME",     "asha_db")

    if _is_pg_reachable(host, port):
        encoded_password = quote_plus(password)
        pg_url = f"postgresql+psycopg://{user}:{encoded_password}@{host}:{port}/{db_name}"
        logger.info("🐘  Configured for PostgreSQL: %s:%s", host, port)
        return pg_url
    else:
        # Fallback to SQLite
        sqlite_dir = _ROOT / "app" / "database"
        sqlite_dir.mkdir(parents=True, exist_ok=True)
        sqlite_path = sqlite_dir / "asha_seva.db"
        sqlite_url = f"sqlite:///{sqlite_path.as_posix()}"
        logger.warning("⚠️  PostgreSQL is unreachable. Falling back to persistent SQLite at %s", sqlite_path)
        return sqlite_url


def _engine_options(db_url: str) -> dict:
    """Return appropriate connection-pool options based on DB type."""
    if db_url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False}
        }
    return {
        "pool_size":    5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,   # recycle connections every 30 min
        "pool_pre_ping": True,  # verify connections before use
    }



# Compute once at import time so all Config classes share the same decision
_DATABASE_URL     = _get_database_url()
_ENGINE_OPTIONS   = _engine_options(_DATABASE_URL)


class BaseConfig:
    """Shared settings for all environments."""

    # ------------------------------------------------------------------ Flask
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    DEBUG:      bool = False
    TESTING:    bool = False

    # -------------------------------------------------------------- SQLAlchemy
    SQLALCHEMY_DATABASE_URI:        str  = _DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO:                bool = False   # set True to log SQL queries
    SQLALCHEMY_ENGINE_OPTIONS:      dict = _ENGINE_OPTIONS

    # -------------------------------------------------------------------- JWT
    JWT_SECRET_KEY:           str = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))

    # ------------------------------------------------------------------- CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")

    # ---------------------------------------------------------------- Exports
    BASE_DIR:    str = str(_ROOT)
    EXPORTS_DIR: str = str(_ROOT / os.getenv("EXPORTS_DIR", "exports"))


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = False   # flip to True to see raw SQL


class ProductionConfig(BaseConfig):
    DEBUG = False


class TestingConfig(BaseConfig):
    TESTING = True
    # Tests use an isolated in-memory SQLite — never touches real data

    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}


# ---------------------------------------------------------------------- lookup
_ENV_MAP = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}


def get_config():
    """Return the correct Config class based on FLASK_ENV."""
    env = os.getenv("FLASK_ENV", "development")
    return _ENV_MAP.get(env, DevelopmentConfig)
