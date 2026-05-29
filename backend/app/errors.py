from flask import jsonify, current_app
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

def _format_error(message: str, status: int, errors=None):
    payload = {
        "success": False,
        "message": message,
        "errors": errors or []
    }
    return jsonify(payload), status

def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return _format_error("Validation failed", 400, err.messages)

    @app.errorhandler(404)
    def handle_404(err):
        return _format_error("Resource not found", 404)

    @app.errorhandler(400)
    def handle_400(err):
        return _format_error("Bad request", 400)

    @app.errorhandler(401)
    def handle_401(err):
        return _format_error("Unauthorized", 401)

    @app.errorhandler(500)
    def handle_500(err):
        current_app.logger.exception(err)
        return _format_error("Internal server error", 500)

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return _format_error(err.description or "Error", err.code or 500)
