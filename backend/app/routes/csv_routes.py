"""
app/routes/csv_routes.py
=========================
CSV export and import endpoints.

Endpoints:
  GET  /api/export/<table_name>      – export table to CSV, returns the file
  POST /api/import/<table_name>      – import a CSV file into the table
  GET  /api/tables                   – list tables available for import/export

Export sample response (file download):
  Content-Type: text/csv
  Content-Disposition: attachment; filename="families.csv"

Import sample response (POST /api/import/families):
{
    "success": true,
    "message": "Import complete.",
    "data": {
        "table": "families",
        "total_rows": 50,
        "inserted": 45,
        "duplicates": 5,
        "errors": []
    }
}

Supported tables:
  users, families, family_members, anc_records, children, vaccine_entries
"""

import logging
import os
import tempfile

from flask import Blueprint, send_file, request, current_app
from flask_jwt_extended import jwt_required

from app.utils.csv_utils import (
    available_tables,
    export_table_to_csv,
    import_csv_to_table,
)
from app.utils.response import error_response, success_response

logger = logging.getLogger(__name__)
csv_bp = Blueprint("csv", __name__)


# --------------------------------------------------------------------------
# GET /api/tables  – discovery endpoint
# --------------------------------------------------------------------------

@csv_bp.get("/tables")
@jwt_required()
def list_tables():
    """
    Return all table names that support CSV import/export.

    Sample response:
    {
        "success": true,
        "data": ["users", "families", "family_members", "anc_records", "children", "vaccine_entries"]
    }
    """
    return success_response(data=available_tables(), message="Available tables.")


# --------------------------------------------------------------------------
# GET /api/export/<table_name>
# --------------------------------------------------------------------------

@csv_bp.get("/export/<string:table_name>")
@jwt_required()
def export_table(table_name: str):
    """
    Export all rows from *table_name* as a downloadable UTF-8 CSV file.

    Example:
        GET /api/export/families
        → downloads families.csv

    On error:
    {
        "success": false,
        "message": "Table 'xyz' not supported.",
        "data": null
    }
    """
    try:
        filepath = export_table_to_csv(table_name)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except RuntimeError as exc:
        logger.exception("Export error for table '%s': %s", table_name, exc)
        return error_response(str(exc), 500)

    logger.info("Serving export: %s", filepath)
    return send_file(
        filepath,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"{table_name}.csv",
    )


# --------------------------------------------------------------------------
# POST /api/import/<table_name>
# --------------------------------------------------------------------------

@csv_bp.post("/import/<string:table_name>")
@jwt_required()
def import_table(table_name: str):
    """
    Import rows from an uploaded CSV file into *table_name*.

    Request:
        Content-Type: multipart/form-data
        file: <csv-file>

    The endpoint:
      1. Validates the table name.
      2. Saves the uploaded file to a temp location.
      3. Reads & validates column headers.
      4. Skips duplicate rows (based on unique keys for that table).
      5. Inserts new rows and commits.
      6. Returns a summary.

    Sample success response:
    {
        "success": true,
        "message": "Import complete.",
        "data": {
            "table": "families",
            "total_rows": 50,
            "inserted": 45,
            "duplicates": 5,
            "errors": ["Row 12: aadhaar must be 12 digits"]
        }
    }
    """
    # Validate table name first (fast fail before touching the file)
    if table_name not in available_tables():
        return error_response(
            f"Table '{table_name}' not supported. "
            f"Available: {available_tables()}",
            400,
        )

    # Validate file upload
    if "file" not in request.files:
        return error_response("No file part in the request. Use key 'file'.", 400)

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return error_response("No file selected.", 400)

    if not uploaded_file.filename.lower().endswith(".csv"):
        return error_response("Only .csv files are accepted.", 400)

    # Save to a temporary file so pandas can read it
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".csv",
            delete=False,
            mode="wb",
        ) as tmp:
            uploaded_file.save(tmp)
            tmp_path = tmp.name

        result = import_csv_to_table(table_name, tmp_path)

    except ValueError as exc:
        return error_response(str(exc), 400)
    except RuntimeError as exc:
        logger.exception("Import error for table '%s': %s", table_name, exc)
        return error_response(str(exc), 500)
    finally:
        # Always clean up the temp file
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # Determine HTTP status: 207 Multi-Status if there were row-level errors
    status = 207 if result.get("errors") else 200
    return success_response(
        data={"table": table_name, **result},
        message=(
            f"Import complete. {result['inserted']} inserted, "
            f"{result['duplicates']} duplicates skipped."
        ),
        status_code=status,
    )
