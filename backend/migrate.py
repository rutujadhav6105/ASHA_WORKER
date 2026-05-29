"""
migrate_v2.py
==============
Fixed one-time migration. Handles the full real schema found in your DB.

Existing users columns:
  asha_id, block, created_at, created_by, csv_backup_path, district,
  email, full_name, id, is_active, last_login, mobile, password_hash,
  profile_data, role, supervisor_id, sync_status, updated_at, username,
  village, zone

New UserModel expects:
  id, name, mobile, email, role, worker_id, supervisor_id, area,
  district, password_hash, is_active, created_at, updated_at

Steps:
  1. Rename full_name → name
  2. Rename username  → worker_id  (or drop if worker_id exists)
  3. Rename village   → area       (closest match; or add area fresh)
  4. Add worker_id column if still missing
  5. Drop extra columns not in UserModel (safe – no data loss for new model)
  6. Seed default admin if none exists
"""

import os
import uuid
from datetime import datetime, timezone

import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "asha_db"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

# Columns the new UserModel needs
REQUIRED_COLS = {
    "id", "name", "mobile", "email", "role",
    "worker_id", "supervisor_id", "area", "district",
    "password_hash", "is_active", "created_at", "updated_at",
}

# Extra columns in old schema we can safely drop
LEGACY_COLS_TO_DROP = {
    "full_name", "username", "asha_id", "block", "zone", "village",
    "last_login", "sync_status", "csv_backup_path", "profile_data",
    "created_by",
}


def get_columns(cur, table):
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s ORDER BY ordinal_position;
    """, (table,))
    return {row[0] for row in cur.fetchall()}


def get_check_constraints(cur):
    """Return only non-PK CHECK constraints on users table."""
    cur.execute("""
        SELECT tc.constraint_name
        FROM information_schema.table_constraints tc
        WHERE tc.table_name = 'users'
          AND tc.constraint_type = 'CHECK'
          AND tc.constraint_name NOT LIKE '%_not_null'
          AND tc.constraint_name NOT IN (
              SELECT constraint_name FROM information_schema.table_constraints
              WHERE table_name = 'users' AND constraint_type = 'PRIMARY KEY'
          );
    """)
    return [row[0] for row in cur.fetchall()]


def run():
    print("🔌  Connecting to PostgreSQL …")
    conn = psycopg.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        cols = get_columns(cur, "users")
        print(f"\n📋  Current columns: {sorted(cols)}\n")

        # ── Step 1: Drop only real CHECK constraints (not PK) ────────────
        print("🔧  Step 1 – Dropping non-PK CHECK constraints …")
        for cname in get_check_constraints(cur):
            cur.execute(f'ALTER TABLE users DROP CONSTRAINT IF EXISTS "{cname}";')
            print(f"    Dropped: {cname}")

        # ── Step 2: Rename full_name → name ──────────────────────────────
        print("\n🔧  Step 2 – full_name → name …")
        cols = get_columns(cur, "users")
        if "full_name" in cols and "name" not in cols:
            cur.execute("ALTER TABLE users RENAME COLUMN full_name TO name;")
            print("    Renamed full_name → name")
        elif "full_name" in cols and "name" in cols:
            cur.execute("UPDATE users SET name = full_name WHERE name IS NULL OR name = '';")
            cur.execute("ALTER TABLE users DROP COLUMN full_name;")
            print("    Merged full_name into name, dropped full_name")
        else:
            print("    name already exists — skipping")

        # ── Step 3: Rename username → worker_id ──────────────────────────
        print("\n🔧  Step 3 – username → worker_id …")
        cols = get_columns(cur, "users")
        if "username" in cols and "worker_id" not in cols:
            cur.execute("ALTER TABLE users RENAME COLUMN username TO worker_id;")
            print("    Renamed username → worker_id")
        elif "username" in cols and "worker_id" in cols:
            cur.execute("ALTER TABLE users DROP COLUMN username;")
            print("    Dropped username (worker_id already exists)")
        else:
            print("    No username column — skipping")

        # ── Step 4: Handle `area` column (map from village if present) ────
        print("\n🔧  Step 4 – area column …")
        cols = get_columns(cur, "users")
        if "area" not in cols:
            if "village" in cols:
                cur.execute("ALTER TABLE users RENAME COLUMN village TO area;")
                print("    Renamed village → area")
            else:
                cur.execute("ALTER TABLE users ADD COLUMN area VARCHAR(100);")
                print("    Added area column")
        else:
            print("    area already exists — skipping")

        # ── Step 5: Add worker_id if still missing ────────────────────────
        print("\n🔧  Step 5 – Ensuring worker_id exists …")
        cols = get_columns(cur, "users")
        if "worker_id" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN worker_id VARCHAR(50) UNIQUE;")
            print("    Added worker_id column")
        else:
            # Make sure it has UNIQUE constraint
            print("    worker_id exists — skipping")

        # ── Step 6: Add is_active / updated_at if missing ────────────────
        print("\n🔧  Step 6 – Ensuring is_active and updated_at …")
        cols = get_columns(cur, "users")
        if "is_active" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;")
            print("    Added is_active")
        else:
            print("    is_active exists — skipping")
        if "updated_at" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();")
            print("    Added updated_at")
        else:
            print("    updated_at exists — skipping")

        # ── Step 7: Drop legacy columns not needed by UserModel ───────────
        print("\n🔧  Step 7 – Dropping legacy columns …")
        cols = get_columns(cur, "users")
        to_drop = cols & LEGACY_COLS_TO_DROP  # only drop what actually exists
        if to_drop:
            for col in sorted(to_drop):
                cur.execute(f"ALTER TABLE users DROP COLUMN IF EXISTS {col};")
                print(f"    Dropped: {col}")
        else:
            print("    Nothing to drop")

        # ── Step 8: Ensure name NOT NULL ──────────────────────────────────
        print("\n🔧  Step 8 – Ensuring name NOT NULL …")
        cur.execute("UPDATE users SET name = 'Unknown' WHERE name IS NULL OR name = '';")
        cur.execute("ALTER TABLE users ALTER COLUMN name SET NOT NULL;")
        print("    Done")

        # ── Step 9: Seed admin ────────────────────────────────────────────
        print("\n🔧  Step 9 – Seeding default admin …")
        cur.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1;")
        if not cur.fetchone():
            import bcrypt as _bcrypt
            hashed = _bcrypt.hashpw(b"admin123", _bcrypt.gensalt()).decode()
            admin_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            cur.execute("""
                INSERT INTO users
                  (id, name, mobile, email, role, worker_id,
                   password_hash, is_active, created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (admin_id, "System Admin", "0000000000",
                  "admin@nhm.gov.in", "admin", "ADMIN001",
                  hashed, True, now, now))
            print("    ✅ Admin seeded  mobile=0000000000  password=admin123")
        else:
            print("    Admin already exists — skipping")

        conn.commit()

        # ── Final column report ───────────────────────────────────────────
        cols = get_columns(cur, "users")
        print(f"\n📋  Final columns: {sorted(cols)}")
        missing = REQUIRED_COLS - cols
        if missing:
            print(f"⚠️   Still missing: {missing}")
        else:
            print("✅  All required columns present!")

        print("\n✅  Migration complete — run: python app.py")

    except Exception as e:
        conn.rollback()
        print(f"\n❌  Migration failed — rolled back.\n    Error: {e}")
        import traceback; traceback.print_exc()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run()