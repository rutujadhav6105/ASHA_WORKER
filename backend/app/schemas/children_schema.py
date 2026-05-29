"""
app/schemas/children_schema.py
================================
Marshmallow schemas for ChildModel and VaccineEntry.
"""

from marshmallow import fields, validate

from app.extensions import ma
from app.models.children import ChildModel
from app.models.vaccine import VaccineEntry


class VaccineEntrySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = VaccineEntry
        load_instance = True
        include_fk    = True

    status = fields.String(
        validate=validate.OneOf(["scheduled", "due", "given", "overdue"]),
        load_default="scheduled",
    )


class ChildSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ChildModel
        load_instance = True
        include_fk    = True

    child_name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    gender     = fields.String(validate=validate.OneOf(["Male", "Female"]), load_default=None)
    vaccines   = fields.Nested(VaccineEntrySchema, many=True, dump_only=True)


child_schema     = ChildSchema()
children_schema  = ChildSchema(many=True)
vaccine_schema   = VaccineEntrySchema()
vaccines_schema  = VaccineEntrySchema(many=True)
