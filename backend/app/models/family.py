"""
app/models/family.py
=====================
FamilyModel  – one household
FamilyMemberModel – individuals belonging to a household

Changes in v2.0 (PostgreSQL migration):
  - Added __table_args__ with indexes on asha_id, village, district
  - Added CHECK constraints on gender, apl_bpl, age
  - DateTime columns now use timezone=True for TIMESTAMPTZ in PostgreSQL
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Index

from app.extensions import db


class FamilyModel(db.Model):
    """
    Represents a household registered by an ASHA worker.
    One family can have many family members (one-to-many).
    """

    __tablename__ = "families"

    __table_args__ = (
        Index("idx_families_asha_id",  "asha_id"),
        Index("idx_families_village",  "village"),
        Index("idx_families_district", "district"),
    )

    id          = db.Column(db.String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    home_no     = db.Column(db.String(20),  nullable=True)
    address     = db.Column(db.Text,        nullable=True)
    village     = db.Column(db.String(100), nullable=True)
    taluka      = db.Column(db.String(100), nullable=True)
    district    = db.Column(db.String(100), nullable=True)
    family_head = db.Column(db.String(100), nullable=False)
    asha_id     = db.Column(db.String(50),  nullable=True)   # soft FK → users.worker_id
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    __table_args__ = (__table_args__ or ()) + (db.Index('idx_families_created_at', 'created_at'),)

    # Relationship: list of members belonging to this family
    members = db.relationship(
        "FamilyMemberModel",
        backref="family",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def to_dict(self, include_members: bool = False) -> dict:
        data = {
            "id":          self.id,
            "home_no":     self.home_no,
            "address":     self.address,
            "village":     self.village,
            "taluka":      self.taluka,
            "district":    self.district,
            "family_head": self.family_head,
            "asha_id":     self.asha_id,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
        }
        if include_members:
            data["members"] = [m.to_dict() for m in self.members]
        return data

    def __repr__(self) -> str:
        return f"<Family {self.family_head} – {self.village}>"


class FamilyMemberModel(db.Model):
    """
    Represents an individual member within a household.
    """

    __tablename__ = "family_members"

    __table_args__ = (
        CheckConstraint("age IS NULL OR (age >= 0 AND age <= 150)", name="chk_member_age"),
        CheckConstraint("apl_bpl IN ('APL', 'BPL')",               name="chk_member_apl_bpl"),
        CheckConstraint("gender IN ('Male', 'Female', 'Other') OR gender IS NULL", name="chk_member_gender"),
        Index("idx_family_members_family_id", "family_id"),
        Index("idx_family_members_gender",    "gender"),
        Index("idx_family_members_rep_pair",  "is_reproductive_pair"),
    )

    id                   = db.Column(db.String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    family_id            = db.Column(db.String(36),  db.ForeignKey("families.id", ondelete="CASCADE"), nullable=False)
    name                 = db.Column(db.String(100), nullable=False)
    dob                  = db.Column(db.Date,        nullable=True)
    age                  = db.Column(db.Integer,     nullable=True)
    aadhaar              = db.Column(db.String(12),  nullable=True, unique=True)
    gender               = db.Column(db.String(10),  nullable=True)
    is_reproductive_pair = db.Column(db.Boolean,     default=False)
    caste                = db.Column(db.String(100), nullable=True)
    sub_caste            = db.Column(db.String(100), nullable=True)
    apl_bpl              = db.Column(db.String(5),   default="APL")
    education            = db.Column(db.String(100), nullable=True)
    created_at           = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id":                   self.id,
            "family_id":            self.family_id,
            "name":                 self.name,
            "dob":                  self.dob.isoformat() if self.dob else None,
            "age":                  self.age,
            "aadhaar":              self.aadhaar,
            "gender":               self.gender,
            "is_reproductive_pair": self.is_reproductive_pair,
            "caste":                self.caste,
            "sub_caste":            self.sub_caste,
            "apl_bpl":              self.apl_bpl,
            "education":            self.education,
            "created_at":           self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<FamilyMember {self.name} (family={self.family_id})>"
