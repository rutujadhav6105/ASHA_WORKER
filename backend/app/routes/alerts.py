"""Alerts route."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db, sync_model_to_csv
from app.models.models import Alert
from app.utils.auth_utils import get_current_user

router = APIRouter()

@router.get("/alerts")
def list_alerts(unread: Optional[bool] = Query(False), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    q = db.query(Alert).filter(Alert.target_user_id == current_user.id)
    if unread: q = q.filter(Alert.is_read == False)
    items = q.order_by(Alert.created_at.desc()).limit(50).all()
    return {"success": True, "alerts": [
        {"id": a.id, "title": a.title, "message": a.message, "severity": a.severity,
         "is_read": a.is_read, "created_at": str(a.created_at)}
        for a in items
    ]}

@router.put("/alerts/{aid}/read")
def mark_read(aid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    a = db.query(Alert).filter(Alert.id == aid).first()
    if not a: raise HTTPException(404, "Not found")
    a.is_read = True
    db.commit()
    return {"success": True}
