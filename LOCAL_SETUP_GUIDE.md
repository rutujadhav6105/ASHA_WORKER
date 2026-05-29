# ASHA App - Local Development Setup Guide

This guide will help you run the entire project locally with frontend, backend, and database.

## Prerequisites

Install these tools first:
- **Python 3.11 or 3.12** - https://www.python.org/downloads/
- **Flutter SDK** - https://flutter.dev/docs/get-started/install
- **PostgreSQL 14+** OR **Docker** - https://www.postgresql.org/download/ OR https://www.docker.com/products/docker-desktop
- **Git** (optional)

---

## Option A: Using Docker for Database (Recommended - Easiest)

### 1. Start PostgreSQL Database with Docker

```bash
cd e:\FlutterProject\backend

# Start PostgreSQL container in the background
docker compose up -d

# Verify the database is running
docker compose ps
```

The database will be available at: `localhost:5432`

### 2. Configure Backend Environment Variables

```bash
# In the backend directory
cd e:\FlutterProject\backend

# Create .env file (copy from example if exists, or create new)
# Edit .env with these values:
```

Create file `e:\FlutterProject\backend\.env` with:
```ini
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True

DB_NAME=asha_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

JWT_SECRET_KEY=jwt-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=3600

CORS_ORIGINS=http://localhost,http://localhost:3000,http://localhost:8080,http://10.0.2.2

PORT=5000
```

### 3. Install Backend Dependencies

```bash
cd e:\FlutterProject\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Start Backend Server

```bash
cd e:\FlutterProject\backend

# Make sure venv is activated
python app.py
```

You should see:
```
✅ Database tables verified / created.
✅ Default admin seeded (mobile=0000000000, password=admin123)
Running on http://0.0.0.0:5000/
```

---

## Option B: Using Local PostgreSQL Installation

### 1. Create Database

```bash
# Open PostgreSQL command prompt or use psql
psql -U postgres

# Inside psql:
CREATE DATABASE asha_db;
CREATE USER asha_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE asha_db TO asha_user;
\q
```

### 2. Configure Backend .env

Create `e:\FlutterProject\backend\.env`:
```ini
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True

DB_NAME=asha_db
DB_USER=asha_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

JWT_SECRET_KEY=jwt-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=3600

CORS_ORIGINS=http://localhost,http://localhost:3000,http://localhost:8080,http://10.0.2.2

PORT=5000
```

### 3. Install & Run Backend (same as Option A steps 3-4)

---

## 5. Start Frontend (Flutter Web)

Open a new terminal:

```bash
cd e:\FlutterProject\asha_app

# Get dependencies
flutter pub get

# Run on web (localhost)
flutter run -d chrome --web-port=8080
```

Or run on Android emulator:
```bash
flutter run
```

---

## 6. Access the Application

| Component | URL | Credentials |
|-----------|-----|-------------|
| **Backend API** | http://localhost:5000 | - |
| **Frontend (Web)** | http://localhost:8080 | mobile: 0000000000, password: admin123 |
| **Database (pgAdmin)** | Optional: http://localhost:5050 | - |
| **Android Emulator** | `http://10.0.2.2:5000` | Same login |

---

## Troubleshooting

### Backend won't start

**Error: "ModuleNotFoundError: No module named 'flask'"**
```bash
# Make sure venv is activated, then reinstall:
pip install -r requirements.txt
```

**Error: "database connection refused"**
- Verify PostgreSQL/Docker is running: `docker compose ps`
- Check `.env` file has correct DB credentials
- For Docker: Run `docker compose up -d` again

### Frontend won't compile

```bash
# Clear cache and reinstall
flutter clean
flutter pub get
flutter run -d chrome
```

### Port already in use

If port 5000 or 8080 is already in use:
```bash
# For Backend (change port in .env and app.py)
# For Frontend:
flutter run -d chrome --web-port=9090
```

---

## Stopping the Application

### Stop Backend
Press `Ctrl+C` in the terminal running Flask

### Stop Frontend
Press `Ctrl+C` in the Flutter terminal

### Stop Database (Docker)
```bash
cd backend
docker compose down
```

---

## Next Steps

1. Access the API documentation: `http://localhost:5000/`
2. Check backend logs for any errors
3. Use Flutter DevTools for debugging frontend: `flutter pub global activate devtools && devtools`

For detailed info, see:
- Backend: [e:\FlutterProject\backend\README.md](backend/README.md)
- Backend Setup: [e:\FlutterProject\backend\SETUP.md](backend/SETUP.md)
- Frontend: [e:\FlutterProject\asha_app\README.md](asha_app/README.md)
