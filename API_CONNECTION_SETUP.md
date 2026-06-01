# API Connection Setup - Flutter to Backend

## ✅ Status: FULLY OPERATIONAL

**Backend:** Running ✅  
**Database:** PostgreSQL connected ✅  
**Authentication:** Working ✅  
**Data Persistence:** Working ✅  
**Flutter Integration:** Ready ✅

---

## Test Credentials
```
Mobile: 9876543210
Password: test@123
Role: ASHA Worker
```

---

## Flutter App Configuration

### Current Configuration
- **File:** `asha_app/.env`
- **Current API URL:** `http://10.0.2.2:5000/api` (Android Emulator)

### Connection Details by Platform

#### Android Emulator
```
API_BASE_URL=http://10.0.2.2:5000/api
```
✅ This is already configured in `.env`

#### iOS Simulator
```
API_BASE_URL=http://127.0.0.1:5000/api
```

#### Physical Device (same network)
```
API_BASE_URL=http://<YOUR_MACHINE_IP>:5000/api
# Example: http://192.168.x.x:5000/api
```

#### Web (localhost)
```
API_BASE_URL=http://localhost:5000/api
```

---

## Verify Connection is Working

### Step 1: Run Backend (if not running)
```bash
cd backend
python app.py
```

### Step 2: Test API with curl or Python
```bash
# Login test
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"mobile":"9876543210","password":"test@123"}'
```

### Step 3: Check Flutter App Logs
When running Flutter app, look for:
```
✅ Should see API requests being logged
❌ Watch for 401, 422, or 500 errors
```

---

## Common Issues & Fixes

### Issue 1: "Connection refused" / "Failed to connect to backend"
**Cause:** Backend not running or wrong API URL
**Fix:** 
1. Start backend: `python app.py` in backend folder
2. Check `.env` has correct `API_BASE_URL`
3. Verify port 5000 is open: `netstat -ano | findstr :5000`

### Issue 2: "401 Unauthorized"
**Cause:** Invalid credentials or token expired
**Fix:**
1. Use correct credentials: `9876543210` / `test@123`
2. Check token refresh is working
3. Clear app cache and login again

### Issue 3: "422 Validation Failed"
**Cause:** Request payload has wrong format
**Fix:**
1. Check API expects specific field names (beneficiary_name, not patient_name)
2. Verify date format: `YYYY-MM-DD`
3. Check visit_type is one of: `general`, `maternal`, `child`, `family_planning`, `immunization`

### Issue 4: Records created but not stored in DB
**Cause:** API accepts but doesn't commit to database
**Fix:**
1. Check backend logs for errors
2. Verify database connection: `python check_db.py`
3. Check schema compatibility

---

## API Endpoints Ready for Use

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/profile` - Get profile
- `PUT /api/auth/profile` - Update profile

### Visits (Health Records)
- `POST /api/visits/` - Create visit
- `GET /api/visits/` - List visits
- `GET /api/visits/<id>` - Get visit
- `PUT /api/visits/<id>` - Update visit
- `DELETE /api/visits/<id>` - Delete visit

### Families (Beneficiaries)
- `POST /api/families/` - Register family
- `GET /api/families/` - List families
- `GET /api/families/<id>` - Get family details

---

## Data Storage Workflow

```
Flutter App
    ↓
API Service (api_service.dart)
    ↓
HTTP POST to Backend (http://10.0.2.2:5000/api/visits/)
    ↓
Flask Backend (app/routes/visits.py)
    ↓
Validation (Marshmallow Schema)
    ↓
Save to PostgreSQL Database
    ↓
Response to App
```

---

## Verify Data is Storing

### From Terminal
```bash
cd backend
python -c "
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    result = db.session.execute(db.text('SELECT COUNT(*) FROM visit_records'))
    count = result.scalar()
    print(f'Total visits in database: {count}')
"
```

### From Flutter App
1. Login with test credentials
2. Create a visit record
3. Check terminal output above - count should increase

---

## Next Steps

1. **Update Flutter app `.env` if needed** based on your platform (Android, iOS, Web)
2. **Start backend server:** `python app.py` from backend folder
3. **Run Flutter app** with correct API URL
4. **Login** with credentials: `9876543210` / `test@123`
5. **Create test data** (visit, beneficiary, etc.)
6. **Verify** data appears in database using query above

**Once confirmed working, you can create real ASHA worker accounts and data.**
