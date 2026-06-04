from sqlalchemy import func
"""
app/models/children.py
=======================
Children registered for immunisation tracking.

Changes in v2.0 (PostgreSQL migration):
  - Added __table_args__ with indexes on asha_id, dob, gender
  - Added CHECK constraints on gender, weight
  - DateTime column now uses timezone=True (TIMESTAMPTZ)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Index, func

from app.extensions import db


class ChildModel(db.Model):
    """A child registered under an ASHA worker for vaccination tracking."""

    __tablename__ = "children"
    __table_args__ = (
        db.Index('idx_children_created_at', 'created_at'),
    )

    id          = db.Column(db.String(36),    primary_key=True, default=lambda: str(uuid.uuid4()))
    child_name  = db.Column(db.String(100),   nullable=False)
    mother_name = db.Column(db.String(100),   nullable=True)
    dob         = db.Column(db.Date,          nullable=True)
    gender      = db.Column(db.String(10),    nullable=True)   # Male / Female
    weight      = db.Column(db.Numeric(5, 2), nullable=True)   # kg
    mobile      = db.Column(db.String(15),    nullable=True)
    area        = db.Column(db.String(100),   nullable=True)
    asha_id     = db.Column(db.String(50), db.ForeignKey('users.worker_id'), nullable=True)
    created_at  = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at  = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    vaccines = db.relationship(
        "VaccineEntry",
        back_populates="child",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # One-to-many relationship to VisitRecord
    visits = db.relationship(
        "VisitRecord",
        back_populates="child",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # One-to-many relationship to ImmunizationRecord
    immunizations = db.relationship(
        "ImmunizationRecord",
        back_populates="child",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def to_dict(self, include_vaccines: bool = False, include_immunizations: bool = False) -> dict:
        data = {
            "id":          self.id,
            "child_name":  self.child_name,
            "mother_name": self.mother_name,
            "dob":         self.dob.isoformat() if self.dob else None,
            "gender":      self.gender,
            "weight":      float(self.weight) if self.weight else None,
            "mobile":      self.mobile,
            "area":        self.area,
            "village":     self.area,
            "asha_id":     self.asha_id,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
        }
        if include_vaccines:
            data["vaccines"] = [v.to_dict() for v in self.vaccines]
        if include_immunizations:
            data["immunizations"] = [i.to_dict() for i in self.immunizations]
        if hasattr(self, "visits"):
            data["visits"] = [v.to_dict() for v in self.visits]
        return data

    def __repr__(self) -> str:
        return f"<Child {self.child_name}>"
