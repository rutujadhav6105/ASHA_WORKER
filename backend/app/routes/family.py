"""
app/routes/family.py
=====================
Family and FamilyMember CRUD endpoints.

Endpoints:
  GET    /api/families/                    – list all families (paginated)
  POST   /api/families/                    – create a family
  GET    /api/families/<id>                – get family + members
  PUT    /api/families/<id>                – update family
  DELETE /api/families/<id>                – delete family
  POST   /api/families/<id>/members        – add member to family
  GET    /api/families/<id>/members        – list members of family
  PUT    /api/families/<id>/members/<mid>  – update a member
  DELETE /api/families/<id>/members/<mid>  – delete a member

Sample response (GET /api/families/):
{
    "success": true,
    "message": "Success",
    "data": [
        {
            "id": "abc123",
            "family_head": "Ramesh Kumar",
            "village": "Khed",
            "asha_id": "ASH001",
            "created_at": "2024-01-15T10:30:00"
        }
    ],
    "meta": { "page": 1, "per_page": 20, "total": 45, "total_pages": 3 }
}
"""

import logging

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models.family import FamilyMemberModel, FamilyModel
from app.schemas.family_schema import (
    FamilyMemberSchema,
    FamilySchema,
    FamilyWithMembersSchema,
    family_member_schema,
    family_members_schema,
    family_schema,
    family_with_members_schema,
    families_schema,
)
from app.utils.response import error_response, paginate_query, success_response

logger    = logging.getLogger(__name__)
family_bp = Blueprint("family", __name__)

_family_input_schema = FamilySchema()
_member_input_schema = FamilyMemberSchema()


# --------------------------------------------------------------------------
# Families collection
# --------------------------------------------------------------------------

@family_bp.get("/")
@jwt_required()
def list_families():
    """Return all families with optional pagination."""
    page     = request.args.get("page",     1,  type=int)
    per_page = request.args.get("per_page", 20, type=int)
    asha_id  = request.args.get("asha_id")

    query = FamilyModel.query
    if asha_id:
        query = query.filter_by(asha_id=asha_id)
    query = query.order_by(FamilyModel.created_at.desc())

    items, meta = paginate_query(query, page, per_page)
    return success_response(
        data=[f.to_dict() for f in items],
        meta=meta,
    )


@family_bp.post("/")
@jwt_required()
def create_family():
    """
    Create a new family.

    Sample request body:
    {
        "family_head": "Ramesh Kumar",
        "home_no": "42-B",
        "address": "Near Hanuman Temple",
        "village": "Khed",
        "taluka": "Khed",
        "district": "Pune",
        "asha_id": "ASH001"
    }
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be JSON.", 400)

    try:
        family = _family_input_schema.load(json_data, session=db.session)
    except ValidationError as err:
        return error_response("Validation failed.", 422, errors=err.messages)

    try:
        db.session.add(family)
        db.session.commit()
        logger.info("Data saved successfully")
        logger.info("Family created: %s", family.id)
        return success_response(
            data=family.to_dict(),
            message="Family created successfully.",
            status_code=201,
        )
    except Exception as exc:
        db.session.rollback()
        logger.exception("Create family error: %s", exc)
        return error_response(str(exc), 500)


# --------------------------------------------------------------------------
# Single family
# --------------------------------------------------------------------------

@family_bp.get("/<string:family_id>")
@jwt_required()
def get_family(family_id: str):
    """Get a single family with all its members."""
    family = db.session.get(FamilyModel, family_id)
    if not family:
        return error_response("Family not found.", 404)
    return success_response(data=family.to_dict(include_members=True))


@family_bp.put("/<string:family_id>")
@jwt_required()
def update_family(family_id: str):
    family = db.session.get(FamilyModel, family_id)
    if not family:
        return error_response("Family not found.", 404)

    data    = request.get_json(silent=True) or {}
    allowed = {"home_no", "address", "village", "taluka", "district", "family_head", "asha_id"}
    for field in allowed:
        if field in data:
            setattr(family, field, data[field])

    try:
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=family.to_dict(), message="Family updated.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Update family error: %s", exc)
        return error_response(str(exc), 500)


@family_bp.delete("/<string:family_id>")
@jwt_required()
def delete_family(family_id: str):
    family = db.session.get(FamilyModel, family_id)
    if not family:
        return error_response("Family not found.", 404)

    try:
        db.session.delete(family)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(message="Family deleted.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Delete family error: %s", exc)
        return error_response(str(exc), 500)


# --------------------------------------------------------------------------
# Family members
# --------------------------------------------------------------------------

@family_bp.get("/<string:family_id>/members")
@jwt_required()
def list_members(family_id: str):
    family = db.session.get(FamilyModel, family_id)
    if not family:
        return error_response("Family not found.", 404)
    return success_response(data=[m.to_dict() for m in family.members])


@family_bp.post("/<string:family_id>/members")
@jwt_required()
def add_member(family_id: str):
    """
    Add a member to an existing family.

    Sample request body:
    {
        "name": "Sunita Devi",
        "dob": "1990-05-20",
        "gender": "Female",
        "aadhaar": "123456789012",
        "apl_bpl": "BPL",
        "is_reproductive_pair": true
    }
    """
    family = db.session.get(FamilyModel, family_id)
    if not family:
        return error_response("Family not found.", 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be JSON.", 400)

    json_data["family_id"] = family_id   # inject FK

    try:
        member = _member_input_schema.load(json_data, session=db.session)
    except ValidationError as err:
        return error_response("Validation failed.", 422, errors=err.messages)

    # Aadhaar uniqueness check
    if member.aadhaar:
        existing = FamilyMemberModel.query.filter_by(aadhaar=member.aadhaar).first()
        if existing:
            return error_response(f"Aadhaar {member.aadhaar} is already registered.", 409)

    try:
        db.session.add(member)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(
            data=member.to_dict(),
            message="Member added successfully.",
            status_code=201,
        )
    except Exception as exc:
        db.session.rollback()
        logger.exception("Add member error: %s", exc)
        return error_response(str(exc), 500)


@family_bp.put("/<string:family_id>/members/<string:member_id>")
@jwt_required()
def update_member(family_id: str, member_id: str):
    member = FamilyMemberModel.query.filter_by(id=member_id, family_id=family_id).first()
    if not member:
        return error_response("Member not found.", 404)

    data    = request.get_json(silent=True) or {}
    allowed = {
        "name", "dob", "age", "aadhaar", "gender",
        "is_reproductive_pair", "caste", "sub_caste", "apl_bpl", "education",
    }
    for field in allowed:
        if field in data:
            setattr(member, field, data[field])

    try:
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=member.to_dict(), message="Member updated.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Update member error: %s", exc)
        return error_response(str(exc), 500)


@family_bp.delete("/<string:family_id>/members/<string:member_id>")
@jwt_required()
def delete_member(family_id: str, member_id: str):
    member = FamilyMemberModel.query.filter_by(id=member_id, family_id=family_id).first()
    if not member:
        return error_response("Member not found.", 404)

    try:
        db.session.delete(member)
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(message="Member deleted.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Delete member error: %s", exc)
        return error_response(str(exc), 500)
