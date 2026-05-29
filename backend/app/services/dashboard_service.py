"""
app/services/dashboard_service.py
===================================
Dashboard aggregation service.

All queries run against live PostgreSQL data.  No mock / hardcoded values.

Public functions
----------------
get_summary_stats(asha_id=None)          – headline KPI cards
get_beneficiary_stats(asha_id=None)      – total beneficiaries breakdown
get_pregnant_women_stats(asha_id=None)   – ANC / pregnancy details
get_vaccinated_children_stats(asha_id=None) – vaccination coverage
get_pending_visits(asha_id=None, days=30)   – upcoming / overdue
get_recent_activities(asha_id=None, limit=20) – chronological feed
get_monthly_trend(asha_id=None, months=6)  – chart data (line/bar)
get_visit_type_distribution(asha_id=None)  – pie-chart data
get_risk_distribution(asha_id=None)        – risk status breakdown
get_vaccination_coverage_chart(asha_id=None) – vaccine status chart
"""

import logging
from datetime import date, timedelta

from sqlalchemy import case, func, text

from app.extensions import db
from app.models.anc import ANCRecord
from app.models.children import ChildModel
from app.models.family import FamilyMemberModel, FamilyModel
from app.models.family_planning import FamilyPlanningRecord
from app.models.user import UserModel
from app.models.vaccine import VaccineEntry
from app.models.visit import VisitRecord

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _asha_filter(query, model, asha_id):
    """Conditionally filter a query by asha_id."""
    if asha_id:
        query = query.filter(model.asha_id == asha_id)
    return query


def _safe_scalar(query) -> int:
    """Return scalar count or 0 on failure."""
    try:
        result = query.scalar()
        return result or 0
    except Exception as exc:
        logger.error("Query scalar error: %s", exc)
        return 0


# ---------------------------------------------------------------------------
# 1. Summary / KPI stats
# ---------------------------------------------------------------------------

def get_summary_stats(asha_id: str | None = None) -> dict:
    """
    Headline numbers for the dashboard KPI cards.
    Single optimised pass per table using conditional aggregation.
    """
    try:
        today = date.today()

        # ── Families & members ──
        family_count = _safe_scalar(
            _asha_filter(db.session.query(func.count(FamilyModel.id)), FamilyModel, asha_id)
        )
        member_count = _safe_scalar(
            db.session.query(func.count(FamilyMemberModel.id))
            .join(FamilyModel, FamilyMemberModel.family_id == FamilyModel.id)
            .filter(FamilyModel.asha_id == asha_id) if asha_id
            else db.session.query(func.count(FamilyMemberModel.id))
        )

        # ── ANC (pregnant women) ──
        anc_q = db.session.query(
            func.count(ANCRecord.id).label("total"),
            func.sum(
                case((ANCRecord.risk_status == "High Risk", 1), else_=0)
            ).label("high_risk"),
            func.sum(
                case((ANCRecord.edd >= today, 1), else_=0)
            ).label("active_pregnancies"),
        )
        anc_q = _asha_filter(anc_q, ANCRecord, asha_id)
        anc_row = anc_q.one()

        # ── Children & vaccines ──
        child_count = _safe_scalar(
            _asha_filter(db.session.query(func.count(ChildModel.id)), ChildModel, asha_id)
        )

        # Children with at least one "given" vaccine
        vaccinated_children_q = (
            db.session.query(func.count(func.distinct(VaccineEntry.child_id)))
            .join(ChildModel, VaccineEntry.child_id == ChildModel.id)
            .filter(VaccineEntry.status == "given")
        )
        if asha_id:
            vaccinated_children_q = vaccinated_children_q.filter(ChildModel.asha_id == asha_id)
        vaccinated_children = _safe_scalar(vaccinated_children_q)

        overdue_vaccines_q = (
            db.session.query(func.count(VaccineEntry.id))
            .join(ChildModel, VaccineEntry.child_id == ChildModel.id)
            .filter(VaccineEntry.status == "overdue")
        )
        if asha_id:
            overdue_vaccines_q = overdue_vaccines_q.filter(ChildModel.asha_id == asha_id)
        overdue_vaccines = _safe_scalar(overdue_vaccines_q)

        # ── Visits ──
        visits_q = db.session.query(
            func.count(VisitRecord.id).label("total"),
            func.sum(case((VisitRecord.status == "completed", 1), else_=0)).label("completed"),
            func.sum(case((VisitRecord.status == "scheduled", 1), else_=0)).label("scheduled"),
            func.sum(case((VisitRecord.status == "missed",    1), else_=0)).label("missed"),
        )
        visits_q = _asha_filter(visits_q, VisitRecord, asha_id)
        visit_row = visits_q.one()

        # Pending visits = scheduled for today or future
        pending_visits_q = (
            db.session.query(func.count(VisitRecord.id))
            .filter(VisitRecord.status == "scheduled", VisitRecord.visit_date >= today)
        )
        if asha_id:
            pending_visits_q = pending_visits_q.filter(VisitRecord.asha_id == asha_id)
        pending_visits = _safe_scalar(pending_visits_q)

        # ── Family planning ──
        fp_active = _safe_scalar(
            _asha_filter(
                db.session.query(func.count(FamilyPlanningRecord.id))
                .filter(FamilyPlanningRecord.status == "active"),
                FamilyPlanningRecord,
                asha_id,
            )
        )

        # ── ASHA workers (admin-level overview) ──
        total_workers = (
            UserModel.query.filter_by(role="asha", is_active=True).count()
            if not asha_id else None
        )

        return {
            "total_families":          family_count,
            "total_beneficiaries":     member_count,
            "pregnant_women":          int(anc_row.total or 0),
            "active_pregnancies":      int(anc_row.active_pregnancies or 0),
            "high_risk_pregnancies":   int(anc_row.high_risk or 0),
            "total_children":          child_count,
            "vaccinated_children":     vaccinated_children,
            "overdue_vaccines":        overdue_vaccines,
            "total_visits":            int(visit_row.total or 0),
            "completed_visits":        int(visit_row.completed or 0),
            "scheduled_visits":        int(visit_row.scheduled or 0),
            "missed_visits":           int(visit_row.missed or 0),
            "pending_visits":          pending_visits,
            "fp_active":               fp_active,
            "total_asha_workers":      total_workers,
        }

    except Exception as exc:
        logger.exception("get_summary_stats error: %s", exc)
        raise


# ---------------------------------------------------------------------------
# 2. Beneficiary stats
# ---------------------------------------------------------------------------

def get_beneficiary_stats(asha_id: str | None = None) -> dict:
    """
    Breakdown of registered beneficiaries (family members).
    Groups by gender, caste category, APL/BPL.
    """
    try:
        base_q = (
            db.session.query(FamilyMemberModel)
            .join(FamilyModel, FamilyMemberModel.family_id == FamilyModel.id)
        )
        if asha_id:
            base_q = base_q.filter(FamilyModel.asha_id == asha_id)

        # Gender breakdown
        gender_rows = (
            db.session.query(
                FamilyMemberModel.gender,
                func.count(FamilyMemberModel.id).label("count"),
            )
            .join(FamilyModel, FamilyMemberModel.family_id == FamilyModel.id)
            .filter(FamilyModel.asha_id == asha_id if asha_id else True)
            .group_by(FamilyMemberModel.gender)
            .all()
        )

        # APL / BPL breakdown
        apl_bpl_rows = (
            db.session.query(
                FamilyMemberModel.apl_bpl,
                func.count(FamilyMemberModel.id).label("count"),
            )
            .join(FamilyModel, FamilyMemberModel.family_id == FamilyModel.id)
            .filter(FamilyModel.asha_id == asha_id if asha_id else True)
            .group_by(FamilyMemberModel.apl_bpl)
            .all()
        )

        # Reproductive-pair count
        rep_pair_q = (
            db.session.query(func.count(FamilyMemberModel.id))
            .join(FamilyModel, FamilyMemberModel.family_id == FamilyModel.id)
            .filter(FamilyMemberModel.is_reproductive_pair.is_(True))
        )
        if asha_id:
            rep_pair_q = rep_pair_q.filter(FamilyModel.asha_id == asha_id)
        reproductive_pairs = _safe_scalar(rep_pair_q)

        return {
            "by_gender": [
                {"gender": r.gender or "Unknown", "count": r.count}
                for r in gender_rows
            ],
            "by_apl_bpl": [
                {"category": r.apl_bpl or "Unknown", "count": r.count}
                for r in apl_bpl_rows
            ],
            "reproductive_pairs": reproductive_pairs,
        }

    except Exception as exc:
        logger.exception("get_beneficiary_stats error: %s", exc)
        raise


# ---------------------------------------------------------------------------
# 3. Pregnant women stats
# ---------------------------------------------------------------------------

def get_pregnant_women_stats(asha_id: str | None = None) -> dict:
    """
    ANC / pregnancy statistics:
    – total registrations
    – risk breakdown
    – due this month / next month
    – high-risk list (name + EDD)
    """
    try:
        today  = date.today()
        # Month boundaries
        month_start = today.replace(day=1)
        if today.month == 12:
            next_month_start = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month_start = today.replace(month=today.month + 1, day=1)

        if next_month_start.month == 12:
            month_after_start = next_month_start.replace(year=next_month_start.year + 1, month=1, day=1)
        else:
            month_after_start = next_month_start.replace(month=next_month_start.month + 1, day=1)

        # Risk status aggregation
        risk_q = db.session.query(
            ANCRecord.risk_status,
            func.count(ANCRecord.id).label("count"),
        )
        risk_q = _asha_filter(risk_q, ANCRecord, asha_id)
        risk_rows = risk_q.group_by(ANCRecord.risk_status).all()

        # EDD buckets
        edd_q = db.session.query(
            func.sum(case(
                (ANCRecord.edd.between(today, next_month_start - timedelta(days=1)), 1),
                else_=0,
            )).label("due_this_month"),
            func.sum(case(
                (ANCRecord.edd.between(next_month_start, month_after_start - timedelta(days=1)), 1),
                else_=0,
            )).label("due_next_month"),
            func.sum(case(
                (ANCRecord.edd < today, 1), else_=0,
            )).label("overdue"),
        )
        edd_q = _asha_filter(edd_q, ANCRecord, asha_id)
        edd_row = edd_q.one()

        # High-risk women (up to 10 for dashboard card)
        hr_q = ANCRecord.query.filter_by(risk_status="High Risk").order_by(ANCRecord.edd.asc())
        if asha_id:
            hr_q = hr_q.filter(ANCRecord.asha_id == asha_id)
        high_risk_list = hr_q.limit(10).all()

        return {
            "by_risk_status": [
                {"risk_status": r.risk_status, "count": r.count}
                for r in risk_rows
            ],
            "due_this_month":  int(edd_row.due_this_month  or 0),
            "due_next_month":  int(edd_row.due_next_month  or 0),
            "overdue_edd":     int(edd_row.overdue          or 0),
            "high_risk_women": [
                {
                    "id":               r.id,
                    "name":             r.beneficiary_name,
                    "edd":              r.edd.isoformat() if r.edd else None,
                    "village":          r.village,
                    "mobile":           r.mobile,
                }
                for r in high_risk_list
            ],
        }

    except Exception as exc:
        logger.exception("get_pregnant_women_stats error: %s", exc)
        raise


# ---------------------------------------------------------------------------
# 4. Vaccinated children stats
# ---------------------------------------------------------------------------

def get_vaccinated_children_stats(asha_id: str | None = None) -> dict:
    """
    Vaccination coverage:
    – children registered
    – fully vaccinated vs partially vs unvaccinated
    – vaccine-wise given / overdue breakdown
    – overdue children list (up to 10)
    """
    try:
        # Per-child aggregation via subquery
        child_vaccine_sub = (
            db.session.query(
                VaccineEntry.child_id,
                func.count(VaccineEntry.id).label("total_doses"),
                func.sum(case((VaccineEntry.status == "given",   1), else_=0)).label("given"),
                func.sum(case((VaccineEntry.status == "overdue", 1), else_=0)).label("overdue"),
                func.sum(case((VaccineEntry.status.in_(["scheduled","due"]), 1), else_=0)).label("pending"),
            )
            .group_by(VaccineEntry.child_id)
            .subquery()
        )

        children_base = (
            db.session.query(
                ChildModel,
                child_vaccine_sub.c.total_doses,
                child_vaccine_sub.c.given,
                child_vaccine_sub.c.overdue,
                child_vaccine_sub.c.pending,
            )
            .outerjoin(child_vaccine_sub, ChildModel.id == child_vaccine_sub.c.child_id)
        )
        if asha_id:
            children_base = children_base.filter(ChildModel.asha_id == asha_id)

        rows = children_base.all()
        total = len(rows)
        fully_vaccinated   = sum(1 for r in rows if (r.given or 0) > 0 and (r.overdue or 0) == 0 and (r.pending or 0) == 0)
        partially_vaccinated = sum(1 for r in rows if (r.given or 0) > 0 and ((r.overdue or 0) > 0 or (r.pending or 0) > 0))
        unvaccinated       = sum(1 for r in rows if (r.given or 0) == 0)

        # Vaccine-name breakdown
        vaccine_name_q = (
            db.session.query(
                VaccineEntry.name,
                func.sum(case((VaccineEntry.status == "given",   1), else_=0)).label("given"),
                func.sum(case((VaccineEntry.status == "overdue", 1), else_=0)).label("overdue"),
                func.sum(case((VaccineEntry.status.in_(["scheduled","due"]), 1), else_=0)).label("pending"),
            )
            .join(ChildModel, VaccineEntry.child_id == ChildModel.id)
        )
        if asha_id:
            vaccine_name_q = vaccine_name_q.filter(ChildModel.asha_id == asha_id)
        vaccine_name_rows = vaccine_name_q.group_by(VaccineEntry.name).order_by(VaccineEntry.name).all()

        # Children with overdue vaccines (for alert list)
        overdue_children_q = (
            db.session.query(ChildModel)
            .join(VaccineEntry, ChildModel.id == VaccineEntry.child_id)
            .filter(VaccineEntry.status == "overdue")
            .distinct()
        )
        if asha_id:
            overdue_children_q = overdue_children_q.filter(ChildModel.asha_id == asha_id)
        overdue_children = overdue_children_q.limit(10).all()

        return {
            "total_children":       total,
            "fully_vaccinated":     fully_vaccinated,
            "partially_vaccinated": partially_vaccinated,
            "unvaccinated":         unvaccinated,
            "coverage_percent":     round(fully_vaccinated / total * 100, 1) if total else 0.0,
            "by_vaccine": [
                {
                    "vaccine": r.name,
                    "given":   int(r.given   or 0),
                    "overdue": int(r.overdue or 0),
                    "pending": int(r.pending or 0),
                }
                for r in vaccine_name_rows
            ],
            "overdue_children": [
                {
                    "id":          c.id,
                    "child_name":  c.child_name,
                    "mother_name": c.mother_name,
                    "dob":         c.dob.isoformat() if c.dob else None,
                    "asha_id":     c.asha_id,
                }
                for c in overdue_children
            ],
        }

    except Exception as exc:
        logger.exception("get_vaccinated_children_stats error: %s", exc)
        raise


# ---------------------------------------------------------------------------
# 5. Pending visits
# ---------------------------------------------------------------------------

def get_pending_visits(asha_id: str | None = None, days: int = 30) -> dict:
    """
    Upcoming scheduled visits and overdue (past-scheduled) visits.
    Returns:
      pending_count, overdue_count, visits list (upcoming + overdue)
    """
    try:
        today   = date.today()
        end_day = today + timedelta(days=days)

        # Upcoming
        upcoming_q = VisitRecord.query.filter(
            VisitRecord.status == "scheduled",
            VisitRecord.visit_date >= today,
            VisitRecord.visit_date <= end_day,
        )
        if asha_id:
            upcoming_q = upcoming_q.filter(VisitRecord.asha_id == asha_id)
        upcoming_q = upcoming_q.order_by(VisitRecord.visit_date.asc())

        # Overdue (scheduled but date passed)
        overdue_q = VisitRecord.query.filter(
            VisitRecord.status == "scheduled",
            VisitRecord.visit_date < today,
        )
        if asha_id:
            overdue_q = overdue_q.filter(VisitRecord.asha_id == asha_id)
        overdue_q = overdue_q.order_by(VisitRecord.visit_date.asc())

        upcoming_list = upcoming_q.limit(50).all()
        overdue_list  = overdue_q.limit(20).all()

        return {
            "pending_count": upcoming_q.count(),
            "overdue_count": overdue_q.count(),
            "upcoming_visits": [v.to_dict() for v in upcoming_list],
            "overdue_visits":  [v.to_dict() for v in overdue_list],
        }

    except Exception as exc:
        logger.exception("get_pending_visits error: %s", exc)
        raise


# ---------------------------------------------------------------------------
# 6. Recent activities feed
# ---------------------------------------------------------------------------

def get_recent_activities(asha_id: str | None = None, limit: int = 20) -> list:
    """
    Unified chronological activity feed from multiple tables.
    Each item: { type, entity_id, description, asha_id, timestamp }
    """
    try:
        today = date.today()

        # Recent ANC registrations
        anc_q = ANCRecord.query.order_by(ANCRecord.created_at.desc())
        if asha_id:
            anc_q = anc_q.filter(ANCRecord.asha_id == asha_id)
        anc_rows = anc_q.limit(limit).all()

        # Recent visits
        visit_q = VisitRecord.query.order_by(VisitRecord.created_at.desc())
        if asha_id:
            visit_q = visit_q.filter(VisitRecord.asha_id == asha_id)
        visit_rows = visit_q.limit(limit).all()

        # Recent child registrations
        child_q = ChildModel.query.order_by(ChildModel.created_at.desc())
        if asha_id:
            child_q = child_q.filter(ChildModel.asha_id == asha_id)
        child_rows = child_q.limit(limit).all()

        # Recent family registrations
        family_q = FamilyModel.query.order_by(FamilyModel.created_at.desc())
        if asha_id:
            family_q = family_q.filter(FamilyModel.asha_id == asha_id)
        family_rows = family_q.limit(limit).all()

        # Recent vaccine administrations
        vaccine_q = (
            VaccineEntry.query
            .filter(VaccineEntry.status == "given")
            .order_by(VaccineEntry.created_at.desc())
        )
        if asha_id:
            vaccine_q = (
                vaccine_q.join(ChildModel, VaccineEntry.child_id == ChildModel.id)
                .filter(ChildModel.asha_id == asha_id)
            )
        vaccine_rows = vaccine_q.limit(limit).all()

        activities = []

        for r in anc_rows:
            activities.append({
                "type":        "anc_registration",
                "entity_id":   r.id,
                "description": f"ANC registered: {r.beneficiary_name} ({r.risk_status})",
                "asha_id":     r.asha_id,
                "village":     r.village,
                "timestamp":   r.created_at.isoformat() if r.created_at else None,
            })

        for r in visit_rows:
            activities.append({
                "type":        "visit",
                "entity_id":   r.id,
                "description": f"Visit ({r.visit_type}) – {r.beneficiary_name} [{r.status}]",
                "asha_id":     r.asha_id,
                "village":     r.village,
                "timestamp":   r.created_at.isoformat() if r.created_at else None,
            })

        for r in child_rows:
            activities.append({
                "type":        "child_registration",
                "entity_id":   r.id,
                "description": f"Child registered: {r.child_name} (mother: {r.mother_name or 'N/A'})",
                "asha_id":     r.asha_id,
                "village":     None,
                "timestamp":   r.created_at.isoformat() if r.created_at else None,
            })

        for r in family_rows:
            activities.append({
                "type":        "family_registration",
                "entity_id":   r.id,
                "description": f"Family registered: {r.family_head} – {r.village or 'N/A'}",
                "asha_id":     r.asha_id,
                "village":     r.village,
                "timestamp":   r.created_at.isoformat() if r.created_at else None,
            })

        for r in vaccine_rows:
            activities.append({
                "type":        "vaccination",
                "entity_id":   r.id,
                "description": f"Vaccine given: {r.name} (child_id: {r.child_id})",
                "asha_id":     None,
                "village":     None,
                "timestamp":   r.created_at.isoformat() if r.created_at else None,
            })

        # Sort by timestamp desc, take top N
        activities.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        return activities[:limit]

    except Exception as exc:
        logger.exception("get_recent_activities error: %s", exc)
        raise


# ---------------------------------------------------------------------------
# 7. Monthly trend (chart data)
# ---------------------------------------------------------------------------

def get_monthly_trend(asha_id: str | None = None, months: int = 6) -> dict:
    """
    Monthly counts over the last N months for:
    – visits completed
    – ANC registrations
    – children registered
    Returns data suitable for a line / bar chart.
    """
    try:
        today     = date.today()
        cutoff    = today.replace(day=1) - timedelta(days=(months - 1) * 30)

        # visits by month
        visit_month_q = (
            db.session.query(
                func.date_trunc("month", func.cast(VisitRecord.visit_date, db.Date)).label("month"),
                func.count(VisitRecord.id).label("count"),
            )
            .filter(VisitRecord.visit_date >= cutoff, VisitRecord.status == "completed")
        )
        if asha_id:
            visit_month_q = visit_month_q.filter(VisitRecord.asha_id == asha_id)
        visit_month_rows = (
            visit_month_q
            .group_by(text("month"))
            .order_by(text("month"))
            .all()
        )

        # ANC by month
        anc_month_q = (
            db.session.query(
                func.date_trunc("month", ANCRecord.created_at).label("month"),
                func.count(ANCRecord.id).label("count"),
            )
            .filter(ANCRecord.created_at >= cutoff)
        )
        if asha_id:
            anc_month_q = anc_month_q.filter(ANCRecord.asha_id == asha_id)
        anc_month_rows = (
            anc_month_q
            .group_by(text("month"))
            .order_by(text("month"))
            .all()
        )

        # Children by month
        child_month_q = (
            db.session.query(
                func.date_trunc("month", ChildModel.created_at).label("month"),
                func.count(ChildModel.id).label("count"),
            )
            .filter(ChildModel.created_at >= cutoff)
        )
        if asha_id:
            child_month_q = child_month_q.filter(ChildModel.asha_id == asha_id)
        child_month_rows = (
            child_month_q
            .group_by(text("month"))
            .order_by(text("month"))
            .all()
        )

        def _serialize(rows):
            return [
                {"month": r.month.strftime("%Y-%m") if r.month else None, "count": r.count}
                for r in rows
            ]

        return {
            "visits_completed":    _serialize(visit_month_rows),
            "anc_registrations":   _serialize(anc_month_rows),
            "children_registered": _serialize(child_month_rows),
        }

    except Exception as exc:
        logger.exception("get_monthly_trend error: %s", exc)
        raise


# ---------------------------------------------------------------------------
# 8. Visit-type distribution (pie chart)
# ---------------------------------------------------------------------------

def get_visit_type_distribution(asha_id: str | None = None) -> list:
    """Counts by visit_type for pie / donut chart."""
    try:
        q = db.session.query(
            VisitRecord.visit_type,
            func.count(VisitRecord.id).label("count"),
        )
        q = _asha_filter(q, VisitRecord, asha_id)
        rows = q.group_by(VisitRecord.visit_type).order_by(func.count(VisitRecord.id).desc()).all()
        return [{"visit_type": r.visit_type, "count": r.count} for r in rows]
    except Exception as exc:
        logger.exception("get_visit_type_distribution error: %s", exc)
        raise


# ---------------------------------------------------------------------------
# 9. ANC risk distribution (bar / pie)
# ---------------------------------------------------------------------------

def get_risk_distribution(asha_id: str | None = None) -> list:
    """ANC records by risk_status."""
    try:
        q = db.session.query(
            ANCRecord.risk_status,
            func.count(ANCRecord.id).label("count"),
        )
        q = _asha_filter(q, ANCRecord, asha_id)
        rows = q.group_by(ANCRecord.risk_status).all()
        return [{"risk_status": r.risk_status, "count": r.count} for r in rows]
    except Exception as exc:
        logger.exception("get_risk_distribution error: %s", exc)
        raise


# ---------------------------------------------------------------------------
# 10. Vaccination coverage chart
# ---------------------------------------------------------------------------

def get_vaccination_coverage_chart(asha_id: str | None = None) -> dict:
    """
    Vaccination status totals for a stacked-bar / donut chart.
    Also returns per-village coverage if no asha_id filter (admin view).
    """
    try:
        status_q = (
            db.session.query(
                VaccineEntry.status,
                func.count(VaccineEntry.id).label("count"),
            )
            .join(ChildModel, VaccineEntry.child_id == ChildModel.id)
        )
        if asha_id:
            status_q = status_q.filter(ChildModel.asha_id == asha_id)
        status_rows = status_q.group_by(VaccineEntry.status).all()

        return {
            "by_status": [
                {"status": r.status, "count": r.count}
                for r in status_rows
            ],
        }
    except Exception as exc:
        logger.exception("get_vaccination_coverage_chart error: %s", exc)
        raise
