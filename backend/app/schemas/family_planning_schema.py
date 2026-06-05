"""
app/schemas/family_planning_schema.py
=======================================
Marshmallow schemas for FamilyPlanningRecord.
"""

from datetime import date, datetime
from marshmallow import fields, pre_load, validate

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
    husband_name     = fields.String(allow_none=True)
    mobile           = fields.String(allow_none=True)
    village          = fields.String(allow_none=True)
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
    method_start_date = fields.Date(allow_none=True, load_default=None)
    method_end_date = fields.Date(allow_none=True, load_default=None)
    counselling_date = fields.Date(allow_none=True, load_default=None)
    next_followup_date = fields.Date(allow_none=True, load_default=None)
    counselling_notes = fields.String(allow_none=True)
    side_effects = fields.String(allow_none=True)
    complications = fields.String(allow_none=True)
    followup_notes = fields.String(allow_none=True)
    living_children = fields.Integer(allow_none=True, load_default=None)

    @pre_load
    def preprocess(self, data, **kwargs):
        if not isinstance(data, dict):
            return data

        cleaned = {}
        for key, value in data.items():
            if isinstance(value, str):
                final = value.strip()
                cleaned[key] = None if final == '' else final
            else:
                cleaned[key] = value

        status = cleaned.get('status')
        if isinstance(status, str):
            final = status.lower().strip()
            if final in ('followup', 'follow_up', 'follow up'):
                cleaned['status'] = 'follow_up'
            elif final in ('ideal', 'normal', 'active'):
                cleaned['status'] = 'active'
            elif final in ('dropout', 'discontinued'):
                cleaned['status'] = 'discontinued'
            elif final in ('complete', 'completed'):
                cleaned['status'] = 'completed'

        def parse_date(value):
            if not isinstance(value, str):
                return value
            value = value.strip()
            if not value:
                return None
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            try:
                return datetime.fromisoformat(value).date()
            except ValueError:
                return value

        for field in (
            'method_start_date',
            'method_end_date',
            'counselling_date',
            'next_followup_date',
        ):
            if field in cleaned:
                cleaned[field] = parse_date(cleaned[field])

        # Coerce numeric fields sent as strings into integers where possible
        for num_field in ('age', 'living_children'):
            if num_field in cleaned and isinstance(cleaned[num_field], str):
                try:
                    cleaned[num_field] = int(cleaned[num_field])
                except (ValueError, TypeError):
                    cleaned[num_field] = None

        method = cleaned.get('method')
        if isinstance(method, str):
            raw_method = method.lower().strip()
            if 'condom' in raw_method:
                cleaned['method'] = 'Condom'
            elif 'iud' in raw_method:
                cleaned['method'] = 'IUCD'
            elif 'ocp' in raw_method or 'pill' in raw_method or 'oral' in raw_method:
                cleaned['method'] = 'OCP'
            elif 'inject' in raw_method:
                cleaned['method'] = 'Injectable'
            elif 'sterili' in raw_method or 'tube' in raw_method or 'vase' in raw_method:
                cleaned['method'] = 'Sterilization'
            elif raw_method == 'lam' or 'lam' in raw_method:
                cleaned['method'] = 'LAM'
            elif raw_method == 'nfp' or 'natural' in raw_method:
                cleaned['method'] = 'NFP'
            elif 'none' in raw_method:
                cleaned['method'] = 'None'
            else:
                cleaned['method'] = 'Other'

        return cleaned


fp_schema  = FamilyPlanningSchema()
fps_schema = FamilyPlanningSchema(many=True)
