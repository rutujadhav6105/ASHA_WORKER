"""Scheme enrollment model - PostgreSQL."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Index

from app.extensions import db


class SchemeEnrollment(db.Model):
    __tablename__ = "scheme_enrollments"

    __table_args__ = (
        Index("idx_scheme_enroll_asha_id", "asha_id"),
        Index("idx_scheme_enroll_scheme", "scheme_name"),
        Index("idx_scheme_enroll_district", "district"),
        Index("idx_scheme_enroll_created", "created_at"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_name = db.Column(db.String(200), nullable=False)
    beneficiary_name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), nullable=False)
    aadhaar_number = db.Column(db.String(20), nullable=True)
    village = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    asha_id = db.Column(db.String(50), nullable=True)
    asha_worker_name = db.Column(db.String(100), nullable=False)
    enrollment_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="Enrolled")
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scheme_name": self.scheme_name,
            "beneficiary_name": self.beneficiary_name,
            "mobile_number": self.mobile_number,
            "aadhaar_number": self.aadhaar_number or "",
            "village": self.village,
            "district": self.district,
            "asha_id": self.asha_id,
            "asha_worker_name": self.asha_worker_name,
            "enrollment_date": self.enrollment_date.isoformat()
            if self.enrollment_date
            else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
