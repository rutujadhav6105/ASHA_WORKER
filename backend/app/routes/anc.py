"""
app/routes/anc.py
==================
ANC (Antenatal Care) CRUD routes.

Endpoints:
  GET    /api/anc/        – list all ANC records (filterable by asha_id)
  POST   /api/anc/        – create ANC record
  GET    /api/anc/<id>    – get single record
  PUT    /api/anc/<id>    – update record
  DELETE /api/anc/<id>    – delete record

Sample success response (POST /api/anc/):
{
    "success": true,
    "message": "ANC record created successfully.",
    "data": {
        "id": "uuid",
        "beneficiary_name": "Meena Sharma",
        "lmp": "2024-01-01",
        "edd": "2024-10-08",
        "risk_status": "Normal",
        "asha_id": "ASH001"
    }
}
"""

import logging

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models.anc import ANCRecord
from app.schemas.anc_schema import ANCSchema, anc_schema, ancs_schema
from app.utils.response import error_response, paginate_query, success_response

logger = logging.getLogger(__name__)
anc_bp = Blueprint("anc", __name__)

_anc_input = ANCSchema()


@anc_bp.get("/")
@jwt_required()
def list_anc():
    page     = request.args.get("page",     1,  type=int)
    per_page = request.args.get("per_page", 20, type=int)
    asha_id  = request.args.get("asha_id")

    query = ANCRecord.query
    if asha_id:
        query = query.filter_by(asha_id=asha_id)
    query = query.order_by(ANCRecord.created_at.desc())

    items, meta = paginate_query(query, page, per_page)
    return success_response(data=[r.to_dict() for r in items], meta=meta)


@anc_bp.post("/")
@jwt_required()
def create_anc():
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be JSON.", 400)

    try:
        record = _anc_input.load(json_data, session=db.session)
    except ValidationError as err:
        return error_response("Validation failed.", 422, errors=err.messages)

    try:
        db.session.add(record)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=record.to_dict(), message="ANC record created successfully.", status_code=201)
    except Exception as exc:
        db.session.rollback()
        logger.exception("Create ANC error: %s", exc)
        return error_response(str(exc), 500)


@anc_bp.get("/<string:record_id>")
@jwt_required()
def get_anc(record_id: str):
    record = db.session.get(ANCRecord, record_id)
    if not record:
        return error_response("ANC record not found.", 404)
    return success_response(data=record.to_dict())


@anc_bp.put("/<string:record_id>")
@jwt_required()
def update_anc(record_id: str):
    record = db.session.get(ANCRecord, record_id)
    if not record:
        return error_response("ANC record not found.", 404)

    data    = request.get_json(silent=True) or {}
    allowed = {"beneficiary_name", "husband_name", "lmp", "edd", "gravida", "risk_status", "mobile", "village", "asha_id"}
    for field in allowed:
        if field in data:
            setattr(record, field, data[field])

    try:
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=record.to_dict(), message="ANC record updated.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Update ANC error: %s", exc)
        return error_response(str(exc), 500)


@anc_bp.delete("/<string:record_id>")
@jwt_required()
def delete_anc(record_id: str):
    record = db.session.get(ANCRecord, record_id)
    if not record:
        return error_response("ANC record not found.", 404)

    try:
        db.session.delete(record)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(message="ANC record deleted.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Delete ANC error: %s", exc)
        return error_response(str(exc), 500)
