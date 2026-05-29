"""Medicine stock route."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db, sync_model_to_csv
from app.models.models import MedicineStock
from app.utils.auth_utils import get_current_user

router = APIRouter()

class MedicineUpdate(BaseModel):
    medicine_name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    current_stock: Optional[int] = None
    minimum_stock: Optional[int] = None
    expiry_date: Optional[str] = None
    batch_number: Optional[str] = None
    supplier: Optional[str] = None
    village: Optional[str] = None

@router.get("/medicine-stock")
def list_medicines(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(MedicineStock).all()
    return {"success": True, "stock": [
        {"id": m.id, "medicine_name": m.medicine_name, "category": m.category,
         "current_stock": m.current_stock, "minimum_stock": m.minimum_stock,
         "is_low_stock": m.is_low_stock, "expiry_date": str(m.expiry_date) if m.expiry_date else None,
         "unit": m.unit}
        for m in items
    ]}

@router.get("/medicine-stock/low-stock")
def low_stock(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(MedicineStock).filter(MedicineStock.is_low_stock == True).all()
    return {"success": True, "count": len(items), "items": [
        {"id": m.id, "medicine_name": m.medicine_name, "current_stock": m.current_stock, "minimum_stock": m.minimum_stock}
        for m in items
    ]}

@router.post("/medicine-stock", status_code=201)
def create_medicine(body: MedicineUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from datetime import datetime
    m = MedicineStock(
        medicine_name=body.medicine_name,
        category=body.category,
        unit=body.unit,
        current_stock=body.current_stock or 0,
        minimum_stock=body.minimum_stock or 10,
        batch_number=body.batch_number,
        supplier=body.supplier,
        village=body.village,
        created_by=current_user.id,
    )
    if body.expiry_date:
        m.expiry_date = datetime.fromisoformat(body.expiry_date)
    m.is_low_stock = (m.current_stock or 0) <= (m.minimum_stock or 10)
    db.add(m); db.commit(); db.refresh(m)
    sync_model_to_csv(m)
    return {"success": True, "id": m.id}

@router.put("/medicine-stock/{mid}")
def update_medicine(mid: int, body: MedicineUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    m = db.query(MedicineStock).filter(MedicineStock.id == mid).first()
    if not m: raise HTTPException(404, "Not found")
    for k, v in body.dict(exclude_none=True).items():
        setattr(m, k, v)
    m.is_low_stock = (m.current_stock or 0) <= (m.minimum_stock or 10)
    db.commit(); db.refresh(m); sync_model_to_csv(m)
    return {"success": True}

@router.delete("/medicine-stock/{mid}")
def delete_medicine(mid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    m = db.query(MedicineStock).filter(MedicineStock.id == mid).first()
    if not m: raise HTTPException(404, "Not found")
    db.delete(m); db.commit()
    return {"success": True}
