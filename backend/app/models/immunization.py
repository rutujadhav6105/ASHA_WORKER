from sqlalchemy import func
# Immunization record model – tracks individual vaccine doses administered to a child.

import uuid
from datetime import datetime, timezone

from sqlalchemy import Index, CheckConstraint, func

from app.extensions import db


class ImmunizationRecord(db.Model):
    """One immunization dose linked to a child.

    Fields:
        id               – primary key (UUID string)
        child_id         – FK to children.id (CASCADE delete)
        vaccine_id       – FK to vaccine_entries.id (CASCADE delete)
        vaccine_name     – name of the vaccine (historical snapshot)
        dose_number      – integer dose order
        due_date         – when the dose is due
        administered_date– when actually given
        status           – scheduled | due | given | overdue | missed | cancelled
        notes            – free‑form text
        created_at       – timestamp
        updated_at       – timestamp on update
    """

    __tablename__ = "immunization_records"

    __table_args__ = (
        # Basic indexes
        Index("idx_immunization_child_id", "child_id"),
        Index("idx_immunization_due_date", "due_date"),
        Index("idx_immunization_status", "status"),
        Index("idx_immunization_vaccine_name", "vaccine_name"),
        # Composite indexes for dashboard queries
        Index("idx_immun_child_status", "child_id", "status"),
        Index("idx_immun_child_due", "child_id", "due_date"),
        # Status enum constraint
        CheckConstraint(
            "status IN ('scheduled', 'due', 'given', 'overdue', 'missed', 'cancelled')",
            name="chk_immunization_status",
        ),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    child_id = db.Column(db.String(36), db.ForeignKey('children.id', ondelete='CASCADE'), nullable=False)
    vaccine_id = db.Column(db.String(36), db.ForeignKey('vaccine_entries.id', ondelete='CASCADE'), nullable=True)
    vaccine_name = db.Column(db.String(100), nullable=False)
    dose_number = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    administered_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default="scheduled", nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    child = db.relationship(
        'ChildModel',
        back_populates='immunizations',
        passive_deletes=True,
    )
    vaccine = db.relationship(
        'VaccineEntry',
        backref='immunization_records',
        lazy='select',
        passive_deletes=True,
    )

    def to_dict(
        self,
        include_child: bool = False,
        include_vaccine: bool = False,
    ) -> dict:
        data = {
            "id": self.id,
            "child_id": self.child_id,
            "vaccine_id": self.vaccine_id,
            "vaccine_name": self.vaccine_name,
            "dose_number": self.dose_number,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "administered_date": self.administered_date.isoformat() if self.administered_date else None,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_child and hasattr(self, "child") and self.child:
            data["child"] = self.child.to_dict()
        if include_vaccine and hasattr(self, "vaccine") and self.vaccine:
            data["vaccine"] = self.vaccine.to_dict()
        return data

    def __repr__(self) -> str:
        return f"<Immunization {self.vaccine_name} dose {self.dose_number} for child {self.child_id}>"
