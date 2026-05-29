"""
app/utils/csv_utils.py
=======================
Reusable helpers for CSV export and import.

Design decisions:
  • All files written with UTF-8 + BOM so Excel opens them correctly.
  • Export  → reads from DB via SQLAlchemy ORM, converts to pandas DataFrame,
              saves to  backend/exports/<table_name>.csv
  • Import  → reads uploaded CSV, validates schema columns, deduplicates
              against existing DB rows, bulk-inserts new rows only.
  • Duplicate detection uses a configurable unique_key per table.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from flask import current_app
from sqlalchemy import inspect, text

from app.extensions import db

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Registry: table_name → { model, unique_cols }
# unique_cols are used to detect duplicate rows during import.
# ------------------------------------------------------------------
def _build_table_registry() -> dict:
    """
    Lazily import models here (inside a function) to avoid circular imports
    at module load time.  Called on first use.
    """
    from app.models.anc      import ANCRecord
    from app.models.children import ChildModel
    from app.models.family   import FamilyMemberModel, FamilyModel
    from app.models.user     import UserModel
    from app.models.vaccine  import VaccineEntry

    return {
        "users":          {"model": UserModel,          "unique_cols": ["mobile", "worker_id"]},
        "families":       {"model": FamilyModel,        "unique_cols": ["home_no", "village", "family_head"]},
        "family_members": {"model": FamilyMemberModel,  "unique_cols": ["aadhaar", "name", "family_id"]},
        "anc_records":    {"model": ANCRecord,          "unique_cols": ["beneficiary_name", "mobile", "lmp"]},
        "children":       {"model": ChildModel,         "unique_cols": ["child_name", "mother_name", "dob"]},
        "vaccine_entries":{"model": VaccineEntry,       "unique_cols": ["child_id", "name", "due_date"]},
    }


# Module-level cache populated on first call
_TABLE_REGISTRY: dict | None = None


def get_table_registry() -> dict:
    global _TABLE_REGISTRY
    if _TABLE_REGISTRY is None:
        _TABLE_REGISTRY = _build_table_registry()
    return _TABLE_REGISTRY


# ------------------------------------------------------------------
# Export
# ------------------------------------------------------------------

def export_table_to_csv(table_name: str) -> str:
    """
    Query all rows from *table_name* and write them to a UTF-8 CSV file.

    Returns:
        str – absolute path of the saved CSV file.

    Raises:
        ValueError – if table_name is not registered.
        RuntimeError – if the export fails for any reason.
    """
    registry = get_table_registry()
    if table_name not in registry:
        raise ValueError(
            f"Table '{table_name}' not supported. "
            f"Available: {list(registry.keys())}"
        )

    model = registry[table_name]["model"]

    try:
        # Fetch all rows via ORM
        rows = db.session.execute(db.select(model)).scalars().all()

        if not rows:
            # Return empty CSV with column headers only
            mapper   = inspect(model)
            columns  = [c.key for c in mapper.mapper.columns]
            df       = pd.DataFrame(columns=columns)
        else:
            df = pd.DataFrame([_row_to_dict(row) for row in rows])

        # Save with UTF-8 BOM so Excel reads it correctly
        exports_dir = current_app.config["EXPORTS_DIR"]
        os.makedirs(exports_dir, exist_ok=True)

        filename  = f"{table_name}.csv"
        filepath  = os.path.join(exports_dir, filename)
        df.to_csv(filepath, index=False, encoding="utf-8-sig")

        logger.info("Exported %d rows from '%s' → %s", len(df), table_name, filepath)
        return filepath

    except Exception as exc:
        logger.exception("Export failed for table '%s': %s", table_name, exc)
        raise RuntimeError(f"Export failed: {exc}") from exc


# ------------------------------------------------------------------
# Import
# ------------------------------------------------------------------

def import_csv_to_table(table_name: str, filepath: str) -> dict:
    """
    Read a CSV file and insert non-duplicate rows into *table_name*.

    Returns a summary dict:
        {
            "total_rows":     int,   # rows in CSV (excl. header)
            "inserted":       int,   # new rows inserted
            "duplicates":     int,   # rows skipped as duplicates
            "errors":         list,  # row-level error messages
        }

    Raises:
        ValueError – unknown table or missing required columns.
        RuntimeError – on DB commit failure.
    """
    registry = get_table_registry()
    if table_name not in registry:
        raise ValueError(
            f"Table '{table_name}' not supported. "
            f"Available: {list(registry.keys())}"
        )

    entry       = registry[table_name]
    model       = entry["model"]
    unique_cols = entry["unique_cols"]

    # ---------------------------------------------------------------- Read CSV
    try:
        df = pd.read_csv(filepath, encoding="utf-8-sig", dtype=str)
        df = df.where(pd.notna(df), None)   # convert NaN → None
    except Exception as exc:
        raise ValueError(f"Could not read CSV: {exc}") from exc

    if df.empty:
        return {"total_rows": 0, "inserted": 0, "duplicates": 0, "errors": []}

    # ----------------------------------------- Validate required columns exist
    mapper   = inspect(model)
    db_cols  = {c.key for c in mapper.mapper.columns}
    csv_cols = set(df.columns.tolist())

    # Columns in the CSV that are not in the model are silently ignored.
    # Mandatory columns (non-nullable, no default) must be present.
    missing = _required_columns(model) - csv_cols
    if missing:
        raise ValueError(
            f"CSV is missing required columns for '{table_name}': {missing}"
        )

    # ---------------------------------- Load existing unique-key combinations
    # Build a set of tuples for fast duplicate lookup
    existing_keys: set[tuple] = set()
    valid_unique_cols = [c for c in unique_cols if c in db_cols]

    if valid_unique_cols:
        existing_rows = db.session.execute(db.select(model)).scalars().all()
        for row in existing_rows:
            key = tuple(str(getattr(row, c, "")) for c in valid_unique_cols)
            existing_keys.add(key)

    # ----------------------------------------------------------------- Insert
    inserted   = 0
    duplicates = 0
    errors: list[str] = []

    for idx, csv_row in df.iterrows():
        row_num = int(idx) + 2   # 1-based, +1 for header

        # Duplicate check
        if valid_unique_cols:
            row_key = tuple(str(csv_row.get(c) or "") for c in valid_unique_cols)
            if row_key in existing_keys:
                duplicates += 1
                continue

        # Build ORM instance
        try:
            kwargs = _csv_row_to_kwargs(csv_row, model, db_cols)
            instance = model(**kwargs)
            db.session.add(instance)

            # Track the new key so we catch intra-batch duplicates too
            if valid_unique_cols:
                new_key = tuple(str(kwargs.get(c, "")) for c in valid_unique_cols)
                existing_keys.add(new_key)

            inserted += 1

        except Exception as exc:
            db.session.rollback()
            msg = f"Row {row_num}: {exc}"
            errors.append(msg)
            logger.warning("Import error – %s", msg)

    # ----------------------------------------------------------------- Commit
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise RuntimeError(f"DB commit failed: {exc}") from exc

    total = len(df)
    logger.info(
        "Import '%s': total=%d  inserted=%d  duplicates=%d  errors=%d",
        table_name, total, inserted, duplicates, len(errors),
    )

    return {
        "total_rows": total,
        "inserted":   inserted,
        "duplicates": duplicates,
        "errors":     errors,
    }


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _row_to_dict(instance: Any) -> dict:
    """Convert an ORM instance to a plain dict."""
    mapper = inspect(type(instance))
    result = {}
    for col in mapper.mapper.columns:
        val = getattr(instance, col.key)
        # Serialise dates/datetimes to ISO strings so pandas handles them
        if hasattr(val, "isoformat"):
            val = val.isoformat()
        result[col.key] = val
    return result


def _required_columns(model) -> set:
    """
    Return column names that are non-nullable, have no server default,
    and are not the primary key (which we generate ourselves).
    """
    mapper   = inspect(model)
    required = set()
    for col in mapper.mapper.columns:
        c = col.columns[0]
        if (
            not c.nullable
            and c.default is None
            and c.server_default is None
            and not c.primary_key
            and col.key not in ("created_at", "updated_at")
        ):
            required.add(col.key)
    return required


def _csv_row_to_kwargs(csv_row: pd.Series, model, db_cols: set) -> dict:
    """
    Convert a pandas Series (one CSV row) to a dict of kwargs suitable for
    passing to the ORM model constructor.

    • Skips 'id', 'created_at', 'updated_at' – generated server-side.
    • Skips columns not present in the model.
    • Converts empty strings to None.
    """
    import uuid as _uuid

    SKIP = {"id", "created_at", "updated_at"}
    kwargs: dict = {}

    for col_name in db_cols:
        if col_name in SKIP:
            continue
        if col_name not in csv_row.index:
            continue
        val = csv_row[col_name]
        # Treat empty / whitespace strings as None
        if isinstance(val, str) and val.strip() == "":
            val = None
        kwargs[col_name] = val

    # Always generate a fresh UUID for the primary key
    kwargs["id"] = str(_uuid.uuid4())
    return kwargs


# ------------------------------------------------------------------
# Utility: list available tables
# ------------------------------------------------------------------

def available_tables() -> list[str]:
    """Return the names of all tables that support CSV import/export."""
    return list(get_table_registry().keys())
