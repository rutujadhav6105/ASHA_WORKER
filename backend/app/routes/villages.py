"""Villages route."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Village
from app.utils.auth_utils import get_current_user

router = APIRouter()

@router.get("/villages")
def list_villages(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(Village).all()
    return {"success": True, "villages": [
        {"id": v.id, "name": v.name, "district": v.district, "population": v.population, "health_score": v.health_score}
        for v in items
    ]}

@router.get("/villages/{name}/health")
def village_health(name: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from app.models.models import Patient, RiskLevelEnum
    total = db.query(Patient).filter(Patient.village == name).count()
    high_risk = db.query(Patient).filter(Patient.village == name, Patient.risk_level == RiskLevelEnum.high).count()
    return {"success": True, "village": name, "total_patients": total, "high_risk": high_risk}
