"""
app/routes/vaccine.py
======================
Vaccine entry routes (nested under children).

Endpoints:
  GET    /api/vaccines/                              – list all entries
  POST   /api/vaccines/                              – add vaccine entry
  GET    /api/vaccines/<id>                          – get single entry
  PUT    /api/vaccines/<id>                          – update entry
  DELETE /api/vaccines/<id>                          – delete entry
  GET    /api/vaccines/child/<child_id>              – all vaccines for a child

Sample response (POST /api/vaccines/):
{
    "success": true,
    "message": "Vaccine entry added.",
    "data": {
        "id": "uuid",
        "child_id": "uuid",
        "name": "BCG",
        "due_date": "2023-06-15",
        "status": "given"
    }
}
"""

import logging

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models.vaccine import VaccineEntry
from app.schemas.children_schema import VaccineEntrySchema, vaccine_schema, vaccines_schema
from app.utils.response import error_response, success_response

logger     = logging.getLogger(__name__)
vaccine_bp = Blueprint("vaccine", __name__)

_vaccine_input = VaccineEntrySchema()


@vaccine_bp.get("/")
@jwt_required()
def list_vaccines():
    entries = VaccineEntry.query.order_by(VaccineEntry.due_date).all()
    return success_response(data=[e.to_dict() for e in entries])


@vaccine_bp.get("/child/<string:child_id>")
@jwt_required()
def list_vaccines_for_child(child_id: str):
    entries = VaccineEntry.query.filter_by(child_id=child_id).order_by(VaccineEntry.due_date).all()
    return success_response(data=[e.to_dict() for e in entries])


@vaccine_bp.post("/")
@jwt_required()
def add_vaccine():
    """
    Add a vaccine entry.

    Sample request:
    {
        "child_id": "uuid",
        "name": "BCG",
        "due_date": "2023-06-15",
        "given_date": "2023-06-15",
        "status": "given"
    }
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be JSON.", 400)

    try:
        entry = _vaccine_input.load(json_data, session=db.session)
    except ValidationError as err:
        return error_response("Validation failed.", 422, errors=err.messages)

    try:
        db.session.add(entry)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=entry.to_dict(), message="Vaccine entry added.", status_code=201)
    except Exception as exc:
        db.session.rollback()
        logger.exception("Add vaccine error: %s", exc)
        return error_response(str(exc), 500)


@vaccine_bp.get("/<string:entry_id>")
@jwt_required()
def get_vaccine(entry_id: str):
    entry = db.session.get(VaccineEntry, entry_id)
    if not entry:
        return error_response("Vaccine entry not found.", 404)
    return success_response(data=entry.to_dict())


@vaccine_bp.put("/<string:entry_id>")
@jwt_required()
def update_vaccine(entry_id: str):
    entry = db.session.get(VaccineEntry, entry_id)
    if not entry:
        return error_response("Vaccine entry not found.", 404)

    data    = request.get_json(silent=True) or {}
    allowed = {"name", "due_date", "given_date", "next_due", "status"}
    for field in allowed:
        if field in data:
            setattr(entry, field, data[field])

    try:
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=entry.to_dict(), message="Vaccine entry updated.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Update vaccine error: %s", exc)
        return error_response(str(exc), 500)


@vaccine_bp.delete("/<string:entry_id>")
@jwt_required()
def delete_vaccine(entry_id: str):
    entry = db.session.get(VaccineEntry, entry_id)
    if not entry:
        return error_response("Vaccine entry not found.", 404)

    try:
        db.session.delete(entry)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(message="Vaccine entry deleted.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Delete vaccine error: %s", exc)
        return error_response(str(exc), 500)
