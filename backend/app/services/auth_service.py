"""
app/services/auth_service.py
==============================
Auth helper service — uses SQLAlchemy (UserModel) only.

NOTE: The old sqlite3 `get_db()` approach has been removed.
All persistence now goes through the SQLAlchemy session managed
by Flask-SQLAlchemy (app.extensions.db).
"""

from flask import current_app
from flask_jwt_extended import create_access_token

from app.extensions import bcrypt, db
from app.models.user import UserModel


def login_user(mobile: str, password: str):
    """
    Authenticate a user by mobile + password.

    Returns (response_dict, http_status_code).
    """
    user = UserModel.query.filter_by(mobile=mobile).first()

    if not user:
        return {"status": "error", "message": "Invalid credentials"}, 401

    if not bcrypt.check_password_hash(user.password_hash, password):
        return {"status": "error", "message": "Invalid credentials"}, 401

    if not user.is_active:
        return {"status": "error", "message": "Account is deactivated"}, 403

    token = create_access_token(identity=user.id)

    return {
        "status": "success",
        "message": "Login successful",
        "data": {
            "access_token": token,
            "user": user.to_dict(),
        },
    }, 200


def seed_admin():
    """
    Ensure at least one admin account exists in the database.
    Called once at startup inside the app context.
    """
    existing = UserModel.query.filter_by(mobile="0000000000").first()
    if existing:
        return  # already seeded

    hashed = bcrypt.generate_password_hash("admin123").decode("utf-8")
    admin = UserModel(
        name="System Admin",
        mobile="0000000000",
        email="admin@nhm.gov.in",
        role="admin",
        worker_id="ADMIN001",
        password_hash=hashed,
        is_active=True,
    )
    db.session.add(admin)
    db.session.commit()
    current_app.logger.info("✅  Default admin seeded (mobile=0000000000, password=admin123)")
