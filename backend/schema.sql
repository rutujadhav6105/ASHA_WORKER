-- ============================================================
-- ASHA Seva Backend — PostgreSQL Schema
-- Version: 2.0
-- Compatible with: Flask-SQLAlchemy 3.1 / SQLAlchemy 2.0
--
-- Run order:
--   1. CREATE DATABASE asha_db;
--   2. \c asha_db
--   3. \i schema.sql
--
-- Tables:
--   users, families, family_members,
--   anc_records, children, vaccine_entries
-- ============================================================

-- ── Extensions ─────────────────────────────────────────────
-- pgcrypto gives us gen_random_uuid() for UUID defaults
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ── Enum types ──────────────────────────────────────────────
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('admin', 'supervisor', 'asha');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE gender_type AS ENUM ('Male', 'Female', 'Other');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE apl_bpl_type AS ENUM ('APL', 'BPL');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE risk_status_type AS ENUM ('Normal', 'Low Risk', 'High Risk');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE vaccine_status_type AS ENUM ('scheduled', 'due', 'given', 'overdue');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- TABLE: users
-- Stores admin, supervisor, and ASHA worker accounts.
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    -- Primary key: UUID v4 as VARCHAR for SQLAlchemy String(36) compatibility
    id            VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::text,

    -- Identity
    name          VARCHAR(100) NOT NULL,
    mobile        VARCHAR(15)  UNIQUE,
    email         VARCHAR(100) UNIQUE,

    -- Role & hierarchy
    role          VARCHAR(20)  NOT NULL
                               CHECK (role IN ('admin', 'supervisor', 'asha')),
    worker_id     VARCHAR(50)  UNIQUE,         -- ASHA / supervisor staff ID
    supervisor_id VARCHAR(50),                 -- references another user's worker_id

    -- Location
    area          VARCHAR(100),
    district      VARCHAR(100),

    -- Auth
    password_hash VARCHAR(255) NOT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,

    -- Timestamps
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  users IS 'System users: admin, supervisor, ASHA worker accounts';
COMMENT ON COLUMN users.worker_id IS 'Staff ID assigned to ASHA/supervisor; referenced by asha_id in other tables';
COMMENT ON COLUMN users.supervisor_id IS 'worker_id of the supervising user (soft FK)';

-- Indexes on users
CREATE INDEX IF NOT EXISTS idx_users_role      ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_mobile    ON users (mobile);
CREATE INDEX IF NOT EXISTS idx_users_district  ON users (district);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active);


-- ============================================================
-- TABLE: families
-- One household registered by an ASHA worker.
-- ============================================================
CREATE TABLE IF NOT EXISTS families (
    id          VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    home_no     VARCHAR(20),
    address     TEXT,
    village     VARCHAR(100),
    taluka      VARCHAR(100),
    district    VARCHAR(100),
    family_head VARCHAR(100) NOT NULL,

    -- Soft FK to users.worker_id
    asha_id     VARCHAR(50),

    -- Timestamps
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  families IS 'Households registered by ASHA workers';
COMMENT ON COLUMN families.asha_id IS 'References users.worker_id (soft FK — no constraint to allow flexible registration)';

-- Indexes on families
CREATE INDEX IF NOT EXISTS idx_families_asha_id  ON families (asha_id);
CREATE INDEX IF NOT EXISTS idx_families_village  ON families (village);
CREATE INDEX IF NOT EXISTS idx_families_district ON families (district);
-- Composite: useful for de-duplication checks
CREATE UNIQUE INDEX IF NOT EXISTS uq_families_head_home_village
    ON families (family_head, home_no, village)
    WHERE home_no IS NOT NULL;


-- ============================================================
-- TABLE: family_members
-- Individuals belonging to a household.
-- ============================================================
CREATE TABLE IF NOT EXISTS family_members (
    id                   VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::text,

    -- Hard FK: a member must belong to a family
    family_id            VARCHAR(36)  NOT NULL
                                      REFERENCES families (id) ON DELETE CASCADE,

    -- Identity
    name                 VARCHAR(100) NOT NULL,
    dob                  DATE,
    age                  INTEGER      CHECK (age IS NULL OR (age >= 0 AND age <= 150)),
    aadhaar              CHAR(12)     UNIQUE,       -- 12-digit Aadhaar number
    gender               VARCHAR(10)  CHECK (gender IN ('Male', 'Female', 'Other')),

    -- Social / economic
    is_reproductive_pair BOOLEAN      NOT NULL DEFAULT FALSE,
    caste                VARCHAR(100),
    sub_caste            VARCHAR(100),
    apl_bpl              VARCHAR(5)   NOT NULL DEFAULT 'APL'
                                      CHECK (apl_bpl IN ('APL', 'BPL')),
    education            VARCHAR(100),

    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  family_members IS 'Individual members within a registered household';
COMMENT ON COLUMN family_members.aadhaar IS '12-digit Aadhaar — UNIQUE (NULLs excluded from uniqueness check in PostgreSQL)';

-- Indexes on family_members
CREATE INDEX IF NOT EXISTS idx_family_members_family_id ON family_members (family_id);
CREATE INDEX IF NOT EXISTS idx_family_members_gender    ON family_members (gender);
CREATE INDEX IF NOT EXISTS idx_family_members_rep_pair  ON family_members (is_reproductive_pair);


-- ============================================================
-- TABLE: anc_records
-- Antenatal Care (ANC) records for pregnant beneficiaries.
-- ============================================================
CREATE TABLE IF NOT EXISTS anc_records (
    id               VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::text,

    -- Beneficiary details
    beneficiary_name VARCHAR(100) NOT NULL,
    husband_name     VARCHAR(100),
    lmp              DATE,                       -- Last Menstrual Period
    edd              DATE,                       -- Expected Delivery Date
    gravida          INTEGER      CHECK (gravida IS NULL OR gravida >= 0),
    risk_status      VARCHAR(20)  NOT NULL DEFAULT 'Normal'
                                  CHECK (risk_status IN ('Normal', 'Low Risk', 'High Risk')),
    mobile           VARCHAR(15),
    village          VARCHAR(100),

    -- Soft FK to users.worker_id
    asha_id          VARCHAR(50),

    -- Timestamps
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  anc_records IS 'Antenatal care records for pregnant women registered by ASHA workers';
COMMENT ON COLUMN anc_records.lmp IS 'Last Menstrual Period — used to calculate EDD and trimester';

-- Indexes on anc_records
CREATE INDEX IF NOT EXISTS idx_anc_asha_id     ON anc_records (asha_id);
CREATE INDEX IF NOT EXISTS idx_anc_risk_status ON anc_records (risk_status);
CREATE INDEX IF NOT EXISTS idx_anc_edd         ON anc_records (edd);
CREATE INDEX IF NOT EXISTS idx_anc_village     ON anc_records (village);
-- Partial index: only High Risk records (common dashboard filter)
CREATE INDEX IF NOT EXISTS idx_anc_high_risk   ON anc_records (asha_id, edd)
    WHERE risk_status = 'High Risk';


-- ============================================================
-- TABLE: children
-- Children registered for immunisation tracking.
-- ============================================================
CREATE TABLE IF NOT EXISTS children (
    id          VARCHAR(36)   PRIMARY KEY DEFAULT gen_random_uuid()::text,

    -- Identity
    child_name  VARCHAR(100)  NOT NULL,
    mother_name VARCHAR(100),
    dob         DATE,
    gender      VARCHAR(10)   CHECK (gender IN ('Male', 'Female')),
    weight      NUMERIC(5, 2) CHECK (weight IS NULL OR weight > 0),  -- kg

    -- Soft FK to users.worker_id
    asha_id     VARCHAR(50),

    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  children IS 'Children registered under ASHA workers for vaccination tracking';
COMMENT ON COLUMN children.weight IS 'Birth/current weight in kg';

-- Indexes on children
CREATE INDEX IF NOT EXISTS idx_children_asha_id ON children (asha_id);
CREATE INDEX IF NOT EXISTS idx_children_dob     ON children (dob);
CREATE INDEX IF NOT EXISTS idx_children_gender  ON children (gender);


-- ============================================================
-- TABLE: vaccine_entries
-- One vaccine dose linked to a child.
-- ============================================================
CREATE TABLE IF NOT EXISTS vaccine_entries (
    id         VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,

    -- Hard FK: dose must belong to a child
    child_id   VARCHAR(36) NOT NULL
                           REFERENCES children (id) ON DELETE CASCADE,

    -- Vaccine info
    name       VARCHAR(100) NOT NULL,           -- BCG, OPV-0, HepB, etc.
    due_date   DATE,
    given_date DATE,
    next_due   DATE,
    status     VARCHAR(20)  NOT NULL DEFAULT 'scheduled'
                            CHECK (status IN ('scheduled', 'due', 'given', 'overdue')),

    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- Business rule: same vaccine shouldn't be scheduled twice for same child
    CONSTRAINT uq_child_vaccine_due UNIQUE (child_id, name, due_date)
);

COMMENT ON TABLE  vaccine_entries IS 'Vaccination records (doses) for each registered child';
COMMENT ON COLUMN vaccine_entries.status IS 'scheduled | due | given | overdue';

-- Indexes on vaccine_entries
CREATE INDEX IF NOT EXISTS idx_vaccine_child_id  ON vaccine_entries (child_id);
CREATE INDEX IF NOT EXISTS idx_vaccine_status    ON vaccine_entries (status);
CREATE INDEX IF NOT EXISTS idx_vaccine_due_date  ON vaccine_entries (due_date);
-- Partial index: upcoming doses (common query for reminders)
CREATE INDEX IF NOT EXISTS idx_vaccine_upcoming  ON vaccine_entries (due_date)
    WHERE status IN ('scheduled', 'due');


-- ============================================================
-- TABLE: scheme_enrollments
-- Government scheme beneficiary enrollments by ASHA workers.
-- ============================================================
CREATE TABLE IF NOT EXISTS scheme_enrollments (
    id                VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::text,
    scheme_name       VARCHAR(200) NOT NULL,
    beneficiary_name  VARCHAR(100) NOT NULL,
    mobile_number     VARCHAR(15)  NOT NULL,
    aadhaar_number    VARCHAR(20),
    village           VARCHAR(100) NOT NULL,
    district          VARCHAR(100) NOT NULL,
    asha_id           VARCHAR(50),
    asha_worker_name  VARCHAR(100) NOT NULL,
    enrollment_date   DATE         NOT NULL,
    status            VARCHAR(30)  NOT NULL DEFAULT 'Enrolled',
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scheme_enroll_asha_id ON scheme_enrollments (asha_id);
CREATE INDEX IF NOT EXISTS idx_scheme_enroll_scheme ON scheme_enrollments (scheme_name);
CREATE INDEX IF NOT EXISTS idx_scheme_enroll_district ON scheme_enrollments (district);
CREATE INDEX IF NOT EXISTS idx_scheme_enroll_created ON scheme_enrollments (created_at);


-- ============================================================
-- TRIGGER: auto-update updated_at on row change
-- Applied to: users, families, anc_records
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at      ON users;
DROP TRIGGER IF EXISTS trg_families_updated_at   ON families;
DROP TRIGGER IF EXISTS trg_anc_records_updated_at ON anc_records;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_families_updated_at
    BEFORE UPDATE ON families
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_anc_records_updated_at
    BEFORE UPDATE ON anc_records
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ============================================================
-- DEFAULT ADMIN SEED
-- Safe to run multiple times (INSERT ... ON CONFLICT DO NOTHING)
-- Password: admin123 (bcrypt hash — change in production!)
-- ============================================================
INSERT INTO users (
    id, name, mobile, email, role, worker_id,
    password_hash, is_active, created_at, updated_at
)
VALUES (
    gen_random_uuid()::text,
    'System Admin',
    '0000000000',
    'admin@nhm.gov.in',
    'admin',
    'ADMIN001',
    -- bcrypt hash of 'admin123' — generated externally for SQL portability
    -- In production: replace with a real bcrypt hash generated by the app
    '$2b$12$placeholder_replace_with_real_bcrypt_hash_at_setup',
    TRUE,
    NOW(),
    NOW()
)
ON CONFLICT (mobile) DO NOTHING;

-- NOTE: The Flask app seeds a proper bcrypt hash automatically on first startup.
-- This SQL seed is a fallback for manual DB setup only.
-- The Flask auto-seed in auth_service.seed_admin() will override if admin exists.
