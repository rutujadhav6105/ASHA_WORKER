import logging
from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.models import MedicineStock
from app.utils.response import error_response, success_response


def _parse_stock_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        parsed = value.strip()
        if parsed == "":
            return None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(parsed, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(parsed)
        except ValueError:
            pass
    raise ValueError("Invalid date format")


def _parse_int(value, default=0):
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValueError("Boolean is not a valid numeric value")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned == "":
            return default
        return int(cleaned)
    return int(value)

logger = logging.getLogger(__name__)

stock_bp = Blueprint("stock", __name__)


def _serialize_stock(item: MedicineStock) -> dict:
    return {
        "id": item.id,
        "medicine_name": item.medicine_name,
        "category": item.category,
        "unit": item.unit,
        "current_stock": item.current_stock,
        "minimum_stock": item.minimum_stock,
        "batch_number": item.batch_number,
        "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
        "supplier": item.supplier,
        "village": item.village,
        "is_low_stock": item.is_low_stock,
    }


@stock_bp.get("/medicine-stock")
@stock_bp.get("/stock")
@jwt_required()
def list_stock():
    query = MedicineStock.query.order_by(MedicineStock.id.desc())
    items = query.all()
    return success_response(data=[_serialize_stock(item) for item in items])


@stock_bp.get("/medicine-stock/low-stock")
@stock_bp.get("/stock/low-stock")
@jwt_required()
def low_stock():
    items = MedicineStock.query.filter_by(is_low_stock=True).all()
    return success_response(data=[_serialize_stock(item) for item in items])


@stock_bp.get("/medicine-stock/<int:stock_id>")
@stock_bp.get("/stock/<int:stock_id>")
@jwt_required()
def get_stock(stock_id: int):
    item = MedicineStock.query.get(stock_id)
    if not item:
        return error_response("Stock item not found", 404)
    return success_response(data=_serialize_stock(item))


@stock_bp.post("/medicine-stock")
@stock_bp.post("/stock")
@jwt_required()
def create_stock():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return error_response("Invalid request payload", 400)

    medicine_name = payload.get("medicine_name") or payload.get("name")
    if not medicine_name or str(medicine_name).strip() == "":
        return error_response("medicine_name is required", 400)

    current_stock = payload.get("current_stock")
    if current_stock is None:
        current_stock = payload.get("qty", 0)

    minimum_stock = payload.get("minimum_stock")
    if minimum_stock is None:
        minimum_stock = payload.get("min", 10)

    try:
        current_stock = _parse_int(current_stock, 0)
        minimum_stock = _parse_int(minimum_stock, 10)
    except ValueError:
        return error_response("Invalid stock value", 400)

    item = MedicineStock(
        medicine_name=str(medicine_name).strip(),
        category=payload.get("category"),
        unit=payload.get("unit"),
        current_stock=current_stock,
        minimum_stock=minimum_stock,
        batch_number=payload.get("batch_number") or payload.get("batch"),
        supplier=payload.get("supplier"),
        village=payload.get("village"),
        created_by=get_jwt_identity(),
    )
    if payload.get("expiry_date") is not None:
        try:
            item.expiry_date = _parse_stock_date(payload["expiry_date"])
        except ValueError:
            return error_response("Invalid expiry_date format", 400)

    item.is_low_stock = item.current_stock <= item.minimum_stock
    db.session.add(item)
    db.session.commit()
    return success_response(data=_serialize_stock(item), message="Stock item saved", status_code=201)


@stock_bp.put("/medicine-stock/<int:stock_id>")
@stock_bp.put("/stock/<int:stock_id>")
@jwt_required()
def update_stock(stock_id: int):
    item = MedicineStock.query.get(stock_id)
    if not item:
        return error_response("Stock item not found", 404)

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return error_response("Invalid request payload", 400)

    if "medicine_name" in payload:
        item.medicine_name = payload["medicine_name"]
    if "category" in payload:
        item.category = payload["category"]
    if "unit" in payload:
        item.unit = payload["unit"]
    if "current_stock" in payload:
        try:
            item.current_stock = _parse_int(payload["current_stock"], 0)
        except ValueError:
            return error_response("Invalid current_stock value", 400)
    elif "qty" in payload:
        try:
            item.current_stock = _parse_int(payload["qty"], 0)
        except ValueError:
            return error_response("Invalid qty value", 400)
    if "minimum_stock" in payload:
        try:
            item.minimum_stock = _parse_int(payload["minimum_stock"], 10)
        except ValueError:
            return error_response("Invalid minimum_stock value", 400)
    elif "min" in payload:
        try:
            item.minimum_stock = _parse_int(payload["min"], 10)
        except ValueError:
            return error_response("Invalid min value", 400)
    if "batch_number" in payload:
        item.batch_number = payload["batch_number"]
    elif "batch" in payload:
        item.batch_number = payload["batch"]
    if "supplier" in payload:
        item.supplier = payload["supplier"]
    if "village" in payload:
        item.village = payload["village"]
    if "expiry_date" in payload:
        if payload["expiry_date"] is None or str(payload["expiry_date"]).strip() == "":
            item.expiry_date = None
        else:
            try:
                item.expiry_date = _parse_stock_date(payload["expiry_date"])
            except ValueError:
                return error_response("Invalid expiry_date format", 400)

    item.is_low_stock = item.current_stock <= item.minimum_stock
    db.session.commit()
    return success_response(data=_serialize_stock(item), message="Stock item updated")


@stock_bp.delete("/medicine-stock/<int:stock_id>")
@stock_bp.delete("/stock/<int:stock_id>")
@jwt_required()
def delete_stock(stock_id: int):
    item = MedicineStock.query.get(stock_id)
    if not item:
        return error_response("Stock item not found", 404)
    db.session.delete(item)
    db.session.commit()
    return success_response(data={"id": stock_id}, message="Stock item deleted")
