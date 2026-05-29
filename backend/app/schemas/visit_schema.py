"""
app/schemas/visit_schema.py
============================
Marshmallow schemas for VisitRecord.
"""

from marshmallow import fields, validate

from app.extensions import ma
from app.models.visit import VisitRecord

VISIT_TYPES   = ["maternal", "child", "general", "family_planning", "immunization"]
VISIT_STATUSES = ["scheduled", "completed", "missed", "cancelled"]


class VisitSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model         = VisitRecord
        load_instance = True
        include_fk    = True

    beneficiary_name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    asha_id          = fields.String(required=True)
    child_id         = fields.String(required=False, allow_none=True)  # Optional: visits may not be for children
    visit_date       = fields.Date(required=True)
    visit_type       = fields.String(
        validate=validate.OneOf(VISIT_TYPES),
        load_default="general",
    )
    status = fields.String(
        validate=validate.OneOf(VISIT_STATUSES),
        load_default="completed",
    )
    weight_kg      = fields.Decimal(places=2, as_string=False, load_default=None, allow_none=True)
    temperature_c  = fields.Decimal(places=1, as_string=False, load_default=None, allow_none=True)


visit_schema  = VisitSchema()
visits_schema = VisitSchema(many=True)
