# ASHA Seva Backend — API Documentation
**Phase 6 | Version 2.1**

---

## Base URL
```
http://<host>:<port>/api
```

## Authentication
All protected endpoints require a **Bearer JWT** in the `Authorization` header:
```
Authorization: Bearer <access_token>
```
Obtain a token via `POST /api/auth/login`.

---

## Standard Response Envelope
Every response uses this shape:

```json
{
  "success": true | false,
  "message": "Human-readable string",
  "data":    <payload> | null,
  "meta":    { "page": 1, "per_page": 20, "total": 100, "total_pages": 5 }  // paginated only
}
```

Error responses also include:
```json
{ "errors": { "field": ["validation message"] } }   // 422 only
```

---

## Health Check
| Method | Path | Auth |
|--------|------|------|
| GET | `/api/health` | ❌ |

```json
{ "status": "ok", "service": "asha-seva-backend" }
```

---

## 1. Authentication (`/api/auth`)

### Register Supervisor
`POST /api/auth/register/supervisor` — ❌ Public

**Body:**
```json
{
  "name": "Rajesh Sharma",
  "mobile": "9876543210",
  "email": "rajesh@nhm.gov.in",      // optional
  "password": "secure123",
  "worker_id": "SUP001",
  "area": "Khed",
  "district": "Pune"
}
```

### Register ASHA Worker
`POST /api/auth/register/asha` — ❌ Public

Same body as supervisor. `supervisor_id` field links ASHA to a supervisor's `worker_id`.

### Login
`POST /api/auth/login` — ❌ Public

**Body:**
```json
{ "mobile": "9876543210", "password": "secure123" }
```
**Response `data`:**
```json
{
  "access_token": "<jwt>",
  "user": { "id": "...", "name": "...", "role": "asha", "worker_id": "ASH001" }
}
```

### Get Profile
`GET /api/auth/profile` — 🔐 JWT

### Update Profile
`PUT /api/auth/profile` — 🔐 JWT

Allowed fields: `name`, `mobile`, `email`, `area`, `district`

### Change Password
`POST /api/auth/change-password` — 🔐 JWT

```json
{ "old_password": "old", "new_password": "newSecure123" }
```

---

## 2. Families (`/api/families`)

### List Families
`GET /api/families/` — 🔐 JWT

**Query params:** `asha_id`, `page`, `per_page`

### Create Family
`POST /api/families/` — 🔐 JWT

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

### Get Family (with members)
`GET /api/families/<family_id>` — 🔐 JWT

### Update Family
`PUT /api/families/<family_id>` — 🔐 JWT

### Delete Family
`DELETE /api/families/<family_id>` — 🔐 JWT

### List Members
`GET /api/families/<family_id>/members` — 🔐 JWT

### Add Member
`POST /api/families/<family_id>/members` — 🔐 JWT

```json
{
  "name": "Sunita Devi",
  "dob": "1990-05-20",
  "gender": "Female",
  "aadhaar": "123456789012",
  "apl_bpl": "BPL",
  "is_reproductive_pair": true,
  "caste": "OBC",
  "education": "Primary"
}
```

### Update / Delete Member
`PUT /api/families/<family_id>/members/<member_id>` — 🔐 JWT
`DELETE /api/families/<family_id>/members/<member_id>` — 🔐 JWT

---

## 3. ANC / Maternal Health (`/api/anc`)

### List ANC Records
`GET /api/anc/` — 🔐 JWT

**Query params:** `asha_id`, `page`, `per_page`

### Create ANC Record
`POST /api/anc/` — 🔐 JWT

```json
{
  "beneficiary_name": "Meena Sharma",
  "husband_name": "Vijay Sharma",
  "lmp": "2024-01-01",
  "edd": "2024-10-08",
  "gravida": 2,
  "risk_status": "High Risk",
  "mobile": "9876500001",
  "village": "Khed",
  "asha_id": "ASH001"
}
```

`risk_status` values: `Normal` | `Low Risk` | `High Risk`

### Get / Update / Delete ANC Record
`GET /api/anc/<record_id>` — 🔐 JWT
`PUT /api/anc/<record_id>` — 🔐 JWT
`DELETE /api/anc/<record_id>` — 🔐 JWT

---

## 4. Children (`/api/children`)

### List Children
`GET /api/children/` — 🔐 JWT

**Query params:** `asha_id`, `page`, `per_page`

### Register Child
`POST /api/children/` — 🔐 JWT

```json
{
  "child_name": "Aryan",
  "mother_name": "Priya Singh",
  "dob": "2023-06-15",
  "gender": "Male",
  "weight": 3.5,
  "asha_id": "ASH001"
}
```

### Get Child (includes vaccines)
`GET /api/children/<child_id>` — 🔐 JWT

### Update / Delete Child
`PUT /api/children/<child_id>` — 🔐 JWT
`DELETE /api/children/<child_id>` — 🔐 JWT

---

## 5. Vaccine Entries (`/api/vaccines`)

Basic CRUD for individual dose records.

### List All Entries
`GET /api/vaccines/` — 🔐 JWT

### List Vaccines for a Child
`GET /api/vaccines/child/<child_id>` — 🔐 JWT

### Add Vaccine Entry
`POST /api/vaccines/` — 🔐 JWT

```json
{
  "child_id": "<uuid>",
  "name": "BCG",
  "due_date": "2023-06-15",
  "given_date": "2023-06-15",
  "next_due": "2023-07-15",
  "status": "given"
}
```

`status` values: `scheduled` | `due` | `given` | `overdue`

### Get / Update / Delete Vaccine Entry
`GET /api/vaccines/<entry_id>` — 🔐 JWT
`PUT /api/vaccines/<entry_id>` — 🔐 JWT
`DELETE /api/vaccines/<entry_id>` — 🔐 JWT

---

## 6. Vaccination Management (`/api/vaccination`)

Higher-level immunization management endpoints.

### Due / Overdue Vaccines
`GET /api/vaccination/due` — 🔐 JWT

**Query params:** `asha_id`, `days` (default 7 — within N days)

Returns vaccine entries enriched with child info.

### Upcoming Schedule
`GET /api/vaccination/schedule` — 🔐 JWT

**Query params:** `asha_id`, `days` (default 30)

### Bulk-Update Vaccination Status
`POST /api/vaccination/bulk-update` — 🔐 JWT

```json
{
  "vaccine_ids": ["uuid1", "uuid2"],
  "given_date": "2024-05-15",
  "status": "given"
}
```

**Response:**
```json
{ "updated": 2, "not_found": [] }
```

### Coverage Statistics
`GET /api/vaccination/coverage` — 🔐 JWT

**Query params:** `asha_id`

Returns per-ASHA, per-vaccine, per-status counts.

### Defaulters List
`GET /api/vaccination/defaulters` — 🔐 JWT

**Query params:** `asha_id`

Returns children with overdue vaccines including `days_overdue`.

---

## 7. Visit Tracking (`/api/visits`)

### List Visits
`GET /api/visits/` — 🔐 JWT

**Query params:** `asha_id`, `visit_type`, `status`, `from_date`, `to_date`, `page`, `per_page`

`visit_type` values: `maternal` | `child` | `general` | `family_planning` | `immunization`
`status` values: `scheduled` | `completed` | `missed` | `cancelled`

### Record Visit
`POST /api/visits/` — 🔐 JWT

```json
{
  "asha_id": "ASH001",
  "beneficiary_name": "Sunita Devi",
  "beneficiary_id": "<family_member_uuid>",
  "village": "Khed",
  "visit_type": "maternal",
  "visit_date": "2024-05-10",
  "status": "completed",
  "notes": "BP slightly elevated",
  "weight_kg": 62.5,
  "bp_systolic": 130,
  "bp_diastolic": 85,
  "temperature_c": 37.2,
  "medicines_given": "IFA tablets, Calcium",
  "referred": false,
  "next_visit_date": "2024-06-10"
}
```

### Get / Update / Delete Visit
`GET /api/visits/<visit_id>` — 🔐 JWT
`PUT /api/visits/<visit_id>` — 🔐 JWT
`DELETE /api/visits/<visit_id>` — 🔐 JWT

### Visit Summary Report
`GET /api/visits/report/summary` — 🔐 JWT

**Query params:** `asha_id`, `from_date`, `to_date`

Returns counts grouped by `visit_type + status`.

### Upcoming Scheduled Visits
`GET /api/visits/schedule` — 🔐 JWT

**Query params:** `asha_id`, `days` (default 30)

---

## 8. Family Planning (`/api/family-planning`)

### List Records
`GET /api/family-planning/` — 🔐 JWT

**Query params:** `asha_id`, `method`, `status`, `village`, `page`, `per_page`

`method` values: `OCP` | `IUCD` | `Condom` | `Injectable` | `Sterilization` | `LAM` | `NFP` | `None` | `Other`
`status` values: `active` | `discontinued` | `completed` | `follow_up`

### Create Record
`POST /api/family-planning/` — 🔐 JWT

```json
{
  "asha_id": "ASH001",
  "beneficiary_name": "Sunita Patil",
  "husband_name": "Ramesh Patil",
  "mobile": "9876500002",
  "village": "Manchar",
  "age": 28,
  "method": "IUCD",
  "method_start_date": "2024-03-01",
  "status": "active",
  "counselling_date": "2024-02-20",
  "counselling_notes": "Counselled on IUCD benefits and side effects",
  "next_followup_date": "2024-06-01",
  "living_children": 2
}
```

### Get / Update / Delete Record
`GET /api/family-planning/<record_id>` — 🔐 JWT
`PUT /api/family-planning/<record_id>` — 🔐 JWT
`DELETE /api/family-planning/<record_id>` — 🔐 JWT

### Upcoming Follow-ups
`GET /api/family-planning/follow-ups` — 🔐 JWT

**Query params:** `asha_id`, `days` (default 30)

---

## 9. Reports (`/api/reports`)

All report endpoints support optional `asha_id`, `from_date`, `to_date` unless noted.

### Dashboard Stats (Admin/Supervisor)
`GET /api/reports/dashboard` — 🔐 JWT

Returns system-wide counts: workers, families, ANC records, children, vaccines, visits, FP records.

### Visit Statistics
`GET /api/reports/visits` — 🔐 JWT

Breakdown by `visit_type + status`.

### Maternal Health Report
`GET /api/reports/maternal-health` — 🔐 JWT

ANC counts by `risk_status` + mothers due this month.

### Child Health Report
`GET /api/reports/child-health` — 🔐 JWT

Children by gender + vaccines by status.

### Family Planning Report
`GET /api/reports/family-planning` — 🔐 JWT

FP records by method and status.

### Per-Worker Performance Report
`GET /api/reports/worker/<asha_id>` — 🔐 JWT

Full stats for one ASHA worker: families, ANC, children, vaccines given, visits completed, FP counselled.

---

## 10. CSV Import / Export (`/api`)

### List Supported Tables
`GET /api/tables` — 🔐 JWT

### Export Table
`GET /api/export/<table_name>` — 🔐 JWT

Downloads `<table_name>.csv`. Supported: `users`, `families`, `family_members`, `anc_records`, `children`, `vaccine_entries`

### Import Table
`POST /api/import/<table_name>` — 🔐 JWT

`Content-Type: multipart/form-data`, field name: `file`

**Response:**
```json
{
  "table": "families",
  "total_rows": 50,
  "inserted": 45,
  "duplicates": 5,
  "errors": ["Row 12: aadhaar must be 12 digits"]
}
```

---

## Database Schema — Phase 6 New Tables

### `visit_records`
| Column | Type | Notes |
|--------|------|-------|
| id | VARCHAR(36) PK | UUID |
| asha_id | VARCHAR(50) NOT NULL | Soft FK → users.worker_id |
| beneficiary_id | VARCHAR(36) | Soft FK → family_members.id |
| beneficiary_name | VARCHAR(100) NOT NULL | |
| village | VARCHAR(100) | |
| visit_type | VARCHAR(30) | maternal/child/general/family_planning/immunization |
| visit_date | DATE NOT NULL | |
| status | VARCHAR(20) | scheduled/completed/missed/cancelled |
| notes | TEXT | Clinical observations |
| weight_kg | NUMERIC(5,2) | |
| bp_systolic / bp_diastolic | INTEGER | mmHg |
| temperature_c | NUMERIC(4,1) | Celsius |
| medicines_given | TEXT | |
| referred | BOOLEAN | |
| referral_notes | TEXT | |
| next_visit_date | DATE | |
| created_at / updated_at | TIMESTAMPTZ | Auto-managed |

### `family_planning_records`
| Column | Type | Notes |
|--------|------|-------|
| id | VARCHAR(36) PK | UUID |
| asha_id | VARCHAR(50) NOT NULL | Soft FK → users.worker_id |
| beneficiary_name | VARCHAR(100) NOT NULL | |
| husband_name | VARCHAR(100) | |
| mobile | VARCHAR(15) | |
| village | VARCHAR(100) | |
| age | INTEGER | 10–60 range |
| method | VARCHAR(30) | OCP/IUCD/Condom/Injectable/Sterilization/LAM/NFP/None/Other |
| method_start_date / method_end_date | DATE | |
| status | VARCHAR(20) | active/discontinued/completed/follow_up |
| counselling_date | DATE | |
| counselling_notes | TEXT | |
| side_effects / complications | TEXT | |
| next_followup_date | DATE | Indexed |
| followup_notes | TEXT | |
| living_children | INTEGER | |
| created_at / updated_at | TIMESTAMPTZ | Auto-managed |

---

## Error Codes Reference
| Code | Meaning |
|------|---------|
| 400 | Bad request / missing required field |
| 401 | Unauthenticated (missing or expired JWT) |
| 403 | Forbidden (account deactivated) |
| 404 | Resource not found |
| 409 | Conflict (duplicate mobile, aadhaar, etc.) |
| 422 | Validation error (field-level errors in `errors` key) |
| 500 | Internal server error |
