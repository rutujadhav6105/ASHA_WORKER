"""
app/models/family_planning.py
==============================
Family planning records for reproductive-age couples.

Each record tracks a beneficiary's contraceptive method, counselling
history, and follow-up schedule.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Index, Text

from app.extensions import db

CONTRACEPTIVE_METHODS = [
    "OCP",          # Oral Contraceptive Pill
    "IUCD",         # Intra-Uterine Contraceptive Device
    "Condom",
    "Injectable",   # Depo-Provera etc.
    "Sterilization",
    "LAM",          # Lactational Amenorrhea Method
    "NFP",          # Natural Family Planning
    "None",
    "Other",
]


class FamilyPlanningRecord(db.Model):
    """Family planning counselling and contraceptive record."""

    __tablename__ = "family_planning_records"

    __table_args__ = (
        CheckConstraint(
            f"method IN ({','.join(repr(m) for m in CONTRACEPTIVE_METHODS)})",
            name="chk_fp_method",
        ),
        CheckConstraint(
            "status IN ('active','discontinued','completed','follow_up')",
            name="chk_fp_status",
        ),
        Index("idx_fp_asha_id",       "asha_id"),
        Index("idx_fp_beneficiary",   "beneficiary_name"),
        Index("idx_fp_method",        "method"),
        Index("idx_fp_status",        "status"),
        Index("idx_fp_next_follow",   "next_followup_date"),
    )

    id                  = db.Column(db.String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    asha_id             = db.Column(db.String(50),  nullable=False)   # soft FK → users.worker_id
    beneficiary_name    = db.Column(db.String(100), nullable=False)
    husband_name        = db.Column(db.String(100), nullable=True)
    mobile              = db.Column(db.String(15),  nullable=True)
    village             = db.Column(db.String(100), nullable=True)
    age                 = db.Column(db.Integer,     nullable=True)

    # Contraception
    method              = db.Column(db.String(30),  nullable=False, default="None")
    method_start_date   = db.Column(db.Date,        nullable=True)
    method_end_date     = db.Column(db.Date,        nullable=True)
    status              = db.Column(db.String(20),  nullable=False, default="active")

    # Counselling
    counselling_date    = db.Column(db.Date,        nullable=True)
    counselling_notes   = db.Column(Text,           nullable=True)

    # Side-effects / complications
    side_effects        = db.Column(Text,           nullable=True)
    complications       = db.Column(Text,           nullable=True)

    # Follow-up
    next_followup_date  = db.Column(db.Date,        nullable=True)
    followup_notes      = db.Column(Text,           nullable=True)

    # Number of living children
    living_children     = db.Column(db.Integer,     nullable=True)

    created_at          = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at          = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id":                  self.id,
            "asha_id":             self.asha_id,
            "beneficiary_name":    self.beneficiary_name,
            "husband_name":        self.husband_name,
            "mobile":              self.mobile,
            "village":             self.village,
            "age":                 self.age,
            "method":              self.method,
            "method_start_date":   self.method_start_date.isoformat()  if self.method_start_date  else None,
            "method_end_date":     self.method_end_date.isoformat()    if self.method_end_date    else None,
            "status":              self.status,
            "counselling_date":    self.counselling_date.isoformat()   if self.counselling_date   else None,
            "counselling_notes":   self.counselling_notes,
            "side_effects":        self.side_effects,
            "complications":       self.complications,
            "next_followup_date":  self.next_followup_date.isoformat() if self.next_followup_date else None,
            "followup_notes":      self.followup_notes,
            "living_children":     self.living_children,
            "created_at":          self.created_at.isoformat() if self.created_at else None,
            "updated_at":          self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<FamilyPlanning {self.beneficiary_name} – {self.method}>"
