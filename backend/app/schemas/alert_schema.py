"""
app/schemas/alert_schema.py
===========================
Alert/message validation schema.
"""

from marshmallow import Schema, fields, validate, pre_load, post_load

from app.models.alert import AlertMessage


class AlertSchema(Schema):
    """Validation schema for alert messages."""

    id            = fields.String(dump_only=True)
    asha_id       = fields.String(required=True, validate=validate.Length(min=2, max=50))
    title         = fields.String(required=True, validate=validate.Length(min=2, max=200))
    message       = fields.String(required=True, validate=validate.Length(min=5))
    alert_type    = fields.String(
        load_default="general",
        validate=validate.OneOf(["general", "supervisor", "vaccine_due", "high_risk", "medicine_low"]),
    )
    severity      = fields.String(
        load_default="info",
        validate=validate.OneOf(["info", "warning", "danger"]),
    )
    is_read       = fields.Boolean(load_default=False)
    action_taken  = fields.Boolean(load_default=False)
    expires_at    = fields.DateTime(allow_none=True)
    created_at    = fields.DateTime(dump_only=True)
    updated_at    = fields.DateTime(dump_only=True)

    @pre_load
    def normalize_asha_id(self, data, **kwargs):
        """Ensure asha_id is present and normalized."""
        if 'asha_id' in data and data['asha_id']:
            data['asha_id'] = str(data['asha_id']).strip()
        return data

    @post_load
    def create_alert(self, data, **kwargs):
        """Create AlertMessage instance from validated data."""
        return AlertMessage(**data)

    class Meta:
        ordered = True


# Instantiate schemas
alert_schema  = AlertSchema()
alerts_schema = AlertSchema(many=True)
