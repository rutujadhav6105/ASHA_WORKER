"""
app/routes/reports.py
======================
Reporting & Analytics API.

Endpoints:
  GET /api/reports/dashboard          – overall dashboard stats
  GET /api/reports/visits             – visit statistics
  GET /api/reports/maternal-health    – ANC / maternal stats
  GET /api/reports/child-health       – child / vaccination stats
  GET /api/reports/family-planning    – FP method distribution
  GET /api/reports/worker/<asha_id>   – per-worker performance report

All endpoints are JWT-protected and accept optional:
  from_date, to_date  (YYYY-MM-DD)
  asha_id
"""

import logging
from datetime import date, datetime
from io import BytesIO
import calendar

from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.extensions import db
from app.models.anc import ANCRecord
from app.models.children import ChildModel
from app.models.family import FamilyMemberModel, FamilyModel
from app.models.family_planning import FamilyPlanningRecord
from app.models.user import UserModel
from app.models.vaccine import VaccineEntry
from app.models.visit import VisitRecord
from app.utils.response import error_response, success_response

logger     = logging.getLogger(__name__)
reports_bp = Blueprint("reports", __name__)


def _date_filter(query, model_col, from_date_str, to_date_str):
    """Apply optional date range filters to a query."""
    if from_date_str:
        try:
            query = query.filter(model_col >= date.fromisoformat(from_date_str))
        except ValueError:
            pass
    if to_date_str:
        try:
            query = query.filter(model_col <= date.fromisoformat(to_date_str))
        except ValueError:
            pass
    return query


@reports_bp.get("/dashboard")
@jwt_required()
def dashboard_stats():
    """
    Overall system stats — useful for the admin/supervisor dashboard.
    Returns counts of users, families, ANC records, children, visits, FP records.
    """
    stats = {
        "total_asha_workers":     UserModel.query.filter_by(role="asha",  is_active=True).count(),
        "total_supervisors":      UserModel.query.filter_by(role="supervisor", is_active=True).count(),
        "total_families":         FamilyModel.query.count(),
        "total_family_members":   FamilyMemberModel.query.count(),
        "total_anc_records":      ANCRecord.query.count(),
        "high_risk_pregnancies":  ANCRecord.query.filter_by(risk_status="High Risk").count(),
        "total_children":         ChildModel.query.count(),
        "vaccines_given":         VaccineEntry.query.filter_by(status="given").count(),
        "vaccines_overdue":       VaccineEntry.query.filter_by(status="overdue").count(),
        "total_visits":           VisitRecord.query.count(),
        "visits_completed":       VisitRecord.query.filter_by(status="completed").count(),
        "total_fp_records":       FamilyPlanningRecord.query.count(),
        "fp_active":              FamilyPlanningRecord.query.filter_by(status="active").count(),
    }
    return success_response(data=stats)


@reports_bp.get("/visits")
@jwt_required()
def visits_report():
    """Visit breakdown by type and status, with optional date range + asha filter."""
    asha_id    = request.args.get("asha_id")
    from_date  = request.args.get("from_date")
    to_date    = request.args.get("to_date")

    query = db.session.query(
        VisitRecord.visit_type,
        VisitRecord.status,
        func.count(VisitRecord.id).label("count"),
    )
    if asha_id:
        query = query.filter(VisitRecord.asha_id == asha_id)
    query = _date_filter(query, VisitRecord.visit_date, from_date, to_date)
    rows  = query.group_by(VisitRecord.visit_type, VisitRecord.status).all()

    return success_response(data=[
        {"visit_type": r.visit_type, "status": r.status, "count": r.count}
        for r in rows
    ])


@reports_bp.get("/maternal-health")
@jwt_required()
def maternal_health_report():
    """ANC records grouped by risk_status, with EDD distribution."""
    asha_id   = request.args.get("asha_id")
    from_date = request.args.get("from_date")
    to_date   = request.args.get("to_date")

    query = db.session.query(
        ANCRecord.risk_status,
        func.count(ANCRecord.id).label("count"),
    )
    if asha_id:
        query = query.filter(ANCRecord.asha_id == asha_id)
    query = _date_filter(query, ANCRecord.created_at, from_date, to_date)
    risk_rows = query.group_by(ANCRecord.risk_status).all()

    # EDD in current month — expectant mothers due soon
    today  = date.today()
    due_soon = ANCRecord.query.filter(
        ANCRecord.edd >= today,
        ANCRecord.edd <= date(today.year, today.month, 28),
    )
    if asha_id:
        due_soon = due_soon.filter_by(asha_id=asha_id)

    return success_response(data={
        "by_risk_status": [{"risk_status": r.risk_status, "count": r.count} for r in risk_rows],
        "due_this_month": due_soon.count(),
    })


@reports_bp.get("/child-health")
@jwt_required()
def child_health_report():
    """Children count by gender + vaccination coverage summary."""
    asha_id = request.args.get("asha_id")

    gender_q = db.session.query(
        ChildModel.gender,
        func.count(ChildModel.id).label("count"),
    )
    if asha_id:
        gender_q = gender_q.filter(ChildModel.asha_id == asha_id)
    gender_rows = gender_q.group_by(ChildModel.gender).all()

    vax_q = db.session.query(
        VaccineEntry.status,
        func.count(VaccineEntry.id).label("count"),
    ).join(ChildModel, VaccineEntry.child_id == ChildModel.id)
    if asha_id:
        vax_q = vax_q.filter(ChildModel.asha_id == asha_id)
    vax_rows = vax_q.group_by(VaccineEntry.status).all()

    return success_response(data={
        "children_by_gender": [{"gender": r.gender, "count": r.count} for r in gender_rows],
        "vaccines_by_status": [{"status": r.status, "count": r.count} for r in vax_rows],
    })


@reports_bp.get("/family-planning")
@jwt_required()
def fp_report():
    """Family planning records by contraceptive method and status."""
    asha_id = request.args.get("asha_id")

    query = db.session.query(
        FamilyPlanningRecord.method,
        FamilyPlanningRecord.status,
        func.count(FamilyPlanningRecord.id).label("count"),
    )
    if asha_id:
        query = query.filter(FamilyPlanningRecord.asha_id == asha_id)
    rows = query.group_by(FamilyPlanningRecord.method, FamilyPlanningRecord.status).all()

    return success_response(data=[
        {"method": r.method, "status": r.status, "count": r.count}
        for r in rows
    ])


@reports_bp.get("/worker/<string:asha_id>")
@jwt_required()
def worker_report(asha_id: str):
    """Full performance snapshot for one ASHA worker."""
    worker = UserModel.query.filter_by(worker_id=asha_id).first()
    if not worker:
        return error_response("Worker not found.", 404)

    from_date = request.args.get("from_date")
    to_date   = request.args.get("to_date")

    def _count(model, col_name="asha_id"):
        q = model.query.filter(getattr(model, col_name) == asha_id)
        return q.count()

    visit_q = VisitRecord.query.filter_by(asha_id=asha_id)
    visit_q = _date_filter(visit_q, VisitRecord.visit_date, from_date, to_date)

    return success_response(data={
        "worker":               worker.to_dict(),
        "families_registered":  _count(FamilyModel),
        "anc_records":          _count(ANCRecord),
        "high_risk_anc":        ANCRecord.query.filter_by(asha_id=asha_id, risk_status="High Risk").count(),
        "children_registered":  _count(ChildModel),
        "vaccines_given":       db.session.query(func.count(VaccineEntry.id))
                                    .join(ChildModel, VaccineEntry.child_id == ChildModel.id)
                                    .filter(ChildModel.asha_id == asha_id, VaccineEntry.status == "given")
                                    .scalar() or 0,
        "total_visits":         visit_q.count(),
        "completed_visits":     VisitRecord.query.filter_by(asha_id=asha_id, status="completed").count(),
        "fp_counselled":        _count(FamilyPlanningRecord),
    })


def _parse_month(month_value: str) -> tuple[date, date]:
    """Return the first and last date for the requested month."""
    month_value = month_value.strip()
    try:
        # Accept YYYY-MM or YYYY-MM-DD
        parsed = datetime.fromisoformat(month_value)
        return date(parsed.year, parsed.month, 1), date(parsed.year, parsed.month, calendar.monthrange(parsed.year, parsed.month)[1])
    except ValueError:
        pass

    try:
        parsed = datetime.strptime(month_value, "%B %Y")
        return date(parsed.year, parsed.month, 1), date(parsed.year, parsed.month, calendar.monthrange(parsed.year, parsed.month)[1])
    except ValueError:
        pass

    try:
        parsed = datetime.strptime(month_value, "%b %Y")
        return date(parsed.year, parsed.month, 1), date(parsed.year, parsed.month, calendar.monthrange(parsed.year, parsed.month)[1])
    except ValueError:
        pass

    today = date.today()
    return date(today.year, today.month, 1), date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])


def _build_monthly_summary(start_date: date, end_date: date, asha_id: str | None = None) -> dict[str, int]:
    visits_q = VisitRecord.query.filter(VisitRecord.visit_date >= start_date, VisitRecord.visit_date <= end_date)
    anc_q = ANCRecord.query.filter(ANCRecord.created_at >= start_date, ANCRecord.created_at <= end_date)
    vaccine_q = db.session.query(func.count(VaccineEntry.id)).join(ChildModel, VaccineEntry.child_id == ChildModel.id).filter(
        VaccineEntry.status == "given",
        VaccineEntry.given_date >= start_date,
        VaccineEntry.given_date <= end_date,
    )

    if asha_id:
        visits_q = visits_q.filter(VisitRecord.asha_id == asha_id)
        anc_q = anc_q.filter(ANCRecord.asha_id == asha_id)
        vaccine_q = vaccine_q.filter(ChildModel.asha_id == asha_id)

    return {
        "visits": visits_q.count(),
        "anc": anc_q.count(),
        "vaccinations": vaccine_q.scalar() or 0,
    }


def _build_pdf_bytes(month_label: str, summary: dict[str, int]) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 24 * mm

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margin, height - margin, f"ASHA Monthly Report")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(margin, height - margin - 24, f"Month: {month_label}")
    pdf.line(margin, height - margin - 28, width - margin, height - margin - 28)

    y = height - margin - 60
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(margin, y, "Summary")
    pdf.setFont("Helvetica", 11)
    y -= 20

    for label, value in [
        ("Home Visits", summary["visits"]),
        ("ANC Cases", summary["anc"]),
        ("Vaccinations Given", summary["vaccinations"]),
    ]:
        pdf.drawString(margin, y, f"{label}: {value}")
        y -= 18

    y -= 10
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(margin, y, "Notes")
    y -= 18
    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin, y, "Generated by ASHA Worker App backend.")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


@reports_bp.get("/monthly-pdf")
@jwt_required()
def monthly_report_pdf():
    """Generate a monthly report PDF and return it as a downloadable file."""
    month_value = request.args.get("month", "")
    asha_id = request.args.get("asha_id")

    start_date, end_date = _parse_month(month_value)
    summary = _build_monthly_summary(start_date, end_date, asha_id)

    month_label = month_value.strip() or start_date.strftime("%B %Y")
    if not month_label:
        month_label = start_date.strftime("%B %Y")

    pdf_bytes = _build_pdf_bytes(month_label, summary)
    filename = f"asha_monthly_report_{start_date.strftime('%Y_%m')}.pdf"

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )
