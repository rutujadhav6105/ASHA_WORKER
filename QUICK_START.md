# ASHA App - Quick Reference

## 🚀 Fast Start (Choose One)

### Option 1: Automated Setup (Recommended)

**Windows PowerShell:**
```powershell
cd e:\FlutterProject
.\setup.ps1
```

**Windows Command Prompt:**
```cmd
cd e:\FlutterProject
setup.bat
```

Then in a new terminal:
```bash
cd e:\FlutterProject\asha_app
flutter run -d chrome --web-port=8080
```

---

### Option 2: Manual Setup (Understanding Each Step)

#### Terminal 1 - Start Database & Backend

```bash
# Navigate to backend
cd e:\FlutterProject\backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL with Docker (if using Docker)
docker compose up -d

# Start Flask backend
python app.py
```

Wait for message: `Running on http://0.0.0.0:5000/`

#### Terminal 2 - Start Frontend

```bash
# Navigate to frontend
cd e:\FlutterProject\asha_app

# Get dependencies
flutter pub get

# Run on web
flutter run -d chrome --web-port=8080
```

---

## 📱 Access Points

| Service | URL | Notes |
|---------|-----|-------|
| **Backend API** | http://localhost:5000 | Flask backend |
| **Frontend (Web)** | http://localhost:8080 | Flutter web app |
| **Android Emulator** | http://10.0.2.2:5000 | Backend from emulator |
| **Database** | localhost:5432 | PostgreSQL |

---

## 🔑 Default Credentials

```
Mobile Number: 0000000000
Password: admin123
```

---

## 🛑 Stop Everything

```bash
# Stop Backend: Ctrl+C in backend terminal
# Stop Frontend: Ctrl+C in frontend terminal
# Stop Database: 
docker compose down
```

---

## ⚠️ Common Issues & Fixes

### Backend won't start - "ModuleNotFoundError"

```bash
# Ensure venv is activated (should see (venv) in prompt)
# Then reinstall:
pip install -r requirements.txt
```

### Backend can't connect to database

```bash
# Check Docker is running:
docker ps

# Check .env file has correct credentials:
# cat .env | grep DB_

# Restart database:
docker compose down
docker compose up -d
```

### Port 5000 already in use

```bash
# Find what's using port 5000:
netstat -ano | findstr :5000

# Either kill the process or change port in .env and backend code
```

### Frontend won't compile

```bash
flutter clean
flutter pub get
flutter run -d chrome
```

---

## 📂 Important Files

```
e:\FlutterProject\
├── backend\
│   ├── .env                    ← Configuration (auto-created)
│   ├── app.py                  ← Main Flask app
│   ├── requirements.txt        ← Python dependencies
│   └── docker-compose.yml      ← Database container
├── asha_app\
│   ├── pubspec.yaml            ← Flutter dependencies
│   ├── lib\main.dart           ← App entry point
│   └── ...
├── LOCAL_SETUP_GUIDE.md        ← Detailed guide
├── setup.ps1                   ← PowerShell setup script
└── setup.bat                   ← Batch file setup script
```

---

## 🔧 Environment Variables (.env)

The `.env` file in `backend/` contains:

```ini
FLASK_ENV=development        # Development mode
SECRET_KEY=...              # Flask secret (change in production)
DB_NAME=asha_db             # Database name
DB_USER=postgres            # Database user
DB_PASSWORD=postgres        # Database password
DB_HOST=localhost           # Database host
DB_PORT=5432                # Database port
JWT_SECRET_KEY=...          # JWT signing key
CORS_ORIGINS=...            # Allowed frontend origins
PORT=5000                   # Backend server port
```

---

## 📊 API Documentation

Once backend is running, visit: http://localhost:5000/

Check `backend/API_DOCS.md` for full API reference

---

## 🐛 Debugging

### View backend logs:
```bash
# Logs appear in the terminal where you ran: python app.py
```

### View frontend logs:
```bash
# Logs appear in the terminal where you ran: flutter run -d chrome
```

### Enable Chrome DevTools for Flutter Web:
```bash
# DevTools should open automatically, or visit:
# http://localhost:9223
```

### Check database directly:
```bash
# Install pgAdmin (optional):
docker run --name pgadmin \
  -e PGADMIN_DEFAULT_EMAIL=admin@admin.com \
  -e PGADMIN_DEFAULT_PASSWORD=admin \
  -p 5050:80 \
  -d dpage/pgadmin4

# Then visit: http://localhost:5050
# Login: admin@admin.com / admin
```

---

## 📖 Documentation

- [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md) - Detailed setup guide
- [backend/SETUP.md](backend/SETUP.md) - Backend configuration
- [backend/README.md](backend/README.md) - Backend documentation
- [backend/API_DOCS.md](backend/API_DOCS.md) - API endpoints
- [asha_app/README.md](asha_app/README.md) - Frontend documentation

---

## 🎯 Next Steps

1. **Setup the project** using one of the methods above
2. **Login** with default credentials
3. **Explore features** in the Flutter app
4. **Check API docs** at http://localhost:5000/
5. **Review code** in `backend/app/` and `asha_app/lib/`

Happy coding! 🚀
