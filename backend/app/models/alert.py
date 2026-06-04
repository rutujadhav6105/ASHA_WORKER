"""
app/models/alert.py
====================
Alert/notification model for supervisor messages and system alerts.

Supports:
  • Supervisor messages to ASHA workers
  • System alerts (high-risk, vaccine due, medicine low)
  • Read/unread status tracking
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Index, Text

from app.extensions import db


class AlertMessage(db.Model):
    """System alerts and supervisor messages to ASHA workers."""

    __tablename__ = "alert_messages"

    __table_args__ = (
        Index("idx_alert_asha_id",     "asha_id"),
        Index("idx_alert_status",      "is_read"),
        Index("idx_alert_type",        "alert_type"),
        Index("idx_alert_created",     "created_at"),
    )

    id              = db.Column(db.String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Who it's for
    asha_id         = db.Column(db.String(50),  nullable=False, index=True)   # soft FK → users.worker_id
    
    # Message content
    title           = db.Column(db.String(200), nullable=False)
    message         = db.Column(Text, nullable=False)
    alert_type      = db.Column(db.String(50),  nullable=False, default="general")  # general, supervisor, vaccine_due, high_risk, medicine_low
    
    # Priority & status
    severity        = db.Column(db.String(20),  nullable=False, default="info")     # info, warning, danger
    is_read         = db.Column(db.Boolean, default=False)
    action_taken    = db.Column(db.Boolean, default=False)
    
    # Metadata
    expires_at      = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at      = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at      = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "asha_id":      self.asha_id,
            "title":        self.title,
            "message":      self.message,
            "alert_type":   self.alert_type,
            "severity":     self.severity,
            "is_read":      self.is_read,
            "action_taken": self.action_taken,
            "expires_at":   self.expires_at.isoformat() if self.expires_at else None,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
            "updated_at":   self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Alert {self.alert_type} – {self.title} to {self.asha_id}>"
