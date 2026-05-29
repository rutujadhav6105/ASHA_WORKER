"""
app/schemas/user_schema.py
===========================
Marshmallow schemas for UserModel.
"""

from marshmallow import fields, validate

from app.extensions import ma
from app.models.user import UserModel

VALID_ROLES = ["admin", "supervisor", "asha"]


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_instance = True
        exclude       = ("password_hash",)  # never serialise the hash

    role   = fields.String(required=True, validate=validate.OneOf(VALID_ROLES))
    mobile = fields.String(validate=validate.Length(max=15), load_default=None)
    email  = fields.Email(load_default=None)


class RegisterSchema(ma.Schema):
    """Input schema for registration (includes raw password)."""
    name      = fields.String(required=True, validate=validate.Length(min=2, max=100))
    mobile    = fields.String(required=True, validate=validate.Length(min=10, max=15))
    email     = fields.Email(load_default=None)
    password  = fields.String(required=True, validate=validate.Length(min=6))
    role      = fields.String(required=True, validate=validate.OneOf(VALID_ROLES))
    worker_id = fields.String(load_default=None)
    area      = fields.String(load_default=None)
    district  = fields.String(load_default=None)
    supervisor_id = fields.String(load_default=None)


class LoginSchema(ma.Schema):
    """Input schema for login."""
    mobile   = fields.String(required=True)
    password = fields.String(required=True)


user_schema    = UserSchema()
users_schema   = UserSchema(many=True)
register_schema = RegisterSchema()
login_schema   = LoginSchema()
