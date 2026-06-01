"""
app/routes/visits.py
=====================
Visit Tracking CRUD API.

Endpoints:
  GET    /api/visits/                    – list visits (filterable)
  POST   /api/visits/                    – create visit
  GET    /api/visits/<id>                – get single visit
  PUT    /api/visits/<id>                – update visit
  DELETE /api/visits/<id>                – delete visit
  GET    /api/visits/report/summary      – summary stats per ASHA worker
  GET    /api/visits/schedule            – upcoming scheduled visits

Query params (GET /api/visits/):
  asha_id, visit_type, status, from_date (YYYY-MM-DD), to_date (YYYY-MM-DD),
  page, per_page
"""

import logging
from datetime import date, timedelta

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from sqlalchemy import func

from app.extensions import db
from app.models.visit import VisitRecord
from app.schemas.visit_schema import VisitSchema, visit_schema
from app.utils.response import error_response, paginate_query, success_response

logger    = logging.getLogger(__name__)
visits_bp = Blueprint("visits", __name__)

_visit_input = VisitSchema()


@visits_bp.get("/")
@jwt_required()
def list_visits():
    page       = request.args.get("page",       1,  type=int)
    per_page   = request.args.get("per_page",   20, type=int)
    asha_id    = request.args.get("asha_id")
    visit_type = request.args.get("visit_type")
    status     = request.args.get("status")
    from_date  = request.args.get("from_date")
    to_date    = request.args.get("to_date")

    query = VisitRecord.query
    if asha_id:
        query = query.filter_by(asha_id=asha_id)
    if visit_type:
        query = query.filter_by(visit_type=visit_type)
    if status:
        query = query.filter_by(status=status)
    if from_date:
        try:
            query = query.filter(VisitRecord.visit_date >= date.fromisoformat(from_date))
        except ValueError:
            return error_response("Invalid from_date format. Use YYYY-MM-DD.", 400)
    if to_date:
        try:
            query = query.filter(VisitRecord.visit_date <= date.fromisoformat(to_date))
        except ValueError:
            return error_response("Invalid to_date format. Use YYYY-MM-DD.", 400)

    query = query.order_by(VisitRecord.visit_date.desc())
    items, meta = paginate_query(query, page, per_page)
    return success_response(data=[v.to_dict() for v in items], meta=meta)


@visits_bp.post("/")
@jwt_required()
def create_visit():
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be JSON.", 400)

    # Normalize Flutter payload format
    if 'patient_name' in json_data and 'beneficiary_name' not in json_data:
        json_data['beneficiary_name'] = json_data.pop('patient_name')
    
    if 'reason' in json_data and 'visit_type' not in json_data:
        json_data['visit_type'] = json_data.pop('reason')
    
    if 'status' in json_data and json_data['status'] == 'pending':
        json_data['status'] = 'scheduled'
    
    if 'visit_date' in json_data and isinstance(json_data['visit_date'], str):
        if 'T' in json_data['visit_date']:
            json_data['visit_date'] = json_data['visit_date'].split('T')[0]

    try:
        visit = _visit_input.load(json_data, session=db.session)
    except ValidationError as err:
        return error_response("Validation failed.", 422, errors=err.messages)

    try:
        db.session.add(visit)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=visit.to_dict(), message="Visit recorded successfully.", status_code=201)
    except Exception as exc:
        db.session.rollback()
        logger.exception("Create visit error: %s", exc)
        return error_response(str(exc), 500)


@visits_bp.get("/report/summary")
@jwt_required()
def visit_summary():
    asha_id   = request.args.get("asha_id")
    from_date = request.args.get("from_date")
    to_date   = request.args.get("to_date")

    query = db.session.query(
        VisitRecord.asha_id,
        VisitRecord.visit_type,
        VisitRecord.status,
        func.count(VisitRecord.id).label("count"),
    )
    if asha_id:
        query = query.filter(VisitRecord.asha_id == asha_id)
    if from_date:
        try:
            query = query.filter(VisitRecord.visit_date >= date.fromisoformat(from_date))
        except ValueError:
            return error_response("Invalid from_date.", 400)
    if to_date:
        try:
            query = query.filter(VisitRecord.visit_date <= date.fromisoformat(to_date))
        except ValueError:
            return error_response("Invalid to_date.", 400)

    rows = query.group_by(
        VisitRecord.asha_id, VisitRecord.visit_type, VisitRecord.status,
    ).all()

    return success_response(data=[
        {"asha_id": r.asha_id, "visit_type": r.visit_type, "status": r.status, "count": r.count}
        for r in rows
    ])


@visits_bp.get("/schedule")
@jwt_required()
def upcoming_visits():
    asha_id = request.args.get("asha_id")
    days    = request.args.get("days", 30, type=int)
    today   = date.today()
    end_d   = today + timedelta(days=days)

    query = VisitRecord.query.filter(
        VisitRecord.status == "scheduled",
        VisitRecord.visit_date >= today,
        VisitRecord.visit_date <= end_d,
    )
    if asha_id:
        query = query.filter_by(asha_id=asha_id)
    visits = query.order_by(VisitRecord.visit_date.asc()).all()
    return success_response(data=[v.to_dict() for v in visits])


@visits_bp.get("/<string:visit_id>")
@jwt_required()
def get_visit(visit_id: str):
    visit = db.session.get(VisitRecord, visit_id)
    if not visit:
        return error_response("Visit not found.", 404)
    return success_response(data=visit.to_dict())


@visits_bp.put("/<string:visit_id>")
@jwt_required()
def update_visit(visit_id: str):
    visit = db.session.get(VisitRecord, visit_id)
    if not visit:
        return error_response("Visit not found.", 404)

    data    = request.get_json(silent=True) or {}
    allowed = {
        "beneficiary_name", "village", "visit_type", "visit_date", "status",
        "notes", "weight_kg", "bp_systolic", "bp_diastolic", "temperature_c",
        "medicines_given", "referred", "referral_notes", "next_visit_date",
    }
    for field in allowed:
        if field in data:
            setattr(visit, field, data[field])

    try:
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=visit.to_dict(), message="Visit updated.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Update visit error: %s", exc)
        return error_response(str(exc), 500)


@visits_bp.delete("/<string:visit_id>")
@jwt_required()
def delete_visit(visit_id: str):
    visit = db.session.get(VisitRecord, visit_id)
    if not visit:
        return error_response("Visit not found.", 404)

    try:
        db.session.delete(visit)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(message="Visit deleted.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Delete visit error: %s", exc)
        return error_response(str(exc), 500)
