"""
Database configuration and CSV sync utility.
Every write to PostgreSQL automatically mirrors to a CSV file.
"""

import os
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# ── Connection URL ─────────────────────────────────────────────────────────────
# Password is URL-encoded (@ → %40)
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Jiya%40664")   # %40 = @
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "asha_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,          # reconnect on stale connections
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ── CSV export directory ───────────────────────────────────────────────────────
CSV_DIR = Path(__file__).resolve().parent.parent / "csv_exports"
CSV_DIR.mkdir(parents=True, exist_ok=True)
(CSV_DIR / "backups").mkdir(parents=True, exist_ok=True)


# ── Dependency injection ──────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── CSV sync helpers ──────────────────────────────────────────────────────────

def _row_to_dict(obj) -> dict:
    """Convert a SQLAlchemy model instance to a plain dict."""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def upsert_csv_row(table_name: str, row: dict):
    """
    Append or update one row in <table_name>.csv.
    Uses 'id' as the primary key for updates.
    Creates the file with headers if it doesn't exist.
    """
    csv_path = CSV_DIR / f"{table_name}.csv"
    row_id   = row.get("id")

    if not csv_path.exists() or csv_path.stat().st_size == 0:
        # Create fresh
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            writer.writeheader()
            writer.writerow(row)
        return

    df = pd.read_csv(csv_path, dtype=str)
    if "id" in df.columns and row_id is not None:
        mask = df["id"] == str(row_id)
        if mask.any():
            # Update existing
            for k, v in row.items():
                df.loc[mask, k] = str(v) if v is not None else ""
            df.to_csv(csv_path, index=False)
            return

    # Append new row
    new_row = {k: str(v) if v is not None else "" for k, v in row.items()}
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(df.columns))
        # ensure new row has all columns
        merged = {col: new_row.get(col, "") for col in df.columns}
        writer.writerow(merged)


def delete_csv_row(table_name: str, row_id: int):
    """Remove a row from the CSV by id."""
    csv_path = CSV_DIR / f"{table_name}.csv"
    if not csv_path.exists():
        return
    df = pd.read_csv(csv_path, dtype=str)
    if "id" in df.columns:
        df = df[df["id"] != str(row_id)]
        df.to_csv(csv_path, index=False)


def rebuild_csv_from_db(db, Model, table_name: str):
    """Fully regenerate a CSV from the current DB table."""
    csv_path = CSV_DIR / f"{table_name}.csv"
    rows = db.query(Model).all()
    if not rows:
        csv_path.unlink(missing_ok=True)
        return
    records = [_row_to_dict(r) for r in rows]
    df = pd.DataFrame(records)
    df.to_csv(csv_path, index=False)


def sync_model_to_csv(instance):
    """
    Call this after any insert/update on a model instance.
    Automatically resolves table name.
    """
    table_name = instance.__tablename__
    row = _row_to_dict(instance)
    upsert_csv_row(table_name, row)
