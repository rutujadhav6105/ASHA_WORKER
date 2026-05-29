"""Training records route."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.database import get_db, sync_model_to_csv
from app.models.models import TrainingRecord
from app.utils.auth_utils import get_current_user

router = APIRouter()

class TrainingCreate(BaseModel):
    training_name: str
    training_date: str
    conducted_by: Optional[str] = None
    topics_covered: Optional[List[str]] = None
    score: Optional[float] = None
    notes: Optional[str] = None

@router.get("/training")
def list_training(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    records = db.query(TrainingRecord).filter(TrainingRecord.asha_worker_id == current_user.id).all()
    return {"success": True, "records": [
        {"id": r.id, "training_name": r.training_name, "training_date": str(r.training_date),
         "conducted_by": r.conducted_by, "score": r.score}
        for r in records
    ]}

@router.post("/training", status_code=201)
def create_training(body: TrainingCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    r = TrainingRecord(
        asha_worker_id=current_user.id,
        training_name=body.training_name,
        training_date=datetime.fromisoformat(body.training_date),
        conducted_by=body.conducted_by,
        topics_covered=body.topics_covered,
        score=body.score,
        notes=body.notes,
        created_by=current_user.id,
    )
    db.add(r); db.commit(); db.refresh(r)
    sync_model_to_csv(r)
    return {"success": True, "id": r.id}
