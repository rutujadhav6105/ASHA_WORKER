"""
ML Model Trainer
================
Trains RandomForest models from live PostgreSQL data and saves as pickle files.
Call train_all_models(db) to retrain.
"""

import pickle
import numpy as np
from pathlib import Path
from sqlalchemy.orm import Session

ML_DIR = Path(__file__).resolve().parent
ML_DIR.mkdir(parents=True, exist_ok=True)


def train_all_models(db: Session) -> dict:
    results = {}
    results["pregnancy_risk"] = _train_pregnancy_risk(db)
    results["nutrition_risk"] = _train_nutrition_risk(db)
    results["missed_visit"]   = _train_missed_visit(db)
    return results


# ── Pregnancy Risk Model ──────────────────────────────────────────────────────
def _train_pregnancy_risk(db: Session) -> str:
    try:
        from sklearn.ensemble import RandomForestClassifier
        from app.models.models import Pregnancy, RiskLevelEnum

        rows = db.query(Pregnancy).filter(Pregnancy.hemoglobin.isnot(None)).all()

        if len(rows) < 20:
            return _save_dummy_pregnancy_model()

        X, y = [], []
        for r in rows:
            X.append([
                r.patient.age if r.patient else 25,
                r.hemoglobin or 10.0,
                r.systolic_bp or 120.0,
                r.diastolic_bp or 80.0,
                int(r.previous_complications or False),
                r.gestational_week or 20,
                r.gravida or 1,
                r.patient.weight_kg if hasattr(r.patient, 'weight_kg') else 55.0,
            ])
            label = 1 if r.risk_level == RiskLevelEnum.high else 0
            y.append(label)

        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X, y)

        path = ML_DIR / "pregnancy_risk_model.pkl"
        with open(path, "wb") as f:
            pickle.dump(clf, f)

        return f"Trained on {len(rows)} records. Saved to {path}"

    except Exception as e:
        return f"Training failed: {str(e)}. Using rule-based fallback."


def _save_dummy_pregnancy_model() -> str:
    """Save a model trained on synthetic data as a placeholder."""
    try:
        from sklearn.ensemble import RandomForestClassifier

        np.random.seed(42)
        n = 500
        X = np.column_stack([
            np.random.uniform(15, 45, n),   # age
            np.random.uniform(6, 14, n),    # hemoglobin
            np.random.uniform(90, 160, n),  # systolic BP
            np.random.uniform(60, 100, n),  # diastolic BP
            np.random.randint(0, 2, n),     # complications
            np.random.randint(4, 40, n),    # gestational week
            np.random.randint(1, 5, n),     # gravida
            np.random.uniform(40, 90, n),   # weight
        ])
        # Create synthetic labels
        y = (
            (X[:, 1] < 9).astype(int) |
            (X[:, 2] > 140).astype(int) |
            (X[:, 4] == 1).astype(int)
        ).clip(0, 1)

        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X, y)

        path = ML_DIR / "pregnancy_risk_model.pkl"
        with open(path, "wb") as f:
            pickle.dump(clf, f)

        return f"Saved synthetic model to {path}"
    except Exception as e:
        return f"Dummy model failed: {e}"


# ── Nutrition Risk Model ──────────────────────────────────────────────────────
def _train_nutrition_risk(db: Session) -> str:
    try:
        from sklearn.ensemble import RandomForestClassifier
        from app.models.models import Immunization

        rows = db.query(Immunization).filter(
            Immunization.weight_kg.isnot(None),
            Immunization.height_cm.isnot(None),
        ).all()

        if len(rows) < 20:
            return _save_dummy_nutrition_model()

        X, y = [], []
        label_map = {"Normal": 0, "MAM": 1, "SAM": 2}

        for r in rows:
            if r.nutrition_status not in label_map:
                continue
            X.append([r.age_months or 12, r.weight_kg, r.height_cm])
            y.append(label_map[r.nutrition_status])

        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X, y)

        path = ML_DIR / "nutrition_risk_model.pkl"
        with open(path, "wb") as f:
            pickle.dump(clf, f)

        return f"Trained on {len(X)} records."

    except Exception as e:
        return f"Training failed: {str(e)}."


def _save_dummy_nutrition_model() -> str:
    try:
        from sklearn.ensemble import RandomForestClassifier

        np.random.seed(99)
        n = 600
        ages   = np.random.uniform(0, 60, n)
        weights = np.random.uniform(2, 20, n)
        heights = np.random.uniform(45, 110, n)
        X = np.column_stack([ages, weights, heights])

        # BMI-based labels
        bmi = weights / ((heights / 100) ** 2)
        y = np.where(bmi < 13, 2, np.where(bmi < 15, 1, 0))

        clf = RandomForestClassifier(n_estimators=100, random_state=99)
        clf.fit(X, y)

        path = ML_DIR / "nutrition_risk_model.pkl"
        with open(path, "wb") as f:
            pickle.dump(clf, f)
        return f"Saved synthetic nutrition model."
    except Exception as e:
        return f"Failed: {e}"


# ── Missed Visit Model ────────────────────────────────────────────────────────
def _train_missed_visit(db: Session) -> str:
    try:
        from sklearn.ensemble import RandomForestClassifier
        from app.models.models import HomeVisit
        from datetime import datetime

        rows = db.query(HomeVisit).all()
        if len(rows) < 20:
            return _save_dummy_missed_model()

        X, y = [], []
        for r in rows:
            days = (datetime.utcnow() - r.created_at).days if r.created_at else 30
            X.append([days, 0, 2.0])  # simplified features
            y.append(1 if r.status == "missed" else 0)

        clf = RandomForestClassifier(n_estimators=100, random_state=7)
        clf.fit(X, y)

        path = ML_DIR / "missed_visit_model.pkl"
        with open(path, "wb") as f:
            pickle.dump(clf, f)
        return f"Trained on {len(rows)} visit records."

    except Exception as e:
        return f"Training failed: {str(e)}."


def _save_dummy_missed_model() -> str:
    try:
        from sklearn.ensemble import RandomForestClassifier

        np.random.seed(5)
        n = 400
        X = np.column_stack([
            np.random.randint(1, 120, n),   # days since last visit
            np.random.randint(0, 5, n),     # total missed
            np.random.uniform(0, 10, n),    # distance km
        ])
        y = (
            (X[:, 0] > 45).astype(int) |
            (X[:, 1] >= 2).astype(int)
        ).clip(0, 1)

        clf = RandomForestClassifier(n_estimators=100, random_state=5)
        clf.fit(X, y)

        path = ML_DIR / "missed_visit_model.pkl"
        with open(path, "wb") as f:
            pickle.dump(clf, f)
        return "Saved synthetic missed-visit model."
    except Exception as e:
        return f"Failed: {e}"
