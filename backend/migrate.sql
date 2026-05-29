-- ============================================================
-- ASHA Seva Backend — Idempotent Migration Script
-- Version: 2.0
-- Purpose: Apply indexes and constraints to an EXISTING database
--          that was created by SQLAlchemy db.create_all() (which
--          does NOT create indexes beyond primary keys).
--
-- Safe to re-run: all statements use IF NOT EXISTS / ON CONFLICT
-- ============================================================

-- ── Users: add missing indexes ──────────────────────────────
CREATE INDEX IF NOT EXISTS idx_users_role      ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_mobile    ON users (mobile);
CREATE INDEX IF NOT EXISTS idx_users_district  ON users (district);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active);

-- ── Users: add DB-level role constraint ─────────────────────
-- (SQLAlchemy doesn't emit CHECK constraints by default)
DO $$
BEGIN
    ALTER TABLE users
        ADD CONSTRAINT chk_users_role
        CHECK (role IN ('admin', 'supervisor', 'asha'));
EXCEPTION WHEN duplicate_object THEN
    NULL; -- constraint already exists, skip
END;
$$;

-- ── Families: add missing indexes ───────────────────────────
CREATE INDEX IF NOT EXISTS idx_families_asha_id  ON families (asha_id);
CREATE INDEX IF NOT EXISTS idx_families_village  ON families (village);
CREATE INDEX IF NOT EXISTS idx_families_district ON families (district);

-- ── Families: composite unique for de-duplication ───────────
CREATE UNIQUE INDEX IF NOT EXISTS uq_families_head_home_village
    ON families (family_head, home_no, village)
    WHERE home_no IS NOT NULL;

-- ── Family Members: add missing indexes ─────────────────────
CREATE INDEX IF NOT EXISTS idx_family_members_family_id ON family_members (family_id);
CREATE INDEX IF NOT EXISTS idx_family_members_gender    ON family_members (gender);
CREATE INDEX IF NOT EXISTS idx_family_members_rep_pair  ON family_members (is_reproductive_pair);

-- ── Family Members: add age CHECK constraint ────────────────
DO $$
BEGIN
    ALTER TABLE family_members
        ADD CONSTRAINT chk_member_age
        CHECK (age IS NULL OR (age >= 0 AND age <= 150));
EXCEPTION WHEN duplicate_object THEN
    NULL;
END;
$$;

-- ── Family Members: add apl_bpl CHECK constraint ────────────
DO $$
BEGIN
    ALTER TABLE family_members
        ADD CONSTRAINT chk_member_apl_bpl
        CHECK (apl_bpl IN ('APL', 'BPL'));
EXCEPTION WHEN duplicate_object THEN
    NULL;
END;
$$;

-- ── ANC Records: add missing indexes ────────────────────────
CREATE INDEX IF NOT EXISTS idx_anc_asha_id     ON anc_records (asha_id);
CREATE INDEX IF NOT EXISTS idx_anc_risk_status ON anc_records (risk_status);
CREATE INDEX IF NOT EXISTS idx_anc_edd         ON anc_records (edd);
CREATE INDEX IF NOT EXISTS idx_anc_village     ON anc_records (village);

-- Partial index for High Risk filtering
CREATE INDEX IF NOT EXISTS idx_anc_high_risk
    ON anc_records (asha_id, edd)
    WHERE risk_status = 'High Risk';

-- ── ANC Records: add risk_status CHECK constraint ───────────
DO $$
BEGIN
    ALTER TABLE anc_records
        ADD CONSTRAINT chk_anc_risk_status
        CHECK (risk_status IN ('Normal', 'Low Risk', 'High Risk'));
EXCEPTION WHEN duplicate_object THEN
    NULL;
END;
$$;

-- ── Children: add missing indexes ───────────────────────────
CREATE INDEX IF NOT EXISTS idx_children_asha_id ON children (asha_id);
CREATE INDEX IF NOT EXISTS idx_children_dob     ON children (dob);
CREATE INDEX IF NOT EXISTS idx_children_gender  ON children (gender);

-- ── Vaccine Entries: add missing indexes ────────────────────
CREATE INDEX IF NOT EXISTS idx_vaccine_child_id ON vaccine_entries (child_id);
CREATE INDEX IF NOT EXISTS idx_vaccine_status   ON vaccine_entries (status);
CREATE INDEX IF NOT EXISTS idx_vaccine_due_date ON vaccine_entries (due_date);

-- Partial index: upcoming doses
CREATE INDEX IF NOT EXISTS idx_vaccine_upcoming
    ON vaccine_entries (due_date)
    WHERE status IN ('scheduled', 'due');

-- ── Vaccine Entries: add unique constraint ───────────────────
DO $$
BEGIN
    ALTER TABLE vaccine_entries
        ADD CONSTRAINT uq_child_vaccine_due UNIQUE (child_id, name, due_date);
EXCEPTION WHEN duplicate_object THEN
    NULL;
END;
$$;

-- ── Vaccine Entries: add status CHECK constraint ────────────
DO $$
BEGIN
    ALTER TABLE vaccine_entries
        ADD CONSTRAINT chk_vaccine_status
        CHECK (status IN ('scheduled', 'due', 'given', 'overdue'));
EXCEPTION WHEN duplicate_object THEN
    NULL;
END;
$$;

-- ── Updated_at trigger function ──────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop and recreate triggers (safe — OR REPLACE for function, drop+create for triggers)
DROP TRIGGER IF EXISTS trg_users_updated_at       ON users;
DROP TRIGGER IF EXISTS trg_families_updated_at    ON families;
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

-- ── Report: show what was applied ───────────────────────────
SELECT
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('users','families','family_members','anc_records','children','vaccine_entries')
ORDER BY tablename, indexname;

-- ============================================================
-- Phase 6 additions: visit_records + family_planning_records
-- ============================================================

-- ── visit_records ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS visit_records (
    id               VARCHAR(36)   PRIMARY KEY DEFAULT gen_random_uuid()::text,
    asha_id          VARCHAR(50)   NOT NULL,
    beneficiary_id   VARCHAR(36),
    beneficiary_name VARCHAR(100)  NOT NULL,
    village          VARCHAR(100),
    visit_type       VARCHAR(30)   NOT NULL DEFAULT 'general'
                                   CHECK (visit_type IN ('maternal','child','general','family_planning','immunization')),
    visit_date       DATE          NOT NULL,
    status           VARCHAR(20)   NOT NULL DEFAULT 'completed'
                                   CHECK (status IN ('scheduled','completed','missed','cancelled')),
    notes            TEXT,
    weight_kg        NUMERIC(5,2),
    bp_systolic      INTEGER,
    bp_diastolic     INTEGER,
    temperature_c    NUMERIC(4,1),
    medicines_given  TEXT,
    referred         BOOLEAN       NOT NULL DEFAULT FALSE,
    referral_notes   TEXT,
    next_visit_date  DATE,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_visit_asha_id     ON visit_records (asha_id);
CREATE INDEX IF NOT EXISTS idx_visit_type        ON visit_records (visit_type);
CREATE INDEX IF NOT EXISTS idx_visit_status      ON visit_records (status);
CREATE INDEX IF NOT EXISTS idx_visit_date        ON visit_records (visit_date);
CREATE INDEX IF NOT EXISTS idx_visit_beneficiary ON visit_records (beneficiary_id);

DROP TRIGGER IF EXISTS trg_visit_records_updated_at ON visit_records;
CREATE TRIGGER trg_visit_records_updated_at
    BEFORE UPDATE ON visit_records
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ── family_planning_records ──────────────────────────────────
CREATE TABLE IF NOT EXISTS family_planning_records (
    id                 VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::text,
    asha_id            VARCHAR(50)  NOT NULL,
    beneficiary_name   VARCHAR(100) NOT NULL,
    husband_name       VARCHAR(100),
    mobile             VARCHAR(15),
    village            VARCHAR(100),
    age                INTEGER      CHECK (age IS NULL OR (age >= 10 AND age <= 60)),
    method             VARCHAR(30)  NOT NULL DEFAULT 'None'
                                    CHECK (method IN ('OCP','IUCD','Condom','Injectable','Sterilization','LAM','NFP','None','Other')),
    method_start_date  DATE,
    method_end_date    DATE,
    status             VARCHAR(20)  NOT NULL DEFAULT 'active'
                                    CHECK (status IN ('active','discontinued','completed','follow_up')),
    counselling_date   DATE,
    counselling_notes  TEXT,
    side_effects       TEXT,
    complications      TEXT,
    next_followup_date DATE,
    followup_notes     TEXT,
    living_children    INTEGER,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fp_asha_id      ON family_planning_records (asha_id);
CREATE INDEX IF NOT EXISTS idx_fp_method       ON family_planning_records (method);
CREATE INDEX IF NOT EXISTS idx_fp_status       ON family_planning_records (status);
CREATE INDEX IF NOT EXISTS idx_fp_next_follow  ON family_planning_records (next_followup_date);

DROP TRIGGER IF EXISTS trg_fp_records_updated_at ON family_planning_records;
CREATE TRIGGER trg_fp_records_updated_at
    BEFORE UPDATE ON family_planning_records
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
