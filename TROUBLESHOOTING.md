# ASHA App - Troubleshooting Guide

## Installation Issues

### ❌ Python not found

**Error:** `'python' is not recognized as an internal or external command`

**Solution:**
1. Install Python 3.11 or 3.12: https://www.python.org/downloads/
2. During installation, **check "Add Python to PATH"**
3. Restart your terminal/IDE

**Verify:**
```bash
python --version
# Should show: Python 3.11.x or 3.12.x
```

---

### ❌ Flutter not found

**Error:** `'flutter' is not recognized as an internal or external command`

**Solution:**
1. Install Flutter: https://flutter.dev/docs/get-started/install
2. Add Flutter to PATH in Windows:
   - Find Flutter installation folder (usually `C:\flutter`)
   - Add `C:\flutter\bin` to Windows PATH environment variable
3. Restart terminal

**Verify:**
```bash
flutter --version
```

---

### ❌ Docker not found

**Error:** `Docker not found` or `docker: command not found`

**Solution:**
1. Install Docker Desktop: https://www.docker.com/products/docker-desktop
2. Start Docker Desktop application
3. Restart terminal

**Alternative:** Use local PostgreSQL instead of Docker
- Install PostgreSQL: https://www.postgresql.org/download/
- Create database manually (see [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md) Option B)

---

## Backend Issues

### ❌ Backend won't start - ModuleNotFoundError

**Error:**
```
ModuleNotFoundError: No module named 'flask'
ModuleNotFoundError: No module named 'app'
```

**Solution:**

1. **Verify virtual environment is activated** (should see `(venv)` in terminal prompt):
```bash
cd e:\FlutterProject\backend

# On Windows:
venv\Scripts\activate

# You should see:
# (venv) e:\FlutterProject\backend>
```

2. **Reinstall dependencies:**
```bash
pip install -r requirements.txt
```

3. **If still failing**, try:
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Clear cache
pip cache purge

# Reinstall
pip install -r requirements.txt
```

---

### ❌ Backend won't connect to database

**Error:**
```
could not translate host name "localhost" to address: Unknown host
or
FATAL: Ident authentication failed for user "postgres"
```

**Solution:**

1. **Check .env file** exists in `backend/` directory:
```bash
cd e:\FlutterProject\backend
dir .env
```

2. **Check database credentials in .env:**
```bash
# These should match your Docker setup or PostgreSQL install:
DB_NAME=asha_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

3. **Verify database is running:**

   **If using Docker:**
   ```bash
   docker ps
   # Should show: asha_seva_db container running
   
   # If not running, start it:
   cd backend
   docker compose up -d
   ```

   **If using local PostgreSQL:**
   ```bash
   # Check PostgreSQL service is running
   # On Windows: Services app → PostgreSQL → should be "Running"
   ```

4. **Test connection manually:**
```bash
# Using psql (if installed):
psql -U postgres -d asha_db -h localhost
# Enter password: postgres

# Should connect successfully
```

5. **Verify Docker database is healthy:**
```bash
docker compose ps
# Check STATUS column - should be "Up (healthy)"

# If not healthy, restart:
docker compose down
docker compose up -d
```

---

### ❌ Port 5000 already in use

**Error:**
```
Address already in use
OSError: [Errno 48] Address in use
```

**Solution:**

1. **Find process using port 5000:**
```bash
netstat -ano | findstr :5000

# Find the PID (Process ID) in the last column
# Example output: ... LISTENING       12345

tasklist | findstr 12345
```

2. **Kill the process:**
```bash
taskkill /PID 12345 /F
```

OR

3. **Change port in .env:**
```ini
PORT=5001  # Change 5000 to 5001
```

Then update CORS_ORIGINS if needed:
```ini
CORS_ORIGINS=http://localhost:5001,http://localhost:8080,http://10.0.2.2:5001
```

---

### ❌ CORS errors in browser console

**Error:**
```
Access to XMLHttpRequest from 'http://localhost:8080' has been blocked by CORS policy
```

**Solution:**

Make sure `.env` has correct CORS_ORIGINS:
```ini
CORS_ORIGINS=http://localhost:8080,http://localhost:3000,http://10.0.2.2
```

Restart backend after changing.

---

### ❌ JWT token expired or invalid

**Error:**
```
{"msg":"Token has expired"}
or
{"msg":"Invalid token"}
```

**Solution:**

1. **Clear browser storage and re-login:**
   - Open Chrome DevTools (F12)
   - Go to Application → Storage → Clear All
   - Log back in

2. **Check JWT_SECRET_KEY in .env:**
```ini
JWT_SECRET_KEY=jwt-secret-key-change-in-production
```

3. **Verify JWT_ACCESS_TOKEN_EXPIRES:**
```ini
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour in seconds
```

---

## Database Issues

### ❌ Docker database won't start

**Error:**
```
docker: error response from daemon
or
Container exits immediately
```

**Solution:**

1. **Check Docker is running:**
   - Open Docker Desktop application

2. **View logs:**
```bash
docker compose logs postgres
```

3. **Restart database:**
```bash
cd backend
docker compose down
docker compose up -d
```

4. **Check volume:**
```bash
docker volume ls | findstr asha_seva_pgdata

# If volume exists but corrupted:
docker volume rm asha_seva_pgdata
docker compose up -d
# ⚠️ This will delete all data!
```

---

### ❌ Database file permissions error (Windows)

**Error:**
```
Permission denied: asha_seva_pgdata
```

**Solution:**

1. **Check Docker has permission to access the volume:**
```bash
docker volume inspect asha_seva_pgdata
# Note the Mountpoint
```

2. **Grant Docker permissions** (if needed):
   - Right-click Docker → Settings
   - Resources → File Sharing
   - Add `e:\FlutterProject` to shared paths

3. **Restart Docker and try again:**
```bash
docker compose down
docker compose up -d
```

---

### ❌ Migration/Schema errors

**Error:**
```
no such table: user
or
column does not exist
```

**Solution:**

1. **Reset database** (⚠️ deletes all data):
```bash
# Stop backend
# Stop Docker:
docker compose down -v

# Start again:
docker compose up -d

# Restart backend - tables auto-create
python app.py
```

2. **Or manually create tables from schema:**
```bash
cd backend
psql -U postgres -d asha_db -f schema.sql
```

---

## Frontend Issues

### ❌ Flutter won't compile

**Error:**
```
gradle build failed
or
Build failed for web
```

**Solution:**

1. **Clean and rebuild:**
```bash
cd e:\FlutterProject\asha_app

flutter clean
flutter pub get
flutter run -d chrome
```

2. **Update Flutter and dependencies:**
```bash
flutter upgrade
flutter pub get
```

3. **Check Flutter health:**
```bash
flutter doctor
# Fix any issues it reports
```

---

### ❌ Frontend can't reach backend

**Error:**
```
Connection refused to http://localhost:5000
or
Failed to connect to backend
```

**Solution:**

1. **Verify backend is running:**
   - Check terminal where backend is running
   - Should see: `Running on http://0.0.0.0:5000/`

2. **Check CORS is configured:**
   - Backend `.env` should have:
   ```ini
   CORS_ORIGINS=http://localhost:8080
   ```

3. **Check frontend API URL:**
   - Search in `lib/` for `api_layer.dart` or `api` folder
   - Verify it's using `http://localhost:5000` for web
   - Verify it's using `http://10.0.2.2:5000` for Android emulator

4. **Test manually:**
```bash
# In any terminal:
curl http://localhost:5000/
# Should return a response (even if error)
```

---

### ❌ Flutter web on Android emulator

**Error:**
```
Connection refused to http://10.0.2.2:5000
```

**Solution:**

1. **Verify backend is running on 5000:**
```bash
netstat -ano | findstr :5000
```

2. **Check app is using correct URL for emulator:**
   - The app should automatically detect platform
   - Web: `http://localhost:5000`
   - Android emulator: `http://10.0.2.2:5000`

3. **Or run on actual Android device:**
```bash
flutter devices
flutter run -d <device_id>
```

---

### ❌ Hot reload not working

**Solution:**

1. **Press 'r' in terminal to hot-reload:**
```bash
# In the Flutter terminal:
# Press 'r' to hot reload
# Press 'R' for full rebuild
# Press 'q' to quit
```

2. **If 'r' doesn't work:**
```bash
# Stop and restart:
# Press Ctrl+C

flutter run -d chrome
```

---

## Network/Connectivity

### ❌ API timeout errors

**Error:**
```
TimeoutException: Request failed after 30 seconds
or
SocketException: Connection reset
```

**Solution:**

1. **Check backend is responding:**
```bash
curl -X GET http://localhost:5000/
```

2. **Check network connectivity:**
```bash
# Verify localhost resolution:
ping localhost
# Should return 127.0.0.1

ping 10.0.2.2
# Should work from Android emulator
```

3. **Increase timeout in app** (if API calls are genuinely slow):
   - Find API configuration in `api_layer.dart`
   - Increase timeout value

---

## Performance Issues

### ❌ Backend is slow

**Solution:**

1. **Check if running in debug mode:**
```bash
# In terminal, if you see "WARNING in app running in development mode"
# This is normal for development
```

2. **Check CPU/Memory:**
```bash
# Windows Task Manager:
# Monitor Python process CPU/Memory usage
```

3. **Check database queries:**
   - Enable query logging in backend
   - Look for N+1 query problems

---

### ❌ Frontend is slow on web

**Solution:**

1. **Build release version:**
```bash
flutter run -d chrome --release
```

2. **Clear browser cache:**
   - F12 → Application → Clear All

3. **Check for console errors:**
   - F12 → Console tab
   - Look for JavaScript errors or warnings

---

## Getting Help

### Collect debug information:

```bash
# Python version
python --version

# Flutter version
flutter --version

# Docker status
docker ps
docker compose ps

# Backend error logs
# (from backend terminal)

# Frontend error logs
# (from Flutter terminal, also in browser F12 console)

# Database connection test
# cd backend
# python -c "from app import create_app; print(create_app().config)"
```

### Resources:

- [Flutter Docs](https://flutter.dev/docs)
- [Flask Docs](https://flask.palletsprojects.com/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Docker Docs](https://docs.docker.com/)

---

## Quick Fix Checklist

- [ ] Backend terminal shows no errors
- [ ] Frontend terminal shows no errors
- [ ] Browser console (F12) shows no CORS errors
- [ ] Docker container is running: `docker ps`
- [ ] Port 5000 is not in use: `netstat -ano | findstr :5000`
- [ ] .env file exists in backend/
- [ ] Python virtual environment is activated: `(venv)` in prompt
- [ ] Can curl backend: `curl http://localhost:5000/`
- [ ] Can access frontend: `http://localhost:8080`
- [ ] Can login with: `0000000000` / `admin123`

If all checks pass and you still have issues, start fresh:

```bash
# Full reset (removes all data):
cd e:\FlutterProject\backend
docker compose down -v
docker compose up -d

# In backend terminal:
python app.py

# In frontend terminal:
cd e:\FlutterProject\asha_app
flutter run -d chrome --web-port=8080
```
