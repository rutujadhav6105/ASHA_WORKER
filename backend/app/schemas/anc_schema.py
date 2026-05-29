"""
app/schemas/anc_schema.py
==========================
Marshmallow schemas for ANCRecord.
"""

from marshmallow import fields, validate

from app.extensions import ma
from app.models.anc import ANCRecord


class ANCSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ANCRecord
        load_instance = True
        include_fk    = True

    beneficiary_name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    risk_status      = fields.String(
        validate=validate.OneOf(["Normal", "Low Risk", "High Risk"]),
        load_default="Normal",
    )
    lmp = fields.Date(load_default=None)
    edd = fields.Date(load_default=None)


anc_schema  = ANCSchema()
ancs_schema = ANCSchema(many=True)
