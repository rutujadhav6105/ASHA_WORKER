"""
app/models/vaccine.py
======================
Vaccine entries for a child.

Changes in v2.0 (PostgreSQL migration):
  - Added __table_args__ with indexes and unique composite constraint
  - Added CHECK constraint on status
  - DateTime column now uses timezone=True (TIMESTAMPTZ)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Index, UniqueConstraint, func

from app.extensions import db


class VaccineEntry(db.Model):
    """One vaccine dose linked to a child."""

    __tablename__ = "vaccine_entries"

    __table_args__ = (
        # Business rule: same vaccine should not be scheduled twice for the same child on the same due date
        UniqueConstraint("child_id", "name", "due_date", name="uq_child_vaccine_due"),
        CheckConstraint(
            "status IN ('scheduled', 'due', 'given', 'overdue')",
            name="chk_vaccine_status",
        ),
        Index("idx_vaccine_child_id",  "child_id"),
        Index("idx_vaccine_status",    "status"),
        Index("idx_vaccine_due_date",  "due_date"),
    )

    id         = db.Column(db.String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    child_id   = db.Column(db.String(36),  db.ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    name       = db.Column(db.String(100), nullable=False)     # BCG, OPV-0, HepB, etc.
    due_date   = db.Column(db.Date,        nullable=True)
    given_date = db.Column(db.Date,        nullable=True)
    next_due   = db.Column(db.Date,        nullable=True)
    # status: scheduled | due | given | overdue
    status     = db.Column(db.String(20),  default="scheduled")
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    child = db.relationship('ChildModel', back_populates='vaccines')

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "child_id":   self.child_id,
            "name":       self.name,
            "due_date":   self.due_date.isoformat()   if self.due_date   else None,
            "given_date": self.given_date.isoformat() if self.given_date else None,
            "next_due":   self.next_due.isoformat()   if self.next_due   else None,
            "status":     self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Vaccine {self.name} – {self.status}>"
