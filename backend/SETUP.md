# ASHA Seva Backend — PostgreSQL Setup Guide
Version 2.0 | Phase 2 Migration

---

## Prerequisites

- Python 3.11 or 3.12
- PostgreSQL 14+ installed and running
- `psql` CLI available
- `pip` package manager

---

## Step 1 — Create the PostgreSQL Database

```bash
# Connect as the postgres superuser
psql -U postgres

# Inside psql:
CREATE DATABASE asha_db;
CREATE USER asha_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE asha_db TO asha_user;
\q
```

> **Note:** If you prefer to use the default `postgres` user, skip the
> CREATE USER and GRANT steps and set `DB_USER=postgres` in `.env`.

---

## Step 2 — Configure Environment Variables

```bash
# From the backend/ directory
cp .env.example .env
```

Edit `.env` with your actual values:

```ini
FLASK_ENV=development
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">

DB_NAME=asha_db
DB_USER=asha_user          # or postgres
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
JWT_ACCESS_TOKEN_EXPIRES=3600

CORS_ORIGINS=http://localhost,http://10.0.2.2
```

> ⚠️ Special characters in `DB_PASSWORD` (like `@`, `#`, `%`) are handled
> automatically — the app URL-encodes them before building the connection string.

---

## Step 3 — Install Python Dependencies

```bash
# From the backend/ directory
pip install -r requirements.txt
```

Key packages installed:
- `Flask==3.0.3` — web framework
- `Flask-SQLAlchemy==3.1.1` — ORM
- `psycopg[binary]==3.2.13` — PostgreSQL driver (psycopg v3)
- `Flask-JWT-Extended==4.6.0` — JWT auth
- `Flask-Bcrypt==1.0.1` — password hashing
- `flask-marshmallow==1.2.1` — serialization
- `pandas==2.2.3` — CSV export
- `python-dotenv==1.0.1` — .env loading

---

## Step 4 — Run the Application (Tables Auto-Created)

```bash
# Development
python app.py

# OR with gunicorn (production)
gunicorn --bind 0.0.0.0:5000 --workers 4 "app:create_app()"
```

On startup, the app:
1. Connects to PostgreSQL using the URL from `.env`
2. Runs `db.create_all()` — creates all 6 tables if they don't exist
3. Seeds a default admin user if none exists

**Startup log to look for:**
```
✅  Database tables verified / created.
✅  Default admin seeded (mobile=0000000000, password=admin123)
🚀  ASHA Seva backend ready (env=development)
```

---

## Step 5 — Apply Performance Indexes (Recommended)

The indexes defined in the updated model files are created by `db.create_all()`.
For an **existing database** that was created before v2.0, run:

```bash
psql -U postgres -d asha_db -f migrate.sql
```

This script is idempotent — safe to run multiple times.

---

## Step 6 — Verify the Setup

```bash
# Check the health endpoint
curl http://localhost:5000/api/health
# Expected: {"service": "asha-seva-backend", "status": "ok"}

# Test login with seeded admin
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"mobile": "0000000000", "password": "admin123"}'
# Expected: {"success": true, "data": {"access_token": "...", "user": {...}}}
```

---

## Step 7 — (Optional) Apply Full Schema from Scratch

If you want to set up a completely fresh database using the provided SQL:

```bash
psql -U postgres -d asha_db -f schema.sql
```

> ⚠️ This will attempt to CREATE tables. If they already exist (from Step 4),
> use `IF NOT EXISTS` in the SQL (already present) or use `migrate.sql` instead.

---

## Verifying Tables

```bash
psql -U postgres -d asha_db -c "\dt"
```

Expected output:
```
              List of relations
 Schema |      Name       | Type  |  Owner
--------+-----------------+-------+----------
 public | anc_records     | table | postgres
 public | children        | table | postgres
 public | families        | table | postgres
 public | family_members  | table | postgres
 public | users           | table | postgres
 public | vaccine_entries | table | postgres
```

---

## Verifying Indexes

```bash
psql -U postgres -d asha_db -c "
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
"
```

---

## Troubleshooting

### Connection refused
```
sqlalchemy.exc.OperationalError: connection to server on socket ... failed
```
→ PostgreSQL is not running. Start it: `sudo service postgresql start`

### Authentication failed
```
FATAL: password authentication failed for user "postgres"
```
→ Check `DB_PASSWORD` in `.env`. If using a special character, it's auto-encoded — but verify the value is correct.

### Module not found
```
ModuleNotFoundError: No module named 'psycopg'
```
→ Run: `pip install psycopg[binary]==3.2.13`

### Table already exists
→ `db.create_all()` is safe to re-run — it only creates missing tables, never drops existing ones.

### Admin seed fails
```
⚠️  Admin seed skipped: ...
```
→ Usually means an admin already exists. Check:
```bash
psql -U postgres -d asha_db -c "SELECT mobile, role FROM users WHERE role='admin';"
```

---

## Default Admin Credentials

| Field | Value |
|-------|-------|
| Mobile | `0000000000` |
| Password | `admin123` |
| Role | `admin` |

> ⚠️ **Change the admin password in production!**
> Use `POST /api/auth/change-password` after first login.

---

## Environment Summary

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | development / production | `development` |
| `SECRET_KEY` | Flask session secret | 64-char hex string |
| `DB_NAME` | PostgreSQL database name | `asha_db` |
| `DB_USER` | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | `your_password` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `JWT_SECRET_KEY` | JWT signing key | 64-char hex string |
| `JWT_ACCESS_TOKEN_EXPIRES` | Token TTL in seconds | `3600` |
| `CORS_ORIGINS` | Allowed Flutter app origins | `http://10.0.2.2,*` |
| `EXPORTS_DIR` | CSV export folder | `exports` |
