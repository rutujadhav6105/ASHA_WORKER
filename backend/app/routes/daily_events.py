import logging
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.daily_event import DailyEvent
from app.utils.response import error_response, success_response

logger = logging.getLogger(__name__)

daily_events_bp = Blueprint("daily_events", __name__)


def _serialize_event(event: DailyEvent) -> dict:
    record = {} if event.data is None else dict(event.data)
    record.update({
        "id": event.id,
        "event_type": event.event_type,
        "asha_id": event.asha_id,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    })
    return record


@daily_events_bp.get("/marriage")
@jwt_required()
def list_marriages():
    asha_id = request.args.get("asha_id")
    query = DailyEvent.query.filter_by(event_type="marriage")
    if asha_id:
        query = query.filter_by(asha_id=asha_id)
    events = query.order_by(DailyEvent.created_at.desc()).all()
    return success_response(data=[_serialize_event(event) for event in events])


@daily_events_bp.post("/marriage")
@jwt_required()
def create_marriage():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return error_response("Invalid request payload", 400)

    event = DailyEvent(
        event_type="marriage",
        asha_id=payload.get("asha_id"),
        data=payload,
        created_by=get_jwt_identity(),
    )
    db.session.add(event)
    db.session.commit()
    return success_response(data=_serialize_event(event), message="Marriage record saved", status_code=201)


@daily_events_bp.delete("/marriage/<int:event_id>")
@jwt_required()
def delete_marriage(event_id: int):
    event = DailyEvent.query.filter_by(id=event_id, event_type="marriage").first()
    if not event:
        return error_response("Marriage record not found", 404)
    db.session.delete(event)
    db.session.commit()
    return success_response(data={"id": event_id}, message="Marriage record deleted")


@daily_events_bp.get("/birth")
@jwt_required()
def list_births():
    asha_id = request.args.get("asha_id")
    query = DailyEvent.query.filter_by(event_type="birth")
    if asha_id:
        query = query.filter_by(asha_id=asha_id)
    events = query.order_by(DailyEvent.created_at.desc()).all()
    return success_response(data=[_serialize_event(event) for event in events])


@daily_events_bp.post("/birth")
@jwt_required()
def create_birth():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return error_response("Invalid request payload", 400)

    event = DailyEvent(
        event_type="birth",
        asha_id=payload.get("asha_id"),
        data=payload,
        created_by=get_jwt_identity(),
    )
    db.session.add(event)
    db.session.commit()
    return success_response(data=_serialize_event(event), message="Birth record saved", status_code=201)


@daily_events_bp.delete("/birth/<int:event_id>")
@jwt_required()
def delete_birth(event_id: int):
    event = DailyEvent.query.filter_by(id=event_id, event_type="birth").first()
    if not event:
        return error_response("Birth record not found", 404)
    db.session.delete(event)
    db.session.commit()
    return success_response(data={"id": event_id}, message="Birth record deleted")


@daily_events_bp.get("/death")
@jwt_required()
def list_deaths():
    asha_id = request.args.get("asha_id")
    query = DailyEvent.query.filter_by(event_type="death")
    if asha_id:
        query = query.filter_by(asha_id=asha_id)
    events = query.order_by(DailyEvent.created_at.desc()).all()
    return success_response(data=[_serialize_event(event) for event in events])


@daily_events_bp.post("/death")
@jwt_required()
def create_death():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return error_response("Invalid request payload", 400)

    event = DailyEvent(
        event_type="death",
        asha_id=payload.get("asha_id"),
        data=payload,
        created_by=get_jwt_identity(),
    )
    db.session.add(event)
    db.session.commit()
    return success_response(data=_serialize_event(event), message="Death record saved", status_code=201)


@daily_events_bp.delete("/death/<int:event_id>")
@jwt_required()
def delete_death(event_id: int):
    event = DailyEvent.query.filter_by(id=event_id, event_type="death").first()
    if not event:
        return error_response("Death record not found", 404)
    db.session.delete(event)
    db.session.commit()
    return success_response(data={"id": event_id}, message="Death record deleted")
