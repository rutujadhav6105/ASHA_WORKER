from sqlalchemy import func
"""
app/models/anc.py
==================
Antenatal Care (ANC) records for pregnant beneficiaries.

Changes in v2.0 (PostgreSQL migration):
  - Added __table_args__ with indexes on asha_id, risk_status, edd
  - Added partial index hint via Index (actual partial handled in migrate.sql)
  - Added CHECK constraint on risk_status
  - DateTime columns now use timezone=True (TIMESTAMPTZ)

Note: asha_id is stored as a plain string (soft FK) to avoid requiring
a unique index on users.worker_id before table creation. Referential
integrity is enforced at the application layer.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Index, func

from app.extensions import db


class ANCRecord(db.Model):
    """ANC visit/registration record."""

    __tablename__ = "anc_records"

    __table_args__ = (
        CheckConstraint(
            "risk_status IN ('Normal', 'Low Risk', 'High Risk')",
            name="chk_anc_risk_status",
        ),
        CheckConstraint(
            "gravida IS NULL OR gravida >= 0",
            name="chk_anc_gravida",
        ),
        Index("idx_anc_asha_id",     "asha_id"),
        Index("idx_anc_risk_status", "risk_status"),
        Index("idx_anc_edd",         "edd"),
        Index("idx_anc_area",     "area"),
    )

    id               = db.Column(db.String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    name               = db.Column(db.String(100), nullable=False)
    husband_name     = db.Column(db.String(100), nullable=True)
    lmp              = db.Column(db.Date,        nullable=True)   # Last Menstrual Period
    edd              = db.Column(db.Date,        nullable=True)   # Expected Delivery Date
    gravida          = db.Column(db.Integer,     nullable=True)   # number of pregnancies
    risk_status      = db.Column(db.String(20),  default="Normal")
    mobile           = db.Column(db.String(15),  nullable=True)
    area             = db.Column(db.String(100), nullable=True)
    asha_id          = db.Column(db.String(50),  nullable=True)   # soft FK → users.worker_id
    created_at       = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at       = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id":               self.id,
            "name":               self.name,
            "husband_name":     self.husband_name,
            "lmp":              self.lmp.isoformat() if self.lmp else None,
            "edd":              self.edd.isoformat() if self.edd else None,
            "gravida":          self.gravida,
            "risk_status":      self.risk_status,
            "mobile":           self.mobile,
            "area":             self.area,
            "asha_id":          self.asha_id,
            "created_at":       self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<ANCRecord {self.name}>"
