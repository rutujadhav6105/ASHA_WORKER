"""
app/schemas/family_schema.py
=============================
Marshmallow schemas for Family and FamilyMember.
Used for:
  • Serialising ORM objects → JSON (dump)
  • Validating & deserialising request JSON → Python dicts (load)
"""

from marshmallow import fields, validate, validates, ValidationError

from app.extensions import ma
from app.models.family import FamilyMemberModel, FamilyModel


class FamilyMemberSchema(ma.SQLAlchemyAutoSchema):
    """Schema for FamilyMemberModel."""

    class Meta:
        model = FamilyMemberModel
        load_instance = True
        include_fk    = True   # include family_id in serialised output

    # Extra validation
    gender = fields.String(
        validate=validate.OneOf(["Male", "Female", "Other"]),
        load_default=None,
    )
    apl_bpl = fields.String(
        validate=validate.OneOf(["APL", "BPL"]),
        load_default="APL",
    )
    aadhaar = fields.String(
        validate=validate.Length(equal=12),
        load_default=None,
        allow_none=True,
    )

    @validates("age")
    def validate_age(self, value):
        if value is not None and (value < 0 or value > 150):
            raise ValidationError("Age must be between 0 and 150.")


class FamilySchema(ma.SQLAlchemyAutoSchema):
    """Schema for FamilyModel (without nested members by default)."""

    class Meta:
        model = FamilyModel
        load_instance = True
        include_fk    = True

    family_head = fields.String(required=True, validate=validate.Length(min=2, max=100))
    village     = fields.String(load_default=None)


class FamilyWithMembersSchema(FamilySchema):
    """Extended schema that nests family members."""
    members = fields.Nested(FamilyMemberSchema, many=True, dump_only=True)


# Singleton instances used in routes
family_schema              = FamilySchema()
families_schema            = FamilySchema(many=True)
family_with_members_schema = FamilyWithMembersSchema()
family_member_schema       = FamilyMemberSchema()
family_members_schema      = FamilyMemberSchema(many=True)
