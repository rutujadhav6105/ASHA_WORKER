"""Marshmallow schema for SchemeEnrollment."""

from marshmallow import fields, validate

from app.extensions import ma
from app.models.scheme_enrollment import SchemeEnrollment


class SchemeEnrollmentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SchemeEnrollment
        load_instance = True
        include_fk = True

    scheme_name = fields.String(required=True, validate=validate.Length(min=2, max=200))
    beneficiary_name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    mobile_number = fields.String(required=True, validate=validate.Length(min=10, max=15))
    aadhaar_number = fields.String(load_default="", allow_none=True)
    village = fields.String(required=True, validate=validate.Length(min=1, max=100))
    district = fields.String(required=True, validate=validate.Length(min=1, max=100))
    asha_worker_name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    asha_id = fields.String(load_default=None, allow_none=True)
    enrollment_date = fields.Date(required=True)
    status = fields.String(load_default="Enrolled")


scheme_enrollment_schema = SchemeEnrollmentSchema()
scheme_enrollments_schema = SchemeEnrollmentSchema(many=True)
