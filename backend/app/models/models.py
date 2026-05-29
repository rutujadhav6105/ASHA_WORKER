"""
SQLAlchemy models for ASHA Seva.
Every table includes: id, created_at, updated_at, created_by, sync_status, csv_backup_path
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Enum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


# ── Enums ──────────────────────────────────────────────────────────────────────
class RoleEnum(str, enum.Enum):
    admin      = "admin"
    supervisor = "supervisor"
    asha_worker = "asha_worker"


class RiskLevelEnum(str, enum.Enum):
    low    = "low"
    medium = "medium"
    high   = "high"


class SyncStatusEnum(str, enum.Enum):
    synced  = "synced"
    pending = "pending"
    failed  = "failed"


# ── Mixin ──────────────────────────────────────────────────────────────────────
class TimestampMixin:
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by      = Column(Integer, nullable=True)
    sync_status     = Column(String(20), default="synced")
    csv_backup_path = Column(String(255), nullable=True)


# ── Users ──────────────────────────────────────────────────────────────────────
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id           = Column(Integer, primary_key=True, index=True)
    username     = Column(String(100), unique=True, nullable=False, index=True)
    email        = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name    = Column(String(200), nullable=False)
    role         = Column(Enum(RoleEnum), default=RoleEnum.asha_worker)
    mobile       = Column(String(15), nullable=True)
    village      = Column(String(100), nullable=True)
    district     = Column(String(100), nullable=True)
    block        = Column(String(100), nullable=True)
    zone         = Column(String(100), nullable=True)
    asha_id      = Column(String(50), nullable=True)
    supervisor_id = Column(String(50), nullable=True)
    is_active    = Column(Boolean, default=True)
    last_login   = Column(DateTime(timezone=True), nullable=True)
    profile_data = Column(JSON, nullable=True)


# ── Patients ───────────────────────────────────────────────────────────────────
class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id              = Column(Integer, primary_key=True, index=True)
    full_name       = Column(String(200), nullable=False)
    age             = Column(Integer, nullable=False)
    gender          = Column(String(10), nullable=False)
    mobile          = Column(String(15), nullable=True)
    address         = Column(Text, nullable=True)
    village         = Column(String(100), nullable=True, index=True)
    district        = Column(String(100), nullable=True)
    asha_worker_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    aadhar_number   = Column(String(20), nullable=True)
    abha_id         = Column(String(50), nullable=True)
    family_id       = Column(Integer, nullable=True)
    risk_level      = Column(Enum(RiskLevelEnum), default=RiskLevelEnum.low)
    blood_group     = Column(String(5), nullable=True)
    notes           = Column(Text, nullable=True)

    pregnancies     = relationship("Pregnancy", back_populates="patient")
    immunizations   = relationship("Immunization", back_populates="patient")
    home_visits     = relationship("HomeVisit",    back_populates="patient")


# ── Pregnancies ────────────────────────────────────────────────────────────────
class Pregnancy(Base, TimestampMixin):
    __tablename__ = "pregnancies"

    id                    = Column(Integer, primary_key=True, index=True)
    patient_id            = Column(Integer, ForeignKey("patients.id"), nullable=False)
    lmp_date              = Column(DateTime, nullable=True)
    edd                   = Column(DateTime, nullable=True)
    gestational_week      = Column(Integer, nullable=True)
    hemoglobin            = Column(Float, nullable=True)
    systolic_bp           = Column(Float, nullable=True)
    diastolic_bp          = Column(Float, nullable=True)
    weight_kg             = Column(Float, nullable=True)
    previous_complications = Column(Boolean, default=False)
    gravida               = Column(Integer, default=1)
    para                  = Column(Integer, default=0)
    risk_level            = Column(Enum(RiskLevelEnum), default=RiskLevelEnum.low)
    risk_score            = Column(Float, nullable=True)
    delivery_outcome      = Column(String(100), nullable=True)
    delivery_date         = Column(DateTime, nullable=True)
    delivery_place        = Column(String(100), nullable=True)
    status                = Column(String(50), default="active")  # active, delivered, closed
    notes                 = Column(Text, nullable=True)

    patient    = relationship("Patient",    back_populates="pregnancies")
    anc_visits = relationship("ANCVisit",   back_populates="pregnancy")


# ── ANC Visits ─────────────────────────────────────────────────────────────────
class ANCVisit(Base, TimestampMixin):
    __tablename__ = "anc_visits"

    id              = Column(Integer, primary_key=True, index=True)
    pregnancy_id    = Column(Integer, ForeignKey("pregnancies.id"), nullable=False)
    visit_number    = Column(Integer, nullable=False)  # 1, 2, 3, 4
    visit_date      = Column(DateTime, nullable=False)
    hemoglobin      = Column(Float, nullable=True)
    weight_kg       = Column(Float, nullable=True)
    systolic_bp     = Column(Float, nullable=True)
    diastolic_bp    = Column(Float, nullable=True)
    urine_albumin   = Column(String(20), nullable=True)
    fundal_height   = Column(Float, nullable=True)
    fetal_heartrate = Column(Integer, nullable=True)
    tt_vaccination  = Column(Boolean, default=False)
    ifa_tablets     = Column(Integer, default=0)
    calcium_tablets = Column(Integer, default=0)
    risk_flags      = Column(JSON, nullable=True)
    next_visit_date = Column(DateTime, nullable=True)
    notes           = Column(Text, nullable=True)

    pregnancy = relationship("Pregnancy", back_populates="anc_visits")


# ── Immunization ───────────────────────────────────────────────────────────────
class Immunization(Base, TimestampMixin):
    __tablename__ = "immunizations"

    id              = Column(Integer, primary_key=True, index=True)
    patient_id      = Column(Integer, ForeignKey("patients.id"), nullable=False)
    child_name      = Column(String(200), nullable=False)
    date_of_birth   = Column(DateTime, nullable=False)
    gender          = Column(String(10), nullable=False)
    mother_name     = Column(String(200), nullable=True)
    father_name     = Column(String(200), nullable=True)
    weight_kg       = Column(Float, nullable=True)
    height_cm       = Column(Float, nullable=True)
    muac_cm         = Column(Float, nullable=True)
    nutrition_status = Column(String(50), nullable=True)
    village         = Column(String(100), nullable=True)
    vaccine_records = Column(JSON, nullable=True)  # [{vaccine, date, batch, given_by}]
    due_vaccines    = Column(JSON, nullable=True)   # [vaccine_name]
    next_due_date   = Column(DateTime, nullable=True)
    notes           = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="immunizations")


# ── Home Visits ────────────────────────────────────────────────────────────────
class HomeVisit(Base, TimestampMixin):
    __tablename__ = "home_visits"

    id              = Column(Integer, primary_key=True, index=True)
    patient_id      = Column(Integer, ForeignKey("patients.id"), nullable=False)
    asha_worker_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    visit_date      = Column(DateTime, nullable=False)
    visit_type      = Column(String(50), nullable=True)  # antenatal, postnatal, child, general
    status          = Column(String(20), default="completed")  # completed, missed, rescheduled
    findings        = Column(Text, nullable=True)
    actions_taken   = Column(Text, nullable=True)
    referral_made   = Column(Boolean, default=False)
    referral_to     = Column(String(200), nullable=True)
    next_visit_date = Column(DateTime, nullable=True)
    missed_reason   = Column(String(200), nullable=True)
    gps_lat         = Column(Float, nullable=True)
    gps_lng         = Column(Float, nullable=True)
    notes           = Column(Text, nullable=True)

    patient     = relationship("Patient", back_populates="home_visits")
    asha_worker = relationship("User",    foreign_keys=[asha_worker_id])


# ── Medicine Stock ─────────────────────────────────────────────────────────────
class MedicineStock(Base, TimestampMixin):
    __tablename__ = "medicine_stock"

    id              = Column(Integer, primary_key=True, index=True)
    medicine_name   = Column(String(200), nullable=False)
    category        = Column(String(100), nullable=True)
    unit            = Column(String(50), nullable=True)
    current_stock   = Column(Integer, default=0)
    minimum_stock   = Column(Integer, default=10)
    expiry_date     = Column(DateTime, nullable=True)
    batch_number    = Column(String(100), nullable=True)
    supplier        = Column(String(200), nullable=True)
    asha_worker_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    village         = Column(String(100), nullable=True)
    is_low_stock    = Column(Boolean, default=False)
    last_restocked  = Column(DateTime, nullable=True)


# ── Alerts ─────────────────────────────────────────────────────────────────────
class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id              = Column(Integer, primary_key=True, index=True)
    title           = Column(String(200), nullable=False)
    message         = Column(Text, nullable=False)
    alert_type      = Column(String(50), nullable=True)  # high_risk, vaccine_due, medicine_low
    severity        = Column(String(20), default="info")  # info, warning, danger
    patient_id      = Column(Integer, ForeignKey("patients.id"), nullable=True)
    target_user_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_read         = Column(Boolean, default=False)
    action_taken    = Column(Boolean, default=False)
    expires_at      = Column(DateTime, nullable=True)


# ── Reports ────────────────────────────────────────────────────────────────────
class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id            = Column(Integer, primary_key=True, index=True)
    report_type   = Column(String(100), nullable=False)  # monthly, village, worker
    period_start  = Column(DateTime, nullable=True)
    period_end    = Column(DateTime, nullable=True)
    village       = Column(String(100), nullable=True)
    generated_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    data          = Column(JSON, nullable=True)
    file_path     = Column(String(255), nullable=True)


# ── Training Records ───────────────────────────────────────────────────────────
class TrainingRecord(Base, TimestampMixin):
    __tablename__ = "training_records"

    id               = Column(Integer, primary_key=True, index=True)
    asha_worker_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    training_name    = Column(String(200), nullable=False)
    training_date    = Column(DateTime, nullable=False)
    conducted_by     = Column(String(200), nullable=True)
    topics_covered   = Column(JSON, nullable=True)
    score            = Column(Float, nullable=True)
    certificate_path = Column(String(255), nullable=True)
    notes            = Column(Text, nullable=True)


# ── Villages ───────────────────────────────────────────────────────────────────
class Village(Base, TimestampMixin):
    __tablename__ = "villages"

    id                = Column(Integer, primary_key=True, index=True)
    name              = Column(String(200), nullable=False)
    district          = Column(String(100), nullable=True)
    block             = Column(String(100), nullable=True)
    population        = Column(Integer, nullable=True)
    asha_worker_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    supervisor_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    health_score      = Column(Float, nullable=True)
    latitude          = Column(Float, nullable=True)
    longitude         = Column(Float, nullable=True)


# ── Supervisor Notes ───────────────────────────────────────────────────────────
class SupervisorNote(Base, TimestampMixin):
    __tablename__ = "supervisor_notes"

    id              = Column(Integer, primary_key=True, index=True)
    supervisor_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    asha_worker_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    title           = Column(String(200), nullable=False)
    note            = Column(Text, nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
