# Data Persistence Guide

## Why data wasn't saving after reload/restart

The original code was configured **PostgreSQL-only**. If PostgreSQL wasn't running or the `asha_db` database didn't exist, the app would log a silent error at startup (`❌ Could not create tables`) and continue — leaving every write silently failing. On restart, any in-memory state was lost.

---

## What was changed

### `app/core/config.py` — Smart database selection

The config now picks the database automatically:

```
Priority 1 → DATABASE_URL env var          (Railway / Heroku / Render)
Priority 2 → PostgreSQL (DB_HOST, etc.)    — only if the host is reachable
Priority 3 → SQLite at app/database/asha_seva.db  ← always persistent
```

This means the app **always persists data** even if PostgreSQL isn't installed.

### `app/__init__.py` — Fail loudly + show active DB

- The health endpoint (`GET /api/health`) now reports which database is active and whether it's connected:
  ```json
  { "status": "ok", "service": "asha-seva-backend", "database": "postgresql", "db_status": "connected" }
  ```
- If `db.create_all()` fails, the app exits immediately with a clear error instead of silently running broken.

---

## Setup options

### Option A — Docker PostgreSQL (recommended, easiest)

```bash
# Start PostgreSQL in background (data lives in a Docker named volume)
docker compose up -d

# Run the app
python app.py
```

Data persists across restarts because Docker uses a **named volume** (`asha_seva_pgdata`).  
Stops but keeps data: `docker compose down`  
Stops AND deletes data: `docker compose down -v` ← use with caution

---

### Option B — Local PostgreSQL

1. Install PostgreSQL and make sure it's running:
   ```bash
   # macOS
   brew services start postgresql@16

   # Ubuntu/Debian
   sudo systemctl start postgresql
   sudo systemctl enable postgresql   # auto-start on boot
   ```

2. Create the database:
   ```bash
   psql -U postgres -c "CREATE DATABASE asha_db;"
   ```

3. Check your `.env` matches your PG credentials, then run:
   ```bash
   python app.py
   ```

---

### Option C — SQLite (development/offline, zero setup)

No action needed. If PostgreSQL is unavailable, the app automatically uses:

```
backend/app/database/asha_seva.db
```

This file persists across app restarts. Back it up like any important file.

> ⚠️ SQLite is single-writer only. Don't use it in production with multiple gunicorn workers.

---

## Diagnosing persistence issues

Run the built-in diagnostic:

```bash
# Check what's wrong
python check_db.py

# Check + auto-fix (creates missing DB, runs create_all)
python check_db.py --fix
```

Also check the health endpoint after starting:
```bash
curl http://localhost:5000/api/health
```

Expected output (PostgreSQL):
```json
{ "status": "ok", "database": "postgresql", "db_status": "connected" }
```

Expected output (SQLite fallback):
```json
{ "status": "ok", "database": "sqlite", "db_status": "connected" }
```

---

## Production checklist

| Item | Action |
|------|--------|
| PostgreSQL running as a service | `sudo systemctl enable postgresql` |
| Database exists | `CREATE DATABASE asha_db;` |
| `.env` has correct credentials | Double-check `DB_PASSWORD` |
| Run with gunicorn (not dev server) | `gunicorn -w 4 -b 0.0.0.0:5000 app:app` |
| Never set `FLASK_ENV=testing` in prod | That forces in-memory SQLite |
| Back up the database regularly | `pg_dump asha_db > backup.sql` |

---

## Common problems

| Symptom | Cause | Fix |
|---------|-------|-----|
| Data gone after restart | PostgreSQL wasn't running; fell through to nothing | Run `python check_db.py --fix` |
| `FATAL — Could not create tables` | DB doesn't exist or wrong password | Create DB or fix `.env` |
| `connection refused` on port 5432 | PostgreSQL not running | `sudo systemctl start postgresql` |
| Works in dev, loses data in prod | `FLASK_ENV=testing` set accidentally | Remove or set to `production` |
| SQLite used unexpectedly | PostgreSQL host unreachable | Fix PG host or use Docker |
