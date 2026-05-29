"""
app/schemas/family_planning_schema.py
=======================================
Marshmallow schemas for FamilyPlanningRecord.
"""

from marshmallow import fields, validate

from app.extensions import ma
from app.models.family_planning import CONTRACEPTIVE_METHODS, FamilyPlanningRecord

FP_STATUSES = ["active", "discontinued", "completed", "follow_up"]


class FamilyPlanningSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model         = FamilyPlanningRecord
        load_instance = True
        include_fk    = True

    beneficiary_name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    asha_id          = fields.String(required=True)
    method           = fields.String(
        validate=validate.OneOf(CONTRACEPTIVE_METHODS),
        load_default="None",
    )
    status = fields.String(
        validate=validate.OneOf(FP_STATUSES),
        load_default="active",
    )
    age = fields.Integer(
        validate=validate.Range(min=10, max=60),
        load_default=None,
        allow_none=True,
    )


fp_schema  = FamilyPlanningSchema()
fps_schema = FamilyPlanningSchema(many=True)
