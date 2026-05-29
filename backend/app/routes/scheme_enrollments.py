"""Scheme enrollments API - stored in PostgreSQL."""

import logging

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models.scheme_enrollment import SchemeEnrollment
from app.models.user import UserModel
from app.schemas.scheme_enrollment_schema import SchemeEnrollmentSchema
from app.utils.response import error_response, paginate_query, success_response

logger = logging.getLogger(__name__)
scheme_enrollments_bp = Blueprint("scheme_enrollments", __name__)
_input_schema = SchemeEnrollmentSchema()


def _current_asha_context():
    user = UserModel.query.get(get_jwt_identity())
    if not user:
        return None, None
    return user.worker_id, user.name


@scheme_enrollments_bp.get("/")
@jwt_required()
def list_enrollments():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    asha_id = request.args.get("asha_id")
    asha_worker_name = request.args.get("asha_worker_name")
    scheme_name = request.args.get("scheme_name")
    district = request.args.get("district")

    query = SchemeEnrollment.query
    if asha_id:
        query = query.filter_by(asha_id=asha_id)
    if asha_worker_name:
        query = query.filter(
            SchemeEnrollment.asha_worker_name.ilike(f"%{asha_worker_name}%")
        )
    if scheme_name:
        query = query.filter(SchemeEnrollment.scheme_name.ilike(f"%{scheme_name}%"))
    if district:
        query = query.filter_by(district=district)

    query = query.order_by(SchemeEnrollment.created_at.desc())
    items, meta = paginate_query(query, page, per_page)
    return success_response(data=[e.to_dict() for e in items], meta=meta)


@scheme_enrollments_bp.post("/")
@jwt_required()
def create_enrollment():
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be JSON.", 400)

    worker_id, worker_name = _current_asha_context()
    if worker_id and not json_data.get("asha_id"):
        json_data["asha_id"] = worker_id
    if worker_name and not json_data.get("asha_worker_name"):
        json_data["asha_worker_name"] = worker_name

    try:
        enrollment = _input_schema.load(json_data, session=db.session)
    except ValidationError as err:
        return error_response("Validation failed.", 422, errors=err.messages)

    try:
        db.session.add(enrollment)
        db.session.commit()
        logger.info("Scheme enrollment saved to PostgreSQL: %s", enrollment.id)
        return success_response(
            data=enrollment.to_dict(),
            message="Beneficiary enrolled successfully.",
            status_code=201,
        )
    except Exception as exc:
        db.session.rollback()
        logger.exception("Create scheme enrollment error: %s", exc)
        return error_response(str(exc), 500)


@scheme_enrollments_bp.get("/<enrollment_id>")
@jwt_required()
def get_enrollment(enrollment_id):
    enrollment = SchemeEnrollment.query.get(enrollment_id)
    if not enrollment:
        return error_response("Enrollment not found.", 404)
    return success_response(data=enrollment.to_dict())


@scheme_enrollments_bp.delete("/<enrollment_id>")
@jwt_required()
def delete_enrollment(enrollment_id):
    enrollment = SchemeEnrollment.query.get(enrollment_id)
    if not enrollment:
        return error_response("Enrollment not found.", 404)
    try:
        db.session.delete(enrollment)
        db.session.commit()
        return success_response(message="Enrollment deleted.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Delete scheme enrollment error: %s", exc)
        return error_response(str(exc), 500)
