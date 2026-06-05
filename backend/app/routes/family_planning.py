"""
app/routes/family_planning.py
==============================
Family Planning CRUD API.

Endpoints:
  GET    /api/family-planning/           – list records (filterable)
  POST   /api/family-planning/           – create record
  GET    /api/family-planning/<id>       – get single record
  PUT    /api/family-planning/<id>       – update record
  DELETE /api/family-planning/<id>       – delete record
  GET    /api/family-planning/follow-ups – upcoming follow-up appointments

Query params (GET /api/family-planning/):
  asha_id, method, status, village, page, per_page

Sample response (POST):
{
    "success": true,
    "message": "Family planning record created.",
    "data": {
        "id": "uuid",
        "asha_id": "ASH001",
        "beneficiary_name": "Sunita Patil",
        "method": "IUCD",
        "status": "active"
    }
}
"""

import logging
from datetime import date, timedelta

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models.family_planning import FamilyPlanningRecord
from app.schemas.family_planning_schema import FamilyPlanningSchema, fp_schema
from app.utils.response import error_response, paginate_query, success_response

logger           = logging.getLogger(__name__)
family_planning_bp = Blueprint("family_planning", __name__)

_fp_input = FamilyPlanningSchema()


@family_planning_bp.get("/")
@jwt_required()
def list_fp():
    page     = request.args.get("page",     1,  type=int)
    per_page = request.args.get("per_page", 20, type=int)
    asha_id  = request.args.get("asha_id")
    method   = request.args.get("method")
    status   = request.args.get("status")
    village  = request.args.get("village")

    query = FamilyPlanningRecord.query
    if asha_id:
        query = query.filter_by(asha_id=asha_id)
    if method:
        query = query.filter_by(method=method)
    if status:
        query = query.filter_by(status=status)
    if village:
        query = query.filter_by(village=village)

    query = query.order_by(FamilyPlanningRecord.created_at.desc())
    items, meta = paginate_query(query, page, per_page)
    return success_response(data=[r.to_dict() for r in items], meta=meta)


@family_planning_bp.post("/")
@jwt_required()
def create_fp():
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be JSON.", 400)

    try:
        record = _fp_input.load(json_data, session=db.session)
    except ValidationError as err:
        logger.debug("FP validation errors: %s", err.messages)
        return error_response("Validation failed.", 422, errors=err.messages)

    try:
        db.session.add(record)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=record.to_dict(), message="Family planning record created.", status_code=201)
    except Exception as exc:
        db.session.rollback()
        logger.exception("Create FP error: %s", exc)
        return error_response(str(exc), 500)


@family_planning_bp.get("/follow-ups")
@jwt_required()
def upcoming_followups():
    """Return FP records with upcoming follow-up dates (next N days)."""
    asha_id = request.args.get("asha_id")
    days    = request.args.get("days", 30, type=int)
    today   = date.today()
    end_d   = today + timedelta(days=days)

    query = FamilyPlanningRecord.query.filter(
        FamilyPlanningRecord.next_followup_date >= today,
        FamilyPlanningRecord.next_followup_date <= end_d,
        FamilyPlanningRecord.status.in_(["active", "follow_up"]),
    )
    if asha_id:
        query = query.filter_by(asha_id=asha_id)
    records = query.order_by(FamilyPlanningRecord.next_followup_date.asc()).all()
    return success_response(data=[r.to_dict() for r in records])


@family_planning_bp.get("/<string:record_id>")
@jwt_required()
def get_fp(record_id: str):
    record = db.session.get(FamilyPlanningRecord, record_id)
    if not record:
        return error_response("Record not found.", 404)
    return success_response(data=record.to_dict())


@family_planning_bp.put("/<string:record_id>")
@jwt_required()
def update_fp(record_id: str):
    record = db.session.get(FamilyPlanningRecord, record_id)
    if not record:
        return error_response("Record not found.", 404)

    data    = request.get_json(silent=True) or {}
    allowed = {
        "beneficiary_name", "husband_name", "mobile", "village", "age",
        "method", "method_start_date", "method_end_date", "status",
        "counselling_date", "counselling_notes", "side_effects",
        "complications", "next_followup_date", "followup_notes", "living_children",
    }
    for field in allowed:
        if field in data:
            setattr(record, field, data[field])

    try:
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=record.to_dict(), message="Record updated.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Update FP error: %s", exc)
        return error_response(str(exc), 500)


@family_planning_bp.delete("/<string:record_id>")
@jwt_required()
def delete_fp(record_id: str):
    record = db.session.get(FamilyPlanningRecord, record_id)
    if not record:
        return error_response("Record not found.", 404)

    try:
        db.session.delete(record)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(message="Record deleted.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Delete FP error: %s", exc)
        return error_response(str(exc), 500)
