#!/usr/bin/env python3
"""
check_db.py — ASHA Seva database diagnostic & setup tool
==========================================================
Run this before starting the app to verify everything is in order.

Usage:
    python check_db.py           # full check
    python check_db.py --fix     # check + auto-create missing DB / tables
"""

import os
import socket
import sys
from pathlib import Path
from urllib.parse import quote_plus

# ---------------------------------------------------------------------------
# Bootstrap: make sure we can import from the backend package
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

try:
    from dotenv import load_dotenv
    load_dotenv(_HERE / ".env")
except ImportError:
    print("⚠️  python-dotenv not installed — reading only real env vars.")

FIX_MODE = "--fix" in sys.argv

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):    print(f"{GREEN}  ✅  {msg}{RESET}")
def warn(msg):  print(f"{YELLOW}  ⚠️   {msg}{RESET}")
def fail(msg):  print(f"{RED}  ❌  {msg}{RESET}")
def info(msg):  print(f"      {msg}")
def header(msg):print(f"\n{BOLD}{msg}{RESET}")


# ---------------------------------------------------------------------------
# 1. .env file
# ---------------------------------------------------------------------------

header("1. Environment file (.env)")

env_path = _HERE / ".env"
if env_path.exists():
    ok(f".env found at {env_path}")
else:
    warn(".env not found — using system environment variables / defaults.")
    info("Copy .env.example to .env and fill in your database credentials.")

# ---------------------------------------------------------------------------
# 2. Required env vars
# ---------------------------------------------------------------------------

header("2. Required environment variables")

DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "5432"))
DB_USER     = os.getenv("DB_USER",     "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME     = os.getenv("DB_NAME",     "asha_db")

print(f"      DB_HOST     = {DB_HOST}")
print(f"      DB_PORT     = {DB_PORT}")
print(f"      DB_USER     = {DB_USER}")
print(f"      DB_PASSWORD = {'*' * len(DB_PASSWORD)}")
print(f"      DB_NAME     = {DB_NAME}")

# ---------------------------------------------------------------------------
# 3. PostgreSQL reachability
# ---------------------------------------------------------------------------

header("3. PostgreSQL connectivity")

pg_ok = False
try:
    with socket.create_connection((DB_HOST, DB_PORT), timeout=3):
        ok(f"TCP connection to {DB_HOST}:{DB_PORT} succeeded.")
        pg_ok = True
except OSError as e:
    fail(f"Cannot reach PostgreSQL at {DB_HOST}:{DB_PORT} → {e}")
    info("Possible fixes:")
    info("  • Start PostgreSQL:  sudo systemctl start postgresql")
    info("  • Or use Docker:     docker compose up -d")
    info("  • The app will automatically fall back to SQLite if PG is unavailable.")

# ---------------------------------------------------------------------------
# 4. psycopg import
# ---------------------------------------------------------------------------

header("4. psycopg (PostgreSQL driver)")

try:
    import psycopg  # noqa: F401
    ok("psycopg v3 available.")
except ImportError:
    fail("psycopg not installed.")
    info("Fix:  pip install 'psycopg[binary]'")

# ---------------------------------------------------------------------------
# 5. Database existence & connection
# ---------------------------------------------------------------------------

header("5. Database login & schema")

_SQLITE_PATH = _HERE / "app" / "database" / "asha_seva.db"

if pg_ok:
    try:
        import psycopg
        encoded = quote_plus(DB_PASSWORD)
        conn_str = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"

        try:
            conn = psycopg.connect(conn_str, connect_timeout=5)
            conn.close()
            ok(f"Connected to PostgreSQL database '{DB_NAME}'.")
        except psycopg.OperationalError as e:
            if "does not exist" in str(e):
                fail(f"Database '{DB_NAME}' does not exist.")
                if FIX_MODE:
                    info(f"Creating database '{DB_NAME}'…")
                    try:
                        admin_conn = psycopg.connect(
                            f"host={DB_HOST} port={DB_PORT} dbname=postgres "
                            f"user={DB_USER} password={DB_PASSWORD}",
                            autocommit=True, connect_timeout=5,
                        )
                        admin_conn.execute(f'CREATE DATABASE "{DB_NAME}"')
                        admin_conn.close()
                        ok(f"Database '{DB_NAME}' created.")
                    except Exception as ce:
                        fail(f"Could not create database: {ce}")
                        info(f"Manual fix:  psql -U {DB_USER} -c \"CREATE DATABASE {DB_NAME};\"")
                else:
                    info(f"Manual fix:  psql -U {DB_USER} -c \"CREATE DATABASE {DB_NAME};\"")
                    info("Or run:     python check_db.py --fix")
            else:
                fail(f"Login failed: {e}")
                info(f"Check DB_USER and DB_PASSWORD in .env")
    except ImportError:
        warn("psycopg not installed — skipping database login check.")
else:
    warn(f"PostgreSQL unavailable — will use SQLite at {_SQLITE_PATH}")
    if _SQLITE_PATH.exists():
        ok(f"SQLite file exists ({_SQLITE_PATH.stat().st_size // 1024} KB).")
    else:
        info("SQLite file does not exist yet — it will be created on first app start.")

# ---------------------------------------------------------------------------
# 6. SQLAlchemy table check (optional --fix)
# ---------------------------------------------------------------------------

header("6. SQLAlchemy models & tables")

if FIX_MODE:
    info("--fix mode: running db.create_all() to ensure all tables exist…")
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from app.extensions import db
            db.create_all()
            ok("All tables created / verified.")
    except SystemExit:
        fail("App failed to start — see error above.")
    except Exception as e:
        fail(f"db.create_all() failed: {e}")
else:
    info("Run with --fix to auto-create missing tables: python check_db.py --fix")

# ---------------------------------------------------------------------------
# 7. Summary
# ---------------------------------------------------------------------------

header("7. Summary")

print()
if pg_ok:
    print(f"  {GREEN}▶  PostgreSQL is the active database.{RESET}")
    print(f"     Data is stored in: {DB_HOST}:{DB_PORT}/{DB_NAME}")
else:
    print(f"  {YELLOW}▶  SQLite fallback is active.{RESET}")
    print(f"     Data will be stored in: {_SQLITE_PATH}")
    print(f"     To switch to PostgreSQL, start it and restart the app.")

print()
print(f"  Start the app:   python app.py")
print(f"  Health check:    curl http://localhost:5000/api/health")
print()
