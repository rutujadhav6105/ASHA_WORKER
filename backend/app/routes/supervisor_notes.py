"""Supervisor notes route."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db, sync_model_to_csv
from app.models.models import SupervisorNote
from app.utils.auth_utils import get_current_user

router = APIRouter()

class NoteCreate(BaseModel):
    asha_worker_id: Optional[int] = None
    title: str
    note: str

@router.get("/supervisor-notes")
def list_notes(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role.value == "asha_worker":
        notes = db.query(SupervisorNote).filter(SupervisorNote.asha_worker_id == current_user.id).all()
    else:
        notes = db.query(SupervisorNote).filter(SupervisorNote.supervisor_id == current_user.id).all()
    return {"success": True, "notes": [
        {"id": n.id, "title": n.title, "note": n.note, "is_acknowledged": n.is_acknowledged,
         "created_at": str(n.created_at)}
        for n in notes
    ]}

@router.post("/supervisor-notes", status_code=201)
def create_note(body: NoteCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    n = SupervisorNote(
        supervisor_id=current_user.id,
        asha_worker_id=body.asha_worker_id,
        title=body.title,
        note=body.note,
        created_by=current_user.id,
    )
    db.add(n); db.commit(); db.refresh(n)
    sync_model_to_csv(n)
    return {"success": True, "id": n.id}
