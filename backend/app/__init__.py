"""

================
Application factory. Returns a fully-configured Flask app instance.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import uuid
from flask import Flask, jsonify, request, g
import sys
sys.stdout.reconfigure(encoding='utf-8')
from flask_cors import CORS
from sqlalchemy import event
from sqlalchemy.orm import Session


from app.core.config import get_config
from app.extensions import bcrypt, db, jwt, ma, migrate

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# SQLAlchemy Session Event Listeners for Transaction Logging
# --------------------------------------------------------------------------
@event.listens_for(Session, "after_commit")
def receive_after_commit(session):
    logger.info("💾 Database transaction committed successfully.")


@event.listens_for(Session, "after_rollback")
def receive_after_rollback(session):
    logger.warning("↩️ Database transaction rolled back.")


def create_app(config_class=None):
    """Create and configure the Flask application."""

    app = Flask(__name__)

    # ---------------------------------------------------------------- Config
    cfg = config_class or get_config()
    app.config.from_object(cfg)

    # Ensure JWT refresh tokens are long-lived (7 days by default)
    from datetime import timedelta
    if "JWT_REFRESH_TOKEN_EXPIRES" not in app.config:
        app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)

    # Ensure exports directory exists
    os.makedirs(app.config["EXPORTS_DIR"], exist_ok=True)

    # Ensure logs directory exists and configure rotating file handler
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
    os.makedirs(log_dir, exist_ok=True)
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        raise RuntimeError('DATABASE_URL is required for production.')
    log_level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'asha.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # ---------------------------------------------------------------- CORS
    # Enable CORS for all routes and origins - must be before blueprints
    CORS(
        app,
        origins=["*"],
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
        expose_headers=["Content-Type"],
        max_age=3600,
    )

    # ------------------------------------------------------------ Extensions
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)

    # --------------------------------------------------------- JWT callbacks
    # These replace Flask-JWT-Extended's default HTML error pages with the
    # same JSON envelope used by all other routes so Flutter can parse them.

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        logger.warning("🔒 Auth failure: Token has expired. Header: %s, Payload: %s", jwt_header, jwt_payload)
        return jsonify({
            "success": False,
            "message": "Token has expired.",
            "code": "token_expired",
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        logger.warning("🔒 Auth failure: Invalid token. Error: %s", error)
        return jsonify({
            "success": False,
            "message": "Invalid token.",
            "code": "invalid_token",
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        logger.warning("🔒 Auth failure: Missing token. Error: %s", error)
        return jsonify({
            "success": False,
            "message": "Authentication token is required.",
            "code": "authorization_required",
        }), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        logger.warning("🔒 Auth failure: Token has been revoked. Header: %s, Payload: %s", jwt_header, jwt_payload)
        return jsonify({
            "success": False,
            "message": "Token has been revoked.",
            "code": "token_revoked",
        }), 401

    # ------------------------------------------------------------ Request logging
    @app.before_request
    def log_request_info():
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        g.request_id = request_id
        logger.info("API Request", extra={"method": request.method, "path": request.path, "remote_addr": request.remote_addr, "request_id": request_id})

    @app.after_request
    def log_response_info(response):
        if response.status_code >= 400:
            logger.error("API Failure response: %s %s status %s", request.method, request.path, response.status_code)
        else:
            logger.info("API Response: %s %s status %s", request.method, request.path, response.status_code)
        return response

    # -------------------------------------------------------------- Models
    with app.app_context():
        from app.models import (  # noqa: F401
            anc, children, family, user, vaccine, family_planning, visit,
            scheme_enrollment,
        )
        db.create_all()
        from app.services.auth_service import seed_admin
        seed_admin()

    # -------------------------------------------------------------- CLI Commands
    @app.cli.command("create-db")
    def create_db_command():
        """Create all database tables."""
        db.create_all()
        print("✅ Database tables created successfully.")

    @app.cli.command("seed-admin")
    def seed_admin_command():
        """Seed default admin user."""
        from app.services.auth_service import seed_admin
        seed_admin()
        print("✅ Admin seed completed.")

    # ---------------------------------------- Ensure session cleanup on teardown
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if exception:
            db.session.rollback()
        db.session.remove()

    # ------------------------------------------------------------ Blueprints
    _register_blueprints(app)

    # ------------------------------------------------- Global error handlers
    _register_error_handlers(app)

    # ----------------------------------------------------------------- Health
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "asha-seva-backend"}), 200

    logger.info("ASHA Seva backend ready (env=%s)", os.getenv("FLASK_ENV", "development"))
    return app


# --------------------------------------------------------------------------
# Private helpers
# --------------------------------------------------------------------------

def _register_blueprints(app: Flask) -> None:
    """Register all route blueprints."""
    from app.routes.auth import auth_bp
    from app.routes.family import family_bp
    from app.routes.anc import anc_bp
    from app.routes.children import children_bp
    from app.routes.vaccine import vaccine_bp
    from app.routes.csv_routes import csv_bp
    from app.routes.visits import visits_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.family_planning import family_planning_bp
    from app.routes.reports import reports_bp
    from app.routes.vaccination import vaccination_bp
    from app.routes.scheme_enrollments import scheme_enrollments_bp

    # Core NHM Routes
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(family_bp, url_prefix="/api/families")
    app.register_blueprint(family_bp, url_prefix="/api/beneficiaries", name="beneficiaries") # alias mapping
    app.register_blueprint(anc_bp, url_prefix="/api/anc")
    app.register_blueprint(children_bp, url_prefix="/api/children")
    app.register_blueprint(children_bp, url_prefix="/api/child-health", name="child_health") # alias mapping
    app.register_blueprint(vaccine_bp, url_prefix="/api/vaccines")
    app.register_blueprint(csv_bp, url_prefix="/api")

    # Newly fully integrated blueprints
    app.register_blueprint(visits_bp, url_prefix="/api/visits")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(family_planning_bp, url_prefix="/api/family-planning")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
    app.register_blueprint(vaccination_bp, url_prefix="/api/vaccination")
    app.register_blueprint(scheme_enrollments_bp, url_prefix="/api/scheme-enrollments")


def _register_error_handlers(app: Flask) -> None:
    """Uniform JSON error responses for common HTTP errors."""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"success": False, "message": str(e)}), 400

    @app.errorhandler(401)
    def unauthorised(e):
        return jsonify({"success": False, "message": "Unauthorised"}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"success": False, "message": "Forbidden"}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "message": "Method not allowed"}), 405

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"success": False, "message": str(e)}), 422

    @app.errorhandler(500)
    def internal(e):
        logger.exception("Unhandled exception: %s", e)
        return jsonify({"success": False, "message": "Internal server error"}), 500