"""Immunization route."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from app.database import get_db, sync_model_to_csv
from app.models.models import Immunization
from app.utils.auth_utils import get_current_user

router = APIRouter()

class ImmunizationCreate(BaseModel):
    patient_id: int
    child_name: str
    date_of_birth: str
    gender: str
    mother_name: Optional[str] = None
    father_name: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    muac_cm: Optional[float] = None
    nutrition_status: Optional[str] = "Normal"
    village: Optional[str] = None
    vaccine_records: Optional[List[dict]] = None
    due_vaccines: Optional[List[str]] = None
    notes: Optional[str] = None

@router.get("/immunization")
def list_immunization(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    records = db.query(Immunization).all()
    return {"success": True, "records": [
        {"id": r.id, "child_name": r.child_name, "date_of_birth": str(r.date_of_birth),
         "gender": r.gender, "village": r.village, "nutrition_status": r.nutrition_status,
         "next_due_date": str(r.next_due_date) if r.next_due_date else None,
         "due_vaccines": r.due_vaccines}
        for r in records
    ]}

@router.get("/immunization/due")
def due_vaccinations(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    cutoff = datetime.utcnow() + timedelta(days=7)
    records = db.query(Immunization).filter(Immunization.next_due_date <= cutoff).all()
    return {"success": True, "count": len(records), "records": [
        {"id": r.id, "child_name": r.child_name, "next_due_date": str(r.next_due_date)}
        for r in records
    ]}

@router.post("/immunization", status_code=201)
def create_immunization(body: ImmunizationCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    r = Immunization(
        patient_id=body.patient_id,
        child_name=body.child_name,
        date_of_birth=datetime.fromisoformat(body.date_of_birth),
        gender=body.gender,
        mother_name=body.mother_name,
        father_name=body.father_name,
        weight_kg=body.weight_kg,
        height_cm=body.height_cm,
        muac_cm=body.muac_cm,
        nutrition_status=body.nutrition_status,
        village=body.village,
        vaccine_records=body.vaccine_records or [],
        due_vaccines=body.due_vaccines or [],
        notes=body.notes,
        created_by=current_user.id,
    )
    db.add(r); db.commit(); db.refresh(r)
    sync_model_to_csv(r)
    return {"success": True, "id": r.id}

@router.put("/immunization/{rid}")
def update_immunization(rid: int, body: ImmunizationCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    r = db.query(Immunization).filter(Immunization.id == rid).first()
    if not r: raise HTTPException(404, "Not found")
    for k, v in body.dict(exclude_none=True).items():
        setattr(r, k, v)
    db.commit(); db.refresh(r); sync_model_to_csv(r)
    return {"success": True}

@router.delete("/immunization/{rid}")
def delete_immunization(rid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    r = db.query(Immunization).filter(Immunization.id == rid).first()
    if not r: raise HTTPException(404, "Not found")
    db.delete(r); db.commit()
    return {"success": True}
