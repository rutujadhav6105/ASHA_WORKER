"""
app/utils/response.py
======================
Standardised JSON response helpers used by all routes.

Every API response follows this envelope:
{
    "success": bool,
    "message": str,          # human-readable
    "data":    any | null,   # payload on success
    "error":   str | null,   # error detail on failure
    "meta":    dict | null,  # optional pagination / stats
}
"""

from flask import jsonify


def success_response(
    data=None,
    message: str = "Success",
    status_code: int = 200,
    meta: dict | None = None,
    errors: list | None = None,
):
    """Return a 2xx JSON response with optional meta and errors list."""
    payload: dict = {"success": True, "message": message, "data": data, "errors": errors or []}
    if meta:
        payload["meta"] = meta
    return jsonify(payload), status_code


def error_response(
    message: str = "An error occurred",
    status_code: int = 400,
    errors: list | None = None,
):
    """Return a JSON error response with optional errors list."""
    payload: dict = {"success": False, "message": message, "data": None, "errors": errors or []}
    return jsonify(payload), status_code


def paginate_query(query, page: int, per_page: int):
    """
    Apply SQLAlchemy pagination and return (items, meta_dict).

    Usage in a route:
        items, meta = paginate_query(UserModel.query, page=1, per_page=20)
        return success_response(data=[u.to_dict() for u in items], meta=meta)
    """
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    meta = {
        "page":        paginated.page,
        "per_page":    paginated.per_page,
        "total":       paginated.total,
        "total_pages": paginated.pages,
        "has_next":    paginated.has_next,
        "has_prev":    paginated.has_prev,
    }
    return paginated.items, meta
