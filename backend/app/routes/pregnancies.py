"""Pregnancies route with CSV sync."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db, sync_model_to_csv
from app.models.models import Pregnancy, RiskLevelEnum
from app.utils.auth_utils import get_current_user

router = APIRouter()

class PregnancyCreate(BaseModel):
    patient_id: int
    lmp_date: Optional[str] = None
    gestational_week: Optional[int] = None
    hemoglobin: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    weight_kg: Optional[float] = None
    previous_complications: Optional[bool] = False
    gravida: Optional[int] = 1
    para: Optional[int] = 0
    risk_level: Optional[str] = "low"
    notes: Optional[str] = None

@router.get("/pregnancies")
def list_pregnancies(
    page: int = Query(1, ge=1),
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(Pregnancy).filter(Pregnancy.status == "active")
    if risk_level:
        q = q.filter(Pregnancy.risk_level == risk_level)
    total = q.count()
    items = q.offset((page - 1) * 20).limit(20).all()
    return {"success": True, "total": total, "pregnancies": [
        {"id": p.id, "patient_id": p.patient_id, "gestational_week": p.gestational_week,
         "risk_level": p.risk_level.value if p.risk_level else "low",
         "hemoglobin": p.hemoglobin, "systolic_bp": p.systolic_bp,
         "risk_score": p.risk_score, "status": p.status}
        for p in items
    ]}

@router.post("/pregnancies", status_code=201)
def create_pregnancy(body: PregnancyCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    data = body.dict(exclude_none=True)
    risk = data.pop("risk_level", "low")
    p = Pregnancy(**data, created_by=current_user.id, risk_level=RiskLevelEnum(risk))
    db.add(p); db.commit(); db.refresh(p)
    sync_model_to_csv(p)
    return {"success": True, "id": p.id}

@router.put("/pregnancies/{pid}")
def update_pregnancy(pid: int, body: PregnancyCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    p = db.query(Pregnancy).filter(Pregnancy.id == pid).first()
    if not p: raise HTTPException(404, "Not found")
    for k, v in body.dict(exclude_none=True).items():
        if k == "risk_level": p.risk_level = RiskLevelEnum(v)
        else: setattr(p, k, v)
    db.commit(); db.refresh(p); sync_model_to_csv(p)
    return {"success": True}

@router.delete("/pregnancies/{pid}")
def delete_pregnancy(pid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    p = db.query(Pregnancy).filter(Pregnancy.id == pid).first()
    if not p: raise HTTPException(404, "Not found")
    db.delete(p); db.commit()
    return {"success": True}
