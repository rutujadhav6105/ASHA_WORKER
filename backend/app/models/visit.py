"""
app/models/visit.py
====================
Visit records — any home/facility visit made by an ASHA worker.

Covers:
  • Maternal health check-in visits (type='maternal')
  • Child health visits            (type='child')
  • General / follow-up visits     (type='general')
  • Family planning counselling    (type='family_planning')

Relationships (soft FKs to keep the schema flexible):
  • asha_id      → users.worker_id
  • beneficiary_id can reference family_members.id (optional, nullable)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Index, Text

from app.extensions import db


class VisitRecord(db.Model):
    """A visit conducted by an ASHA worker."""

    __tablename__ = "visit_records"

    __table_args__ = (
        CheckConstraint(
            "visit_type IN ('maternal','child','general','family_planning','immunization')",
            name="chk_visit_type",
        ),
        CheckConstraint(
            "status IN ('scheduled','completed','missed','cancelled')",
            name="chk_visit_status",
        ),
        Index("idx_visit_asha_id",       "asha_id"),
        Index("idx_visit_type",          "visit_type"),
        Index("idx_visit_status",        "status"),
        Index("idx_visit_date",          "visit_date"),
        Index("idx_visit_beneficiary",   "beneficiary_id"),
        Index("idx_visit_child_id",      "child_id"),
    )

    id              = db.Column(db.String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))

    # Who conducted / scheduled it
    asha_id         = db.Column(db.String(50),  nullable=False, index=True)   # soft FK → users.worker_id
    child_id        = db.Column(db.String(36), db.ForeignKey('children.id'), nullable=True)   # FK to ChildModel (optional)

    # Beneficiary (optional: could be a family or individual)
    beneficiary_id  = db.Column(db.String(36),  nullable=True)   # soft FK → family_members.id
    beneficiary_name= db.Column(db.String(100), nullable=False)
    village         = db.Column(db.String(100), nullable=True)

    # Visit metadata
    visit_type      = db.Column(db.String(30),  nullable=False, default="general")
    visit_date      = db.Column(db.Date,        nullable=False)
    status          = db.Column(db.String(20),  nullable=False, default="completed")

    # Clinical notes & observations
    notes           = db.Column(Text, nullable=True)
    weight_kg       = db.Column(db.Numeric(5, 2), nullable=True)
    bp_systolic     = db.Column(db.Integer,     nullable=True)   # mmHg
    bp_diastolic    = db.Column(db.Integer,     nullable=True)
    temperature_c   = db.Column(db.Numeric(4, 1), nullable=True)

    # Medicine / referral
    medicines_given = db.Column(Text, nullable=True)   # comma-separated or JSON string
    referred        = db.Column(db.Boolean, default=False)
    referral_notes  = db.Column(Text, nullable=True)

    # Next appointment
    next_visit_date = db.Column(db.Date, nullable=True)

    created_at      = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at      = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship to child
    child = db.relationship('ChildModel', back_populates='visits')

    def to_dict(self) -> dict:
        return {
            "id":               self.id,
            "asha_id":          self.asha_id,
            "beneficiary_id":   self.beneficiary_id,
            "beneficiary_name": self.beneficiary_name,
            "village":          self.village,
            "visit_type":       self.visit_type,
            "visit_date":       self.visit_date.isoformat() if self.visit_date else None,
            "status":           self.status,
            "notes":            self.notes,
            "weight_kg":        float(self.weight_kg) if self.weight_kg else None,
            "bp_systolic":      self.bp_systolic,
            "bp_diastolic":     self.bp_diastolic,
            "temperature_c":    float(self.temperature_c) if self.temperature_c else None,
            "medicines_given":  self.medicines_given,
            "referred":         self.referred,
            "referral_notes":   self.referral_notes,
            "next_visit_date":  self.next_visit_date.isoformat() if self.next_visit_date else None,
            "created_at":       self.created_at.isoformat() if self.created_at else None,
            "updated_at":       self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Visit {self.visit_type} – {self.beneficiary_name} on {self.visit_date}>"
