# ASHA Seva — Redesigned 🏥
**Full-Stack Health Worker Application**

---

## 📁 Project Structure

```
asha_redesigned/
├── frontend/          ← Flutter app (redesigned)
│   └── lib/
│       ├── screens/
│       │   ├── dashboard/       ← asha_dashboard, admin_dashboard, supervisor_dashboard
│       │   ├── auth/            ← login_screen (redesigned)
│       │   └── analytics/       ← analytics_screen (NEW - charts + ML insights)
│       ├── widgets/             ← common_widgets (redesigned, 15+ components)
│       ├── services/            ← api_service (all new endpoints)
│       └── utils/               ← app_theme (full Poppins design system)
│
└── backend/           ← FastAPI Python backend
    ├── app/
    │   ├── main.py              ← App entry, CORS, scheduler
    │   ├── database.py          ← SQLAlchemy + CSV auto-sync
    │   ├── models/models.py     ← 12 DB tables
    │   ├── routes/              ← 17 route modules
    │   │   ├── auth.py          ← login, register, profile
    │   │   ├── dashboard.py     ← /dashboard/summary
    │   │   ├── patients.py      ← CRUD + search + pagination
    │   │   ├── pregnancies.py   ← CRUD
    │   │   ├── anc.py           ← ANC visit CRUD
    │   │   ├── immunization.py  ← Child immunization CRUD
    │   │   ├── home_visits.py   ← CRUD
    │   │   ├── medicine_stock.py ← Stock + low-stock alert
    │   │   ├── ml_routes.py     ← 3 ML prediction endpoints
    │   │   ├── reports.py       ← Monthly / village / worker
    │   │   ├── alerts.py        ← CRUD
    │   │   ├── villages.py      ← Village health
    │   │   ├── schemes.py       ← Government schemes
    │   │   ├── ai_assistant.py  ← Health Q&A
    │   │   ├── training.py      ← Training records
    │   │   ├── supervisor_notes.py
    │   │   └── sync.py          ← Offline sync
    │   ├── ml/
    │   │   └── trainer.py       ← RandomForest model trainer
    │   └── services/
    │       └── backup_service.py ← Daily CSV backup (APScheduler)
    ├── csv_exports/             ← Auto-generated CSVs
    │   └── backups/             ← Timestamped daily backups
    ├── requirements.txt
    └── .env
```

---

## 🚀 Backend Setup

### 1. Create PostgreSQL Database
```sql
CREATE DATABASE asha_db;
```

### 2. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure environment
Edit `.env`:
```
DB_NAME=asha_db
DB_USER=postgres
DB_PASSWORD=Jiya%40664      # % encodes the @ in your password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=change_this_to_a_long_random_string
```

### 4. Run the server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Train ML models (first time)
```bash
# Hit this endpoint after adding some data:
curl -X POST http://localhost:8000/api/ml/retrain \
  -H "Authorization: Bearer <admin_token>"
```

The API docs are available at: **http://localhost:8000/docs**

---

## 📱 Flutter Frontend Setup

### 1. Add Poppins font
Download Poppins from [Google Fonts](https://fonts.google.com/specimen/Poppins) and place in:
```
frontend/assets/fonts/
  Poppins-Regular.ttf
  Poppins-Medium.ttf
  Poppins-SemiBold.ttf
  Poppins-Bold.ttf
  Poppins-ExtraBold.ttf
```

### 2. Update API base URL
In `lib/services/api_service.dart`:
```dart
// Android emulator:
static const String baseUrl = 'http://10.0.2.2:8000/api';

// Physical device (same WiFi):
static const String baseUrl = 'http://192.168.x.x:8000/api';

// iOS simulator / web:
static const String baseUrl = 'http://localhost:8000/api';
```

### 3. Install packages & run
```bash
cd frontend
flutter pub get
flutter run
```

---

## ✨ What's New in This Redesign

### Frontend (Flutter)
| Feature | Before | After |
|---------|--------|-------|
| Font | Roboto | Poppins (weights 400–800) |
| Theme | Basic green | Full design system with semantic colors |
| Login | Flat form | Card with gradient hero + animated role selector |
| Dashboard | Static 0-value cards | Live API data + animated skeleton loading |
| Stats | Simple number cards | Trend indicators + tap-to-navigate |
| ML Section | None | AI Health Insights card (risk counts) |
| Analytics | None | **NEW full screen** with 4 tabs + charts |
| Alerts | None | Auto-dismiss cards on dashboard |
| Village Score | None | Circular progress + 3 sub-metric bars |
| Module tiles | Basic grid | Animated press + badge counts |
| Loading | Spinner | Skeleton shimmer |

### Backend (FastAPI)
| Feature | Status |
|---------|--------|
| PostgreSQL + SQLAlchemy | ✅ |
| JWT Auth (role-based) | ✅ |
| Auto CSV sync on every write | ✅ |
| Daily timestamped backup | ✅ |
| ML: Pregnancy risk | ✅ RandomForest + rule-based fallback |
| ML: Nutrition risk | ✅ WHO Z-score + RandomForest |
| ML: Missed visit | ✅ Probability + interventions |
| ML: Auto-retrain from DB | ✅ |
| Dashboard summary API | ✅ |
| Village health stats | ✅ |
| CRUD for all 11 modules | ✅ |
| Pagination + search | ✅ |
| Offline sync endpoint | ✅ |
| Reports (monthly/village/worker) | ✅ |
| Audit logs (created_by field) | ✅ |

---

## 🔑 API Reference

### Auth
```
POST /api/login
POST /api/register/supervisor
POST /api/register/asha
GET  /api/profile
PUT  /api/profile
POST /api/change-password
POST /api/logout
```

### Dashboard
```
GET /api/dashboard/summary
GET /api/dashboard/village-stats
```

### ML Predictions
```
POST /api/ml/pregnancy-risk
POST /api/ml/nutrition-risk
POST /api/ml/missed-visit
POST /api/ml/retrain          (admin/supervisor)
```

### All Modules (CRUD pattern)
```
GET/POST        /api/patients
GET/PUT/DELETE  /api/patients/{id}
GET/POST        /api/pregnancies
GET/POST        /api/anc
GET/POST        /api/immunization
GET/POST        /api/home-visits
GET/POST/PUT    /api/medicine-stock
GET             /api/alerts
PUT             /api/alerts/{id}/read
GET             /api/reports/monthly
GET             /api/reports/village
GET             /api/reports/worker-performance
```

---

## 📊 CSV Auto-Sync

Every `INSERT` or `UPDATE` to PostgreSQL **automatically** writes to:
```
backend/csv_exports/<table_name>.csv
```

Daily backups run at **2:00 AM** to:
```
backend/csv_exports/backups/YYYY-MM-DD_HH-MM/<table>.csv
```

Only the **last 30 backups** are kept (auto-pruned).

---

## 🔒 Role Permissions

| Endpoint Type | Admin | Supervisor | ASHA |
|--------------|-------|-----------|------|
| All data read | ✅ | ✅ zone only | ✅ village only |
| Register users | ✅ | ❌ | ❌ |
| ML retrain | ✅ | ✅ | ❌ |
| Reports | ✅ all | ✅ zone | ✅ self |
| Delete records | ✅ | ✅ | ❌ |
