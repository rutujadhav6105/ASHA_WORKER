"""Patient CRUD with CSV sync, pagination, search, and village filter."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db, sync_model_to_csv, delete_csv_row
from app.models.models import Patient, RiskLevelEnum
from app.utils.auth_utils import get_current_user

router = APIRouter()


class PatientCreate(BaseModel):
    full_name: str
    age: int
    gender: str
    mobile: Optional[str] = None
    address: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    aadhar_number: Optional[str] = None
    abha_id: Optional[str] = None
    family_id: Optional[int] = None
    risk_level: Optional[str] = "low"
    blood_group: Optional[str] = None
    notes: Optional[str] = None


class PatientUpdate(PatientCreate):
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None


def _serialize(p: Patient) -> dict:
    return {
        "id": p.id,
        "full_name": p.full_name,
        "age": p.age,
        "gender": p.gender,
        "mobile": p.mobile,
        "address": p.address,
        "village": p.village,
        "district": p.district,
        "risk_level": p.risk_level.value if p.risk_level else "low",
        "blood_group": p.blood_group,
        "aadhar_number": p.aadhar_number,
        "abha_id": p.abha_id,
        "family_id": p.family_id,
        "notes": p.notes,
        "created_at": str(p.created_at) if p.created_at else None,
        "updated_at": str(p.updated_at) if p.updated_at else None,
    }


@router.get("/patients")
def list_patients(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    village: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(Patient)

    # ASHA workers see only their village
    if current_user.role.value == "asha_worker" and current_user.village:
        q = q.filter(Patient.village == current_user.village)

    if search:
        q = q.filter(
            or_(
                Patient.full_name.ilike(f"%{search}%"),
                Patient.mobile.ilike(f"%{search}%"),
                Patient.aadhar_number.ilike(f"%{search}%"),
            )
        )
    if village:
        q = q.filter(Patient.village == village)
    if risk_level:
        q = q.filter(Patient.risk_level == risk_level)

    total = q.count()
    patients = q.offset((page - 1) * limit).limit(limit).all()

    return {
        "success": True,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "patients": [_serialize(p) for p in patients],
    }


@router.get("/patients/{patient_id}")
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"success": True, "patient": _serialize(p)}


@router.post("/patients", status_code=201)
def create_patient(
    body: PatientCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    p = Patient(
        **body.dict(exclude_none=True),
        asha_worker_id=current_user.id,
        created_by=current_user.id,
    )
    if body.risk_level:
        p.risk_level = RiskLevelEnum(body.risk_level)

    db.add(p)
    db.commit()
    db.refresh(p)
    sync_model_to_csv(p)   # ← auto CSV sync
    return {"success": True, "patient": _serialize(p)}


@router.put("/patients/{patient_id}")
def update_patient(
    patient_id: int,
    body: PatientUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    for field, value in body.dict(exclude_none=True).items():
        if field == "risk_level" and value:
            setattr(p, field, RiskLevelEnum(value))
        else:
            setattr(p, field, value)

    db.commit()
    db.refresh(p)
    sync_model_to_csv(p)   # ← auto CSV sync on update
    return {"success": True, "patient": _serialize(p)}


@router.delete("/patients/{patient_id}")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(p)
    db.commit()
    delete_csv_row("patients", patient_id)   # ← remove from CSV
    return {"success": True, "message": "Patient deleted"}
