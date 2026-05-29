"""
Daily CSV backup service.
Runs at 2 AM via APScheduler.
Exports all tables to csv_exports/backups/<timestamp>/<table>.csv
"""

import shutil
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

CSV_DIR     = Path(__file__).resolve().parent.parent.parent / "csv_exports"
BACKUP_DIR  = CSV_DIR / "backups"


async def run_daily_backup():
    """
    Copy all current CSVs to a timestamped backup folder.
    Called by APScheduler every day at 2 AM.
    """
    timestamp   = datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_path = BACKUP_DIR / timestamp
    backup_path.mkdir(parents=True, exist_ok=True)

    csv_files = list(CSV_DIR.glob("*.csv"))
    if not csv_files:
        logger.info("No CSV files to back up.")
        return

    for csv_file in csv_files:
        dest = backup_path / csv_file.name
        shutil.copy2(csv_file, dest)

    logger.info(f"Backup completed: {len(csv_files)} files → {backup_path}")

    # Keep only last 30 backups
    _prune_old_backups(keep=30)


def _prune_old_backups(keep: int = 30):
    """Delete oldest backup folders beyond the keep limit."""
    folders = sorted(BACKUP_DIR.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
    for old in folders[keep:]:
        if old.is_dir():
            shutil.rmtree(old)
            logger.info(f"Pruned old backup: {old.name}")


def rebuild_all_csvs_from_db():
    """
    On startup, if a CSV is missing but data exists in DB, rebuild it.
    Call from lifespan if needed.
    """
    from app.database import SessionLocal, rebuild_csv_from_db
    from app.models.models import (
        User, Patient, Pregnancy, ANCVisit, Immunization,
        HomeVisit, MedicineStock, Alert, Report,
        TrainingRecord, Village, SupervisorNote
    )

    db = SessionLocal()
    table_model_pairs = [
        ("users",            User),
        ("patients",         Patient),
        ("pregnancies",      Pregnancy),
        ("anc_visits",       ANCVisit),
        ("immunizations",    Immunization),
        ("home_visits",      HomeVisit),
        ("medicine_stock",   MedicineStock),
        ("alerts",           Alert),
        ("reports",          Report),
        ("training_records", TrainingRecord),
        ("villages",         Village),
        ("supervisor_notes", SupervisorNote),
    ]

    try:
        for table_name, Model in table_model_pairs:
            csv_path = CSV_DIR / f"{table_name}.csv"
            if not csv_path.exists():
                logger.info(f"Rebuilding missing CSV: {table_name}.csv")
                rebuild_csv_from_db(db, Model, table_name)
    finally:
        db.close()
