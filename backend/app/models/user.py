from sqlalchemy import func
"""
app/models/user.py
===================
User model: Admin, Supervisor, ASHA worker.

Changes in v2.0 (PostgreSQL migration):
  - Added __table_args__ with explicit indexes and CHECK constraint
  - Kept String(36) UUID primary key for SQLAlchemy compatibility
  - supervisor_id kept as soft-FK (string) to avoid circular FK dependency
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Index, func

from app.extensions import db


class UserModel(db.Model):
    """
    Represents a system user.

    Roles:
        admin       – full access
        supervisor  – manages a set of ASHA workers
        asha        – field health worker
    """

    __tablename__ = "users"

    __table_args__ = (
        # DB-level role constraint (belt-and-suspenders alongside Marshmallow)
        CheckConstraint(
            "role IN ('admin', 'supervisor', 'asha')",
            name="chk_users_role",
        ),
        # Indexes — declared here so db.create_all() creates them automatically
        Index("idx_users_role",      "role"),
        Index("idx_users_district",  "district"),
        Index("idx_users_is_active", "is_active"),
    )

    # ── Columns ────────────────────────────────────────────────────────────
    id            = db.Column(db.String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    name          = db.Column(db.String(100), nullable=False)
    mobile        = db.Column(db.String(15),  nullable=True, unique=True, index=True)
    email         = db.Column(db.String(100), nullable=True, unique=True)
    role          = db.Column(db.String(20),  nullable=False)          # admin / supervisor / asha
    worker_id     = db.Column(db.String(50),  nullable=True, unique=True)
    supervisor_id = db.Column(db.String(50),  nullable=True)           # soft FK to another user's worker_id
    area          = db.Column(db.String(100), nullable=True)
    district      = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active     = db.Column(db.Boolean,     default=True, nullable=False)
    created_at    = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at    = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (__table_args__ or ()) + (db.Index('idx_users_created_at', 'created_at'),)

    # ── Helpers ─────────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "id":            self.id,
            "name":          self.name,
            "mobile":        self.mobile,
            "email":         self.email,
            "role":          self.role,
            "worker_id":     self.worker_id,
            "supervisor_id": self.supervisor_id,
            "area":          self.area,
            "district":      self.district,
            "is_active":     self.is_active,
            "created_at":    self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.name} ({self.role})>"
