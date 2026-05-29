"""
app/routes/auth.py
===================
Authentication routes:
  POST /api/auth/register/supervisor
  POST /api/auth/register/asha
  POST /api/auth/login
  GET  /api/auth/profile        (JWT required)
  PUT  /api/auth/profile        (JWT required)
  POST /api/auth/change-password (JWT required)

Sample success response (login):
{
    "success": true,
    "message": "Login successful",
    "data": {
        "access_token": "<jwt>",
        "user": { "id": "...", "name": "Priya", "role": "asha", ... }
    }
}
"""

import logging

from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from marshmallow import ValidationError

from app.extensions import bcrypt, db
from app.models.user import UserModel
from app.schemas.user_schema import (
    LoginSchema,
    RegisterSchema,
    user_schema,
)
from app.utils.response import error_response, success_response

logger   = logging.getLogger(__name__)
auth_bp  = Blueprint("auth", __name__)

_register_schema = RegisterSchema()
_login_schema    = LoginSchema()


# --------------------------------------------------------------------------
# POST /api/auth/register/supervisor
# POST /api/auth/register/asha
# --------------------------------------------------------------------------

def _register_user(role: str):
    """Shared registration logic for any role."""
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be JSON.", 400)

    # Force the role from the URL, not from the body
    json_data["role"] = role

    try:
        data = _register_schema.load(json_data)
    except ValidationError as err:
        return error_response("Validation failed.", 422, errors=err.messages)

    # Duplicate check on mobile
    if UserModel.query.filter_by(mobile=data["mobile"]).first():
        return error_response(f"Mobile number {data['mobile']} is already registered.", 409)

    # Duplicate check on email (if provided)
    if data.get("email") and UserModel.query.filter_by(email=data["email"]).first():
        return error_response("Email is already registered.", 409)

    try:
        hashed = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
        user = UserModel(
            name          = data["name"],
            mobile        = data["mobile"],
            email         = data.get("email"),
            role          = role,
            worker_id     = data.get("worker_id"),
            supervisor_id = data.get("supervisor_id"),
            area          = data.get("area"),
            district      = data.get("district"),
            password_hash = hashed,
        )
        db.session.add(user)
        db.session.commit()
        logger.info("New %s registered: %s", role, user.mobile)
        return success_response(
            data=user.to_dict(),
            message=f"{role.capitalize()} registered successfully.",
            status_code=201,
        )
    except Exception as exc:
        db.session.rollback()
        logger.exception("Registration error: %s", exc)
        return error_response(str(exc), 500)


@auth_bp.post("/register/supervisor")
def register_supervisor():
    return _register_user("supervisor")


@auth_bp.post("/register/asha")
def register_asha():
    return _register_user("asha")


@auth_bp.post("/register/admin")
def register_admin():
    return _register_user("admin")


# --------------------------------------------------------------------------
# POST /api/auth/login
# --------------------------------------------------------------------------

@auth_bp.post("/login")
def login():
    """
    Authenticate a user by mobile + password.

    Sample request:
        { "mobile": "9876543210", "password": "secret123" }

    Sample response (200):
        {
            "success": true,
            "message": "Login successful",
            "data": {
                "access_token": "<jwt>",
                "user": { "id": "...", "name": "Priya", "role": "asha" }
            }
        }
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be JSON.", 400)

    try:
        data = _login_schema.load(json_data)
    except ValidationError as err:
        return error_response("Validation failed.", 422, errors=err.messages)

    user = UserModel.query.filter_by(mobile=data["mobile"]).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, data["password"]):
        return error_response("Invalid mobile number or password.", 401)

    if not user.is_active:
        return error_response("Your account has been deactivated.", 403)

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict(),
        },
        message="Login successful.",
    )


@auth_bp.post('/refresh')
@jwt_required(refresh=True)
def refresh_token():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)
    return success_response(
        data={"access_token": new_access_token},
        message="Token refreshed successfully.",
    )


@auth_bp.post('/logout')
@jwt_required()
def logout():
    return success_response(message="Logged out successfully.")


# --------------------------------------------------------------------------
# GET/PUT /api/auth/profile
# --------------------------------------------------------------------------

@auth_bp.get("/profile")
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user    = db.session.get(UserModel, user_id)
    if not user:
        return error_response("User not found.", 404)
    return success_response(data=user.to_dict())


@auth_bp.put("/profile")
@jwt_required()
def update_profile():
    user_id   = get_jwt_identity()
    user      = db.session.get(UserModel, user_id)
    if not user:
        return error_response("User not found.", 404)

    data = request.get_json(silent=True) or {}
    # Only allow safe fields to be updated
    allowed = {"name", "mobile", "email", "area", "district"}
    for field in allowed:
        if field in data:
            setattr(user, field, data[field])

    try:
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(data=user.to_dict(), message="Profile updated.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Profile update error: %s", exc)
        return error_response(str(exc), 500)


# --------------------------------------------------------------------------
# POST /api/auth/change-password
# --------------------------------------------------------------------------

@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    user    = db.session.get(UserModel, user_id)
    if not user:
        return error_response("User not found.", 404)

    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return error_response("Both 'old_password' and 'new_password' are required.", 400)

    if not bcrypt.check_password_hash(user.password_hash, old_password):
        return error_response("Old password is incorrect.", 401)

    if len(new_password) < 6:
        return error_response("New password must be at least 6 characters.", 400)

    try:
        user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
        db.session.commit()
        logger.info("Data saved successfully")
        return success_response(message="Password changed successfully.")
    except Exception as exc:
        db.session.rollback()
        logger.exception("Password change error: %s", exc)
        return error_response(str(exc), 500)
