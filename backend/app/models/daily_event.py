from sqlalchemy import func
from app.extensions import db


class DailyEvent(db.Model):
    __tablename__ = "daily_events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    asha_id = db.Column(db.String(50), nullable=True, index=True)
    data = db.Column(db.JSON, nullable=False)
    created_by = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "asha_id": self.asha_id,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
