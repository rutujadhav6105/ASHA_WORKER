"""
Machine Learning prediction endpoints.
Models are trained with scikit-learn RandomForest and saved as pickle files.
"""

import os
import pickle
import numpy as np
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.utils.auth_utils import get_current_user

router = APIRouter()

ML_DIR = Path(__file__).resolve().parent.parent / "ml"
ML_DIR.mkdir(parents=True, exist_ok=True)


# ── Model loader (lazy) ───────────────────────────────────────────────────────
def _load_model(name: str):
    path = ML_DIR / f"{name}.pkl"
    if path.exists():
        with open(path, "rb") as f:
            return pickle.load(f)
    return None


# ── Schemas ───────────────────────────────────────────────────────────────────
class PregnancyRiskInput(BaseModel):
    age: float
    hemoglobin: float
    systolic_bp: float
    diastolic_bp: float
    previous_complications: bool
    gestational_week: int
    gravida: Optional[int] = 1
    weight_kg: Optional[float] = None


class NutritionRiskInput(BaseModel):
    age_months: float
    weight_kg: float
    height_cm: float


class MissedVisitInput(BaseModel):
    patient_id: int
    days_since_last_visit: int
    total_visits_missed: int
    distance_km: float


# ── Pregnancy Risk Prediction ─────────────────────────────────────────────────
@router.post("/ml/pregnancy-risk")
def predict_pregnancy_risk(
    body: PregnancyRiskInput,
    _=Depends(get_current_user),
):
    """
    Predict pregnancy risk using a trained RandomForest model.
    Falls back to rule-based logic if model file not found.
    """
    model = _load_model("pregnancy_risk_model")

    if model:
        features = np.array([[
            body.age,
            body.hemoglobin,
            body.systolic_bp,
            body.diastolic_bp,
            int(body.previous_complications),
            body.gestational_week,
            body.gravida or 1,
            body.weight_kg or 55.0,
        ]])
        prob = model.predict_proba(features)[0]
        risk_score = float(prob[1]) if len(prob) > 1 else 0.0
    else:
        # Rule-based fallback
        risk_score = _rule_based_pregnancy_risk(body)

    if risk_score >= 0.7:
        risk_level = "high"
    elif risk_score >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "success": True,
        "prediction": {
            "risk_score":  round(risk_score, 4),
            "risk_level":  risk_level,
            "confidence":  round(risk_score if risk_level == "high" else 1 - risk_score, 2),
            "risk_factors": _identify_pregnancy_risk_factors(body),
            "recommendations": _pregnancy_recommendations(risk_level),
        },
    }


def _rule_based_pregnancy_risk(body: PregnancyRiskInput) -> float:
    score = 0.0
    if body.age < 18 or body.age > 35:   score += 0.2
    if body.hemoglobin < 8:              score += 0.25
    elif body.hemoglobin < 10:           score += 0.15
    if body.systolic_bp > 140:           score += 0.25
    elif body.systolic_bp > 130:         score += 0.15
    if body.diastolic_bp > 90:           score += 0.15
    if body.previous_complications:      score += 0.2
    if body.gestational_week > 36:       score += 0.1
    return min(score, 1.0)


def _identify_pregnancy_risk_factors(body: PregnancyRiskInput) -> list:
    factors = []
    if body.hemoglobin < 10:
        factors.append("Anemia (low hemoglobin)")
    if body.systolic_bp > 130 or body.diastolic_bp > 85:
        factors.append("Elevated blood pressure")
    if body.age < 18:
        factors.append("Young maternal age (< 18)")
    if body.age > 35:
        factors.append("Advanced maternal age (> 35)")
    if body.previous_complications:
        factors.append("Previous obstetric complications")
    return factors


def _pregnancy_recommendations(level: str) -> list:
    base = ["Regular ANC visits", "Iron & Folic Acid supplementation"]
    if level == "high":
        return base + ["Immediate referral to CHC/PHC", "Emergency contact on file", "Weekly monitoring"]
    if level == "medium":
        return base + ["Bi-weekly visit", "Diet counselling", "BP monitoring"]
    return base + ["Monthly ANC visit", "Nutrition advice"]


# ── Nutrition Risk Prediction ─────────────────────────────────────────────────
@router.post("/ml/nutrition-risk")
def predict_nutrition_risk(
    body: NutritionRiskInput,
    _=Depends(get_current_user),
):
    """
    Classify child nutrition using WHO Z-score approximation.
    Falls back to rule-based if model not found.
    """
    model = _load_model("nutrition_risk_model")

    if model:
        features = np.array([[body.age_months, body.weight_kg, body.height_cm]])
        prob = model.predict_proba(features)[0]
        risk_score = float(max(prob))
        predicted_class = model.predict(features)[0]
    else:
        predicted_class, risk_score = _rule_based_nutrition(body)

    labels = {0: "Normal", 1: "MAM", 2: "SAM"}
    status_label = labels.get(predicted_class, "Unknown")

    return {
        "success": True,
        "prediction": {
            "nutrition_status":   status_label,
            "risk_score":         round(risk_score, 4),
            "age_months":         body.age_months,
            "weight_kg":          body.weight_kg,
            "height_cm":          body.height_cm,
            "wfh_z_score":        round(_wfh_z(body.weight_kg, body.height_cm), 2),
            "recommendations":    _nutrition_recommendations(status_label),
        },
    }


def _rule_based_nutrition(body: NutritionRiskInput):
    wfh_z = _wfh_z(body.weight_kg, body.height_cm)
    if wfh_z <= -3:
        return 2, 0.85   # SAM
    if wfh_z <= -2:
        return 1, 0.70   # MAM
    return 0, 0.90       # Normal


def _wfh_z(weight: float, height: float) -> float:
    """Simplified weight-for-height Z-score approximation."""
    bmi = weight / ((height / 100) ** 2)
    return (bmi - 15.5) / 2.5


def _nutrition_recommendations(status: str) -> list:
    if status == "SAM":
        return [
            "Immediate therapeutic feeding (RUTF)",
            "Refer to NRC (Nutrition Rehabilitation Centre)",
            "Medical evaluation for infections",
            "Weekly weight monitoring",
        ]
    if status == "MAM":
        return [
            "Supplementary nutrition programme (POSHAN)",
            "High-energy, protein-rich diet",
            "Bi-weekly growth monitoring",
            "Vitamin A & zinc supplementation",
        ]
    return [
        "Continue balanced diet",
        "Monthly growth monitoring",
        "Breastfeeding support if < 6 months",
    ]


# ── Missed Visit Prediction ───────────────────────────────────────────────────
@router.post("/ml/missed-visit")
def predict_missed_visit(
    body: MissedVisitInput,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Predict probability that a patient will miss their next scheduled visit."""
    model = _load_model("missed_visit_model")

    if model:
        features = np.array([[
            body.days_since_last_visit,
            body.total_visits_missed,
            body.distance_km,
        ]])
        prob = float(model.predict_proba(features)[0][1])
    else:
        # Rule-based fallback
        prob = _rule_based_missed_visit(body)

    will_miss = prob >= 0.5
    return {
        "success": True,
        "prediction": {
            "patient_id":      body.patient_id,
            "miss_probability": round(prob, 4),
            "likely_to_miss":  will_miss,
            "risk_level":      "high" if prob >= 0.7 else "medium" if prob >= 0.5 else "low",
            "interventions":   _missed_visit_interventions(prob),
        },
    }


def _rule_based_missed_visit(body: MissedVisitInput) -> float:
    score = 0.0
    if body.days_since_last_visit > 60: score += 0.3
    elif body.days_since_last_visit > 30: score += 0.15
    if body.total_visits_missed >= 3: score += 0.3
    elif body.total_visits_missed >= 1: score += 0.15
    if body.distance_km > 5: score += 0.2
    elif body.distance_km > 2: score += 0.1
    return min(score, 1.0)


def _missed_visit_interventions(prob: float) -> list:
    if prob >= 0.7:
        return ["Phone call reminder", "Home visit by ASHA", "Supervisor follow-up", "SMS alert"]
    if prob >= 0.5:
        return ["SMS reminder 2 days before", "Phone call on visit day"]
    return ["Standard appointment reminder"]


# ── Model Retrain Endpoint ────────────────────────────────────────────────────
@router.post("/ml/retrain")
def retrain_models(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrain all ML models from the PostgreSQL database.
    Only admins and supervisors can trigger this.
    """
    if current_user.role.value == "asha_worker":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    from app.ml.trainer import train_all_models
    results = train_all_models(db)
    return {"success": True, "results": results}
