# ASHA Seva Backend

Production-ready Flask backend for the ASHA Seva healthcare Flutter app.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Framework | Flask 3.x |
| ORM | Flask-SQLAlchemy 3 + SQLAlchemy 2 |
| Database | PostgreSQL (psycopg v3 driver) |
| Auth | Flask-JWT-Extended |
| Password | Flask-Bcrypt |
| Validation | Flask-Marshmallow |
| CSV / Data | pandas |
| CORS | Flask-CORS |

---

## Project Structure

```
backend/
├── app.py                     ← entry point
├── .env                       ← environment variables (never commit)
├── requirements.txt
├── exports/                   ← CSV exports land here
├── logs/
└── app/
    ├── __init__.py            ← application factory (create_app)
    ├── extensions.py          ← db, jwt, bcrypt, ma singletons
    ├── core/
    │   └── config.py          ← DevelopmentConfig / ProductionConfig
    ├── models/
    │   ├── user.py
    │   ├── family.py          ← FamilyModel + FamilyMemberModel
    │   ├── anc.py
    │   ├── children.py
    │   └── vaccine.py
    ├── schemas/
    │   ├── user_schema.py
    │   ├── family_schema.py
    │   ├── anc_schema.py
    │   └── children_schema.py
    ├── routes/
    │   ├── auth.py
    │   ├── family.py
    │   ├── anc.py
    │   ├── children.py
    │   ├── vaccine.py
    │   └── csv_routes.py
    └── utils/
        ├── csv_utils.py       ← export / import engine
        └── response.py        ← standard JSON response helpers
```

---

## Setup

### 1. Create the PostgreSQL database

```sql
CREATE DATABASE asha_db;
```

### 2. Clone / place this backend folder

```
your_project/
├── asha_app/          ← Flutter frontend
└── backend/           ← this folder
```

### 3. Create a virtual environment

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Edit `.env` (already created). The defaults match the DB credentials you provided:

```env
FLASK_ENV=development
SECRET_KEY=change-me
DB_NAME=asha_db
DB_USER=postgres
DB_PASSWORD=Jiya@664         # @ is URL-encoded automatically
DB_HOST=localhost
DB_PORT=5432
JWT_SECRET_KEY=jwt-secret
```

> **Note:** `@` in the password is automatically URL-encoded via `urllib.parse.quote_plus`. No manual escaping needed.

### 6. Run the development server

```bash
python app.py
```

Server starts at: `http://localhost:5000`  
Tables are created automatically on first run.

### 7. Production (Gunicorn)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## API Reference

### Health check
```
GET /api/health
→ { "status": "ok", "service": "asha-seva-backend" }
```

---

### Authentication  `POST /api/auth/…`

#### Register ASHA worker
```http
POST /api/auth/register/asha
Content-Type: application/json

{
  "name": "Priya Sharma",
  "mobile": "9876543210",
  "password": "secret123",
  "role": "asha",
  "worker_id": "ASH001",
  "area": "Khed",
  "district": "Pune"
}
```
```json
{
  "success": true,
  "message": "Asha registered successfully.",
  "data": { "id": "uuid", "name": "Priya Sharma", "role": "asha", ... }
}
```

#### Register Supervisor
```http
POST /api/auth/register/supervisor
```
(Same body, role becomes "supervisor" automatically.)

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{ "mobile": "9876543210", "password": "secret123" }
```
```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "access_token": "<jwt-token>",
    "refresh_token": "<refresh-jwt-token>",
    "user": { "id": "uuid", "name": "Priya Sharma", "role": "asha" }
  }
}
```

#### Refresh token
```http
POST /api/auth/refresh
Authorization: Bearer <refresh-token>
```
```json
{
  "success": true,
  "message": "Token refreshed successfully.",
  "data": { "access_token": "<jwt-token>" }
}
```

#### Logout
```http
POST /api/auth/logout
Authorization: Bearer <access-token>
```
```json
{
  "success": true,
  "message": "Logged out successfully."
}
```

#### Get Profile  *(JWT required)*
```http
GET /api/auth/profile
Authorization: Bearer <token>
```

#### Change Password  *(JWT required)*
```http
POST /api/auth/change-password
Authorization: Bearer <token>
Content-Type: application/json

{ "old_password": "secret123", "new_password": "newpass456" }
```

---

### Families  `GET|POST /api/families/…`  *(JWT required)*

All family endpoints require `Authorization: Bearer <token>`.

| Method | URL | Description |
|--------|-----|-------------|
| GET    | `/api/families/?page=1&per_page=20` | List families (paginated) |
| POST   | `/api/families/` | Create family |
| GET    | `/api/families/<id>` | Get family + members |
| PUT    | `/api/families/<id>` | Update family |
| DELETE | `/api/families/<id>` | Delete family |
| POST   | `/api/families/<id>/members` | Add member |
| GET    | `/api/families/<id>/members` | List members |
| PUT    | `/api/families/<id>/members/<mid>` | Update member |
| DELETE | `/api/families/<id>/members/<mid>` | Delete member |

#### Create family
```json
{
  "family_head": "Ramesh Kumar",
  "home_no": "42-B",
  "address": "Near Hanuman Temple",
  "village": "Khed",
  "taluka": "Khed",
  "district": "Pune",
  "asha_id": "ASH001"
}
```

#### Add family member
```json
{
  "name": "Sunita Devi",
  "dob": "1990-05-20",
  "gender": "Female",
  "aadhaar": "123456789012",
  "apl_bpl": "BPL",
  "is_reproductive_pair": true
}
```

---

### ANC Records  `/api/anc/`  *(JWT required)*

| Method | URL | Description |
|--------|-----|-------------|
| GET  | `/api/anc/?asha_id=ASH001` | List records |
| POST | `/api/anc/` | Create record |
| GET  | `/api/anc/<id>` | Get record |
| PUT  | `/api/anc/<id>` | Update record |
| DELETE | `/api/anc/<id>` | Delete record |

```json
{
  "beneficiary_name": "Meena Sharma",
  "husband_name": "Suresh Sharma",
  "lmp": "2024-01-01",
  "edd": "2024-10-08",
  "gravida": 2,
  "risk_status": "Normal",
  "mobile": "9123456789",
  "village": "Khed",
  "asha_id": "ASH001"
}
```

---

### Children  `/api/children/`  *(JWT required)*

```json
{
  "child_name": "Aryan",
  "mother_name": "Priya",
  "dob": "2023-06-15",
  "gender": "Male",
  "weight": 3.5,
  "asha_id": "ASH001"
}
```

---

### Vaccines  `/api/vaccines/`  *(JWT required)*

```json
{
  "child_id": "<child-uuid>",
  "name": "BCG",
  "due_date": "2023-06-15",
  "given_date": "2023-06-15",
  "status": "given"
}
```

Special:  `GET /api/vaccines/child/<child_id>` returns all vaccines for one child.

---

### CSV Export/Import  *(JWT required)*

#### List available tables
```http
GET /api/tables
Authorization: Bearer <token>
```
```json
{
  "success": true,
  "data": ["users", "families", "family_members", "anc_records", "children", "vaccine_entries"]
}
```

#### Export table to CSV
```http
GET /api/export/families
Authorization: Bearer <token>
→ downloads families.csv (UTF-8 with BOM, Excel-compatible)
```

Exported files are also saved to `backend/exports/<table_name>.csv`.

#### Import CSV into table
```http
POST /api/import/families
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <families.csv>
```
```json
{
  "success": true,
  "message": "Import complete. 45 inserted, 5 duplicates skipped.",
  "data": {
    "table": "families",
    "total_rows": 50,
    "inserted": 45,
    "duplicates": 5,
    "errors": []
  }
}
```

**Duplicate detection keys per table:**

| Table | Unique key columns |
|-------|-------------------|
| users | mobile, worker_id |
| families | home_no + village + family_head |
| family_members | aadhaar + name + family_id |
| anc_records | beneficiary_name + mobile + lmp |
| children | child_name + mother_name + dob |
| vaccine_entries | child_id + name + due_date |

---

## Flutter Integration

In `lib/services/api_service.dart`:

```dart
static const String baseUrl = 'http://YOUR_MACHINE_IP:5000/api';
static const bool useMock = false;
```

For Android emulator use `10.0.2.2:5000` instead of `localhost`.

All protected endpoints need the JWT in the Authorization header:
```dart
headers: {
  'Authorization': 'Bearer $token',
  'Content-Type': 'application/json',
}
```

---

## Error Response Format

All errors follow the same envelope:

```json
{
  "success": false,
  "message": "Validation failed.",
  "data": null,
  "errors": { "mobile": ["Not a valid string."] }
}
```

HTTP status codes used: `200 201 207 400 401 403 404 405 409 422 500`
