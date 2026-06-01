"""
app/routes/dashboard.py
========================
Dashboard aggregation API — all backed by live PostgreSQL data.

Endpoints
---------
GET /api/dashboard/summary              – KPI headline cards
GET /api/dashboard/beneficiaries        – beneficiary breakdown
GET /api/dashboard/pregnant-women       – ANC / pregnancy stats
GET /api/dashboard/vaccinated-children  – vaccination coverage
GET /api/dashboard/pending-visits       – pending & overdue visits
GET /api/dashboard/recent-activities    – activity feed
GET /api/dashboard/charts/monthly-trend    – line/bar chart data
GET /api/dashboard/charts/visit-types      – pie chart: visit distribution
GET /api/dashboard/charts/risk-distribution – pie chart: ANC risk
GET /api/dashboard/charts/vaccination      – stacked bar: vaccine status

All endpoints:
  • JWT-protected  (@jwt_required)
  • Accept optional ?asha_id= query param
  • Return { success, message, data, meta: { last_updated } }
"""

import logging
from datetime import datetime, timezone

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.dashboard_service import (
    get_beneficiary_stats,
    get_monthly_trend,
    get_pending_visits,
    get_pregnant_women_stats,
    get_recent_activities,
    get_risk_distribution,
    get_summary_stats,
    get_vaccinated_children_stats,
    get_vaccination_coverage_chart,
    get_visit_type_distribution,
)
from app.utils.response import error_response, success_response

logger       = logging.getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _meta(extra: dict | None = None) -> dict:
    m = {"last_updated": _now_iso()}
    if extra:
        m.update(extra)
    return m


def _asha_param() -> str | None:
    """Extract optional ?asha_id= from query string."""
    return request.args.get("asha_id") or None


# ---------------------------------------------------------------------------
# 1. Summary / KPI cards
# ---------------------------------------------------------------------------

@dashboard_bp.get("/summary")
@jwt_required()
def summary():
    """
    Headline KPI cards:
    families, beneficiaries, pregnant women, children, vaccines,
    visits (pending / completed / missed), family planning active.
    """
    asha_id = _asha_param()
    try:
        data = get_summary_stats(asha_id=asha_id)
        return success_response(
            data=data,
            message="Dashboard summary fetched successfully.",
            meta=_meta({"scope": asha_id or "all"}),
        )
    except Exception as exc:
        logger.exception("Dashboard summary error: %s", exc)
        return error_response("Failed to fetch dashboard summary.", 500)


# ---------------------------------------------------------------------------
# 2. Beneficiary breakdown
# ---------------------------------------------------------------------------

@dashboard_bp.get("/beneficiaries")
@jwt_required()
def beneficiaries():
    """Beneficiary breakdown by gender, APL/BPL status, reproductive pairs."""
    asha_id = _asha_param()
    try:
        data = get_beneficiary_stats(asha_id=asha_id)
        return success_response(
            data=data,
            message="Beneficiary stats fetched successfully.",
            meta=_meta({"scope": asha_id or "all"}),
        )
    except Exception as exc:
        logger.exception("Beneficiary stats error: %s", exc)
        return error_response("Failed to fetch beneficiary stats.", 500)


# ---------------------------------------------------------------------------
# 3. Pregnant women / ANC
# ---------------------------------------------------------------------------

@dashboard_bp.get("/pregnant-women")
@jwt_required()
def pregnant_women():
    """ANC / pregnancy stats: risk breakdown, EDD buckets, high-risk list."""
    asha_id = _asha_param()
    try:
        data = get_pregnant_women_stats(asha_id=asha_id)
        return success_response(
            data=data,
            message="Pregnant women stats fetched successfully.",
            meta=_meta({"scope": asha_id or "all"}),
        )
    except Exception as exc:
        logger.exception("Pregnant women stats error: %s", exc)
        return error_response("Failed to fetch pregnant women stats.", 500)


# ---------------------------------------------------------------------------
# 4. Vaccinated children
# ---------------------------------------------------------------------------

@dashboard_bp.get("/vaccinated-children")
@jwt_required()
def vaccinated_children():
    """
    Vaccination coverage: fully/partially/unvaccinated counts,
    coverage %, per-vaccine breakdown, overdue children list.
    """
    asha_id = _asha_param()
    try:
        data = get_vaccinated_children_stats(asha_id=asha_id)
        return success_response(
            data=data,
            message="Vaccination stats fetched successfully.",
            meta=_meta({"scope": asha_id or "all"}),
        )
    except Exception as exc:
        logger.exception("Vaccinated children stats error: %s", exc)
        return error_response("Failed to fetch vaccination stats.", 500)


# ---------------------------------------------------------------------------
# 5. Pending visits
# ---------------------------------------------------------------------------

@dashboard_bp.get("/pending-visits")
@jwt_required()
def pending_visits():
    """
    Upcoming scheduled visits and overdue visits.

    Query params:
      asha_id  – filter to one worker
      days     – look-ahead window (default 30, max 365)
    """
    asha_id = _asha_param()
    days    = request.args.get("days", 30, type=int)
    if days < 1 or days > 365:
        return error_response("days must be between 1 and 365.", 400)

    try:
        data = get_pending_visits(asha_id=asha_id, days=days)
        return success_response(
            data=data,
            message="Pending visits fetched successfully.",
            meta=_meta({"scope": asha_id or "all", "look_ahead_days": days}),
        )
    except Exception as exc:
        logger.exception("Pending visits error: %s", exc)
        return error_response("Failed to fetch pending visits.", 500)


# ---------------------------------------------------------------------------
# 6. Recent activities feed
# ---------------------------------------------------------------------------

@dashboard_bp.get("/recent-activities")
@jwt_required()
def recent_activities():
    """
    Unified chronological feed merged from ANC, visits, children, families,
    and vaccine administrations.

    Query params:
      asha_id  – filter to one worker
      limit    – max items (default 20, max 100)
    """
    asha_id = _asha_param()
    limit   = request.args.get("limit", 20, type=int)
    if limit < 1 or limit > 100:
        return error_response("limit must be between 1 and 100.", 400)

    try:
        data = get_recent_activities(asha_id=asha_id, limit=limit)
        return success_response(
            data=data,
            message="Recent activities fetched successfully.",
            meta=_meta({"scope": asha_id or "all", "limit": limit, "returned": len(data)}),
        )
    except Exception as exc:
        logger.exception("Recent activities error: %s", exc)
        return error_response("Failed to fetch recent activities.", 500)


# ---------------------------------------------------------------------------
# 7. Charts – monthly trend
# ---------------------------------------------------------------------------

@dashboard_bp.get("/charts/monthly-trend")
@jwt_required()
def chart_monthly_trend():
    """
    Monthly trend for line/bar chart.
    Returns visits_completed, anc_registrations, children_registered per month.

    Query params:
      months  – how many months back (default 6, max 24)
    """
    asha_id = _asha_param()
    months  = request.args.get("months", 6, type=int)
    if months < 1 or months > 24:
        return error_response("months must be between 1 and 24.", 400)

    try:
        data = get_monthly_trend(asha_id=asha_id, months=months)
        return success_response(
            data=data,
            message="Monthly trend data fetched successfully.",
            meta=_meta({"scope": asha_id or "all", "months": months}),
        )
    except Exception as exc:
        logger.exception("Monthly trend error: %s", exc)
        return error_response("Failed to fetch monthly trend.", 500)


# ---------------------------------------------------------------------------
# 8. Charts – visit type distribution
# ---------------------------------------------------------------------------

@dashboard_bp.get("/charts/visit-types")
@jwt_required()
def chart_visit_types():
    """Visit count by visit_type for a pie/donut chart."""
    asha_id = _asha_param()
    try:
        data = get_visit_type_distribution(asha_id=asha_id)
        return success_response(
            data=data,
            message="Visit type distribution fetched successfully.",
            meta=_meta({"scope": asha_id or "all"}),
        )
    except Exception as exc:
        logger.exception("Visit type distribution error: %s", exc)
        return error_response("Failed to fetch visit type distribution.", 500)


# ---------------------------------------------------------------------------
# 9. Charts – ANC risk distribution
# ---------------------------------------------------------------------------

@dashboard_bp.get("/charts/risk-distribution")
@jwt_required()
def chart_risk_distribution():
    """ANC risk status counts for a bar/pie chart."""
    asha_id = _asha_param()
    try:
        data = get_risk_distribution(asha_id=asha_id)
        return success_response(
            data=data,
            message="Risk distribution fetched successfully.",
            meta=_meta({"scope": asha_id or "all"}),
        )
    except Exception as exc:
        logger.exception("Risk distribution error: %s", exc)
        return error_response("Failed to fetch risk distribution.", 500)


# ---------------------------------------------------------------------------
# 10. Charts – vaccination status
# ---------------------------------------------------------------------------

@dashboard_bp.get("/charts/vaccination")
@jwt_required()
def chart_vaccination():
    """Vaccine entry counts by status for a stacked bar or donut chart."""
    asha_id = _asha_param()
    try:
        data = get_vaccination_coverage_chart(asha_id=asha_id)
        return success_response(
            data=data,
            message="Vaccination chart data fetched successfully.",
            meta=_meta({"scope": asha_id or "all"}),
        )
    except Exception as exc:
        logger.exception("Vaccination chart error: %s", exc)
        return error_response("Failed to fetch vaccination chart data.", 500)


# ---------------------------------------------------------------------------
# 11. Aggregates (Frontend compatibility fallback)
# ---------------------------------------------------------------------------

@dashboard_bp.route("/aggregates", methods=["GET", "OPTIONS"])
def dashboard_aggregates():
    if request.method == "OPTIONS":
        return {}, 200

    asha_id = _asha_param()
    try:
        summary = get_summary_stats(asha_id=asha_id)
        data = {
            "beneficiaries":       summary.get("total_beneficiaries", 0),
            "pregnancies":         summary.get("pregnant_women", 0),
            "high_risk_pregnancies": summary.get("high_risk_pregnancies", 0),
            "visits":              summary.get("total_visits", 0),
            "vaccinations":        summary.get("vaccinated_children", 0),
            "overdue_vaccinations": summary.get("overdue_vaccines", 0),
            "family_planning":     summary.get("fp_active", 0),
        }
        return success_response(
            data=data,
            message="Dashboard aggregates fetched successfully.",
            meta=_meta({"scope": asha_id or "all"}),
        )
    except Exception as exc:
        logger.exception("Dashboard aggregates error: %s", exc)
        return error_response("Failed to fetch dashboard aggregates.", 500)
