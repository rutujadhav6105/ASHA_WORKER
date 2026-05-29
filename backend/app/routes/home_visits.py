"""Home Visits route."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db, sync_model_to_csv
from app.models.models import HomeVisit
from app.utils.auth_utils import get_current_user

router = APIRouter()

class HomeVisitCreate(BaseModel):
    patient_id: int
    visit_date: str
    visit_type: Optional[str] = "general"
    status: Optional[str] = "completed"
    findings: Optional[str] = None
    actions_taken: Optional[str] = None
    referral_made: Optional[bool] = False
    referral_to: Optional[str] = None
    next_visit_date: Optional[str] = None
    missed_reason: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    notes: Optional[str] = None

@router.get("/home-visits")
def list_visits(page: int = Query(1, ge=1), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    q = db.query(HomeVisit)
    if current_user.role.value == "asha_worker":
        q = q.filter(HomeVisit.asha_worker_id == current_user.id)
    total = q.count()
    items = q.offset((page - 1) * 20).limit(20).all()
    return {"success": True, "total": total, "visits": [
        {"id": v.id, "patient_id": v.patient_id, "visit_date": str(v.visit_date),
         "visit_type": v.visit_type, "status": v.status, "referral_made": v.referral_made}
        for v in items
    ]}

@router.post("/home-visits", status_code=201)
def create_visit(body: HomeVisitCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    v = HomeVisit(
        patient_id=body.patient_id,
        asha_worker_id=current_user.id,
        visit_date=datetime.fromisoformat(body.visit_date),
        visit_type=body.visit_type,
        status=body.status,
        findings=body.findings,
        actions_taken=body.actions_taken,
        referral_made=body.referral_made,
        referral_to=body.referral_to,
        missed_reason=body.missed_reason,
        gps_lat=body.gps_lat,
        gps_lng=body.gps_lng,
        notes=body.notes,
        created_by=current_user.id,
    )
    if body.next_visit_date:
        v.next_visit_date = datetime.fromisoformat(body.next_visit_date)
    db.add(v); db.commit(); db.refresh(v)
    sync_model_to_csv(v)
    return {"success": True, "id": v.id}

@router.put("/home-visits/{vid}")
def update_visit(vid: int, body: HomeVisitCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    v = db.query(HomeVisit).filter(HomeVisit.id == vid).first()
    if not v: raise HTTPException(404, "Not found")
    for k, val in body.dict(exclude_none=True).items():
        setattr(v, k, val)
    db.commit(); db.refresh(v); sync_model_to_csv(v)
    return {"success": True}

@router.delete("/home-visits/{vid}")
def delete_visit(vid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    v = db.query(HomeVisit).filter(HomeVisit.id == vid).first()
    if not v: raise HTTPException(404, "Not found")
    db.delete(v); db.commit()
    return {"success": True}
