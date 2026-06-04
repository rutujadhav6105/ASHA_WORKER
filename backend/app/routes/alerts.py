"""
app/routes/alerts.py
====================
Alert/notification message CRUD API.

Endpoints:
  GET    /api/alerts/                    – list alerts (filterable by asha_id, is_read)
  POST   /api/alerts/                    – create alert
  GET    /api/alerts/<id>                – get single alert
  PUT    /api/alerts/<id>                – update alert (mark read, action_taken)
  DELETE /api/alerts/<id>                – delete alert

Query params (GET /api/alerts/):
  asha_id, is_read, alert_type, severity, page, per_page
"""

import logging

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models.alert import AlertMessage
from app.schemas.alert_schema import AlertSchema, alert_schema
from app.utils.response import error_response, paginate_query, success_response

logger     = logging.getLogger(__name__)
alerts_bp  = Blueprint("alerts", __name__)

_alert_input = AlertSchema()


@alerts_bp.get("/")
@jwt_required()
def list_alerts():
    """
    List alerts for an ASHA worker, optionally filtered.

    Query params:
      - asha_id: filter by worker ID
      - is_read: filter by read status (true/false)
      - alert_type: filter by alert type
      - severity: filter by severity
      - page, per_page: pagination
    """
    page      = request.args.get("page",       1,  type=int)
    per_page  = request.args.get("per_page",   20, type=int)
    asha_id   = request.args.get("asha_id")
    is_read   = request.args.get("is_read")
    alert_type = request.args.get("alert_type")
    severity  = request.args.get("severity")

    query = AlertMessage.query
    if asha_id:
        query = query.filter_by(asha_id=asha_id)
    if is_read is not None:
        is_read_bool = is_read.lower() in ("true", "1", "yes")
        query = query.filter_by(is_read=is_read_bool)
    if alert_type:
        query = query.filter_by(alert_type=alert_type)
    if severity:
        query = query.filter_by(severity=severity)

    query = query.order_by(AlertMessage.created_at.desc())
    items, meta = paginate_query(query, page, per_page)
    return success_response(data=[a.to_dict() for a in items], meta=meta)


@alerts_bp.post("/")
@jwt_required()
def create_alert():
    """
    Create a new alert/message.

    Sample request:
    {
        "asha_id": "ASH001",
        "title": "Monthly Report Due",
        "message": "Please submit your June report by 30th.",
        "alert_type": "supervisor",
        "severity": "warning"
    }
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be JSON.", 400)

    try:
        alert = _alert_input.load(json_data)
    except ValidationError as err:
        return error_response("Validation failed.", 422, errors=err.messages)

    try:
        db.session.add(alert)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=alert.to_dict(), message="Alert created.", status_code=201)
    except Exception as exc:
        db.session.rollback()
        logger.exception("Create alert error: %s", exc)
        return error_response(str(exc), 500)


@alerts_bp.get("/<string:alert_id>")
@jwt_required()
def get_alert(alert_id: str):
    """Get a single alert by ID."""
    alert = db.session.get(AlertMessage, alert_id)
    if not alert:
        return error_response("Alert not found.", 404)
    return success_response(data=alert.to_dict())


@alerts_bp.put("/<string:alert_id>")
@jwt_required()
def update_alert(alert_id: str):
    """
    Update alert status (mark as read, action_taken, etc.).

    Sample request:
    {
        "is_read": true,
        "action_taken": true
    }
    """
    alert = db.session.get(AlertMessage, alert_id)
    if not alert:
        return error_response("Alert not found.", 404)

    data    = request.get_json(silent=True) or {}
    allowed = {"title", "message", "alert_type", "severity", "is_read", "action_taken", "expires_at"}
    for field in allowed:
        if field in data:
            setattr(alert, field, data[field])

    try:
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=alert.to_dict(), message="Alert updated.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Update alert error: %s", exc)
        return error_response(str(exc), 500)


@alerts_bp.delete("/<string:alert_id>")
@jwt_required()
def delete_alert(alert_id: str):
    """Delete an alert."""
    alert = db.session.get(AlertMessage, alert_id)
    if not alert:
        return error_response("Alert not found.", 404)

    try:
        db.session.delete(alert)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(message="Alert deleted.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Delete alert error: %s", exc)
        return error_response(str(exc), 500)


@alerts_bp.post("/<string:alert_id>/mark-read")
@jwt_required()
def mark_alert_read(alert_id: str):
    """Mark alert as read."""
    alert = db.session.get(AlertMessage, alert_id)
    if not alert:
        return error_response("Alert not found.", 404)

    alert.is_read = True
    try:
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=alert.to_dict(), message="Alert marked as read.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Mark read error: %s", exc)
        return error_response(str(exc), 500)
