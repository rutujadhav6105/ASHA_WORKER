"""
app/routes/vaccination.py
==========================
Vaccination / Immunization Management API.

Provides higher-level immunization management beyond the basic
vaccine_entries CRUD (app/routes/vaccine.py). Includes:

  GET  /api/vaccination/due              – children with due/overdue vaccines
  GET  /api/vaccination/schedule         – upcoming schedule (next N days)
  POST /api/vaccination/bulk-update      – mark multiple doses as given
  GET  /api/vaccination/coverage         – coverage stats by asha_id/village
  GET  /api/vaccination/defaulters       – overdue + not-given children

These routes are JWT-protected and complement the basic
/api/vaccines/* CRUD endpoints.
"""

import logging
from datetime import date, timedelta

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from app.extensions import db
from app.models.children import ChildModel
from app.models.vaccine import VaccineEntry
from app.utils.response import error_response, success_response

logger          = logging.getLogger(__name__)
vaccination_bp  = Blueprint("vaccination", __name__)


@vaccination_bp.get("/due")
@jwt_required()
def due_vaccines():
    """
    Children who have vaccines with status 'due' or 'overdue'.

    Query params: asha_id, days (default=7 — vaccines due within N days)
    """
    asha_id = request.args.get("asha_id")
    days    = request.args.get("days", 7, type=int)
    today   = date.today()
    cutoff  = today + timedelta(days=days)

    query = db.session.query(VaccineEntry, ChildModel).join(
        ChildModel, VaccineEntry.child_id == ChildModel.id
    ).filter(
        VaccineEntry.status.in_(["due", "overdue", "scheduled"]),
        VaccineEntry.due_date <= cutoff,
    )

    if asha_id:
        query = query.filter(ChildModel.asha_id == asha_id)

    rows = query.order_by(VaccineEntry.due_date.asc()).all()

    data = []
    for vaccine, child in rows:
        entry = vaccine.to_dict()
        entry["child_name"]  = child.child_name
        entry["mother_name"] = child.mother_name
        entry["asha_id"]     = child.asha_id
        data.append(entry)

    return success_response(data=data)


@vaccination_bp.get("/schedule")
@jwt_required()
def vaccination_schedule():
    """
    Upcoming vaccination schedule for next N days.

    Query params: asha_id, days (default=30)
    """
    asha_id = request.args.get("asha_id")
    days    = request.args.get("days", 30, type=int)
    today   = date.today()
    end_d   = today + timedelta(days=days)

    query = db.session.query(VaccineEntry, ChildModel).join(
        ChildModel, VaccineEntry.child_id == ChildModel.id
    ).filter(
        VaccineEntry.status.in_(["scheduled", "due"]),
        VaccineEntry.due_date >= today,
        VaccineEntry.due_date <= end_d,
    )
    if asha_id:
        query = query.filter(ChildModel.asha_id == asha_id)

    rows = query.order_by(VaccineEntry.due_date.asc()).all()

    data = []
    for vaccine, child in rows:
        entry = vaccine.to_dict()
        entry["child_name"]  = child.child_name
        entry["mother_name"] = child.mother_name
        entry["asha_id"]     = child.asha_id
        data.append(entry)

    return success_response(data=data)


@vaccination_bp.post("/bulk-update")
@jwt_required()
def bulk_update_vaccines():
    """
    Mark multiple vaccine entries as 'given' in a single request.

    Request body:
    {
        "vaccine_ids": ["uuid1", "uuid2"],
        "given_date": "2024-05-15",         // optional, defaults to today
        "status": "given"                   // optional, default "given"
    }
    """
    data = request.get_json(silent=True) or {}
    vaccine_ids = data.get("vaccine_ids")
    if not vaccine_ids or not isinstance(vaccine_ids, list):
        return error_response("'vaccine_ids' must be a non-empty list of IDs.", 400)

    given_date_str = data.get("given_date")
    status         = data.get("status", "given")
    if status not in ("given", "overdue", "scheduled", "due"):
        return error_response("Invalid status value.", 400)

    given_date = date.today()
    if given_date_str:
        try:
            given_date = date.fromisoformat(given_date_str)
        except ValueError:
            return error_response("Invalid given_date format. Use YYYY-MM-DD.", 400)

    updated = 0
    not_found = []
    try:
        for vid in vaccine_ids:
            entry = db.session.get(VaccineEntry, vid)
            if not entry:
                not_found.append(vid)
                continue
            entry.status     = status
            entry.given_date = given_date if status == "given" else entry.given_date
            updated += 1
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Bulk update error: %s", exc)
        return error_response("Bulk update failed.", 500)

    return success_response(
        data={"updated": updated, "not_found": not_found},
        message=f"{updated} vaccine(s) updated.",
    )


@vaccination_bp.get("/coverage")
@jwt_required()
def vaccination_coverage():
    """
    Coverage statistics: given vs scheduled+due+overdue counts.

    Query params: asha_id (optional)
    """
    asha_id = request.args.get("asha_id")

    query = db.session.query(
        ChildModel.asha_id,
        VaccineEntry.name,
        VaccineEntry.status,
        func.count(VaccineEntry.id).label("count"),
    ).join(ChildModel, VaccineEntry.child_id == ChildModel.id)

    if asha_id:
        query = query.filter(ChildModel.asha_id == asha_id)

    rows = query.group_by(
        ChildModel.asha_id, VaccineEntry.name, VaccineEntry.status
    ).all()

    # Aggregate into { asha_id: { vaccine_name: { status: count } } }
    result: dict = {}
    for r in rows:
        aid = r.asha_id or "unknown"
        if aid not in result:
            result[aid] = {}
        if r.name not in result[aid]:
            result[aid][r.name] = {}
        result[aid][r.name][r.status] = r.count

    return success_response(data=result)


@vaccination_bp.get("/defaulters")
@jwt_required()
def vaccination_defaulters():
    """
    Children with overdue vaccines (due_date in the past, status != 'given').

    Query params: asha_id (optional)
    """
    asha_id = request.args.get("asha_id")
    today   = date.today()

    query = db.session.query(VaccineEntry, ChildModel).join(
        ChildModel, VaccineEntry.child_id == ChildModel.id
    ).filter(
        VaccineEntry.status.in_(["overdue", "scheduled", "due"]),
        VaccineEntry.due_date < today,
    )
    if asha_id:
        query = query.filter(ChildModel.asha_id == asha_id)

    rows = query.order_by(VaccineEntry.due_date.asc()).all()

    data = []
    for vaccine, child in rows:
        entry = vaccine.to_dict()
        entry["child_name"]  = child.child_name
        entry["mother_name"] = child.mother_name
        entry["asha_id"]     = child.asha_id
        entry["days_overdue"] = (today - vaccine.due_date).days if vaccine.due_date else None
        data.append(entry)

    return success_response(data=data, message=f"{len(data)} defaulter record(s) found.")
