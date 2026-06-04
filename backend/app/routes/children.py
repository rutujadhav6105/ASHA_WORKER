"""
app/routes/children.py
=======================
Children registration and management routes.

Endpoints:
  GET    /api/children/        – list children (filterable by asha_id)
  POST   /api/children/        – register a child
  GET    /api/children/<id>    – get child with vaccine records
  PUT    /api/children/<id>    – update child details
  DELETE /api/children/<id>    – delete child

Sample response (GET /api/children/<id>):
{
    "success": true,
    "data": {
        "id": "uuid",
        "child_name": "Aryan",
        "mother_name": "Priya",
        "dob": "2023-06-15",
        "gender": "Male",
        "weight": 3.5,
        "asha_id": "ASH001",
        "vaccines": []
    }
}
"""

import logging

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models.children import ChildModel
from app.schemas.children_schema import ChildSchema, child_schema, children_schema
from app.utils.response import error_response, paginate_query, success_response

logger      = logging.getLogger(__name__)
children_bp = Blueprint("children", __name__)

_child_input = ChildSchema()


@children_bp.get("/")
@jwt_required()
def list_children():
    page     = request.args.get("page",     1,  type=int)
    per_page = request.args.get("per_page", 20, type=int)
    asha_id  = request.args.get("asha_id")

    query = ChildModel.query
    if asha_id:
        query = query.filter_by(asha_id=asha_id)
    query = query.order_by(ChildModel.created_at.desc())

    items, meta = paginate_query(query, page, per_page)
    return success_response(data=[c.to_dict(include_vaccines=True) for c in items], meta=meta)


@children_bp.post("/")
@jwt_required()
def create_child():
    """
    Register a new child.

    Sample request:
    {
        "child_name": "Aryan",
        "mother_name": "Priya",
        "dob": "2023-06-15",
        "gender": "Male",
        "weight": 3.5,
        "asha_id": "ASH001"
    }
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be JSON.", 400)

    try:
        child = _child_input.load(json_data, session=db.session)
    except ValidationError as err:
        return error_response("Validation failed.", 422, errors=err.messages)

    try:
        db.session.add(child)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=child.to_dict(), message="Child registered successfully.", status_code=201)
    except Exception as exc:
        db.session.rollback()
        logger.exception("Create child error: %s", exc)
        return error_response(str(exc), 500)


@children_bp.get("/<string:child_id>")
@jwt_required()
def get_child(child_id: str):
    child = db.session.get(ChildModel, child_id)
    if not child:
        return error_response("Child not found.", 404)
    return success_response(data=child.to_dict(include_vaccines=True))


@children_bp.put("/<string:child_id>")
@jwt_required()
def update_child(child_id: str):
    child = db.session.get(ChildModel, child_id)
    if not child:
        return error_response("Child not found.", 404)

    data    = request.get_json(silent=True) or {}
    allowed = {"child_name", "mother_name", "dob", "gender", "weight", "asha_id", "mobile", "village"}
    for field in allowed:
        if field in data:
            setattr(child, field, data[field])

    try:
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=child.to_dict(), message="Child updated.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Update child error: %s", exc)
        return error_response(str(exc), 500)


@children_bp.delete("/<string:child_id>")
@jwt_required()
def delete_child(child_id: str):
    child = db.session.get(ChildModel, child_id)
    if not child:
        return error_response("Child not found.", 404)

    try:
        db.session.delete(child)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(message="Child deleted.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Delete child error: %s", exc)
        return error_response(str(exc), 500)
