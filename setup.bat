@echo off
REM ASHA App - Quick Start Batch Script for Windows Command Prompt

setlocal enabledelayedexpansion

echo.
echo ================================
echo ASHA App - Local Development Setup
echo ================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.11 or 3.12
    pause
    exit /b 1
)
echo ✅ Python found

REM Check Flutter
flutter --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Flutter not found. Please install Flutter SDK
    pause
    exit /b 1
)
echo ✅ Flutter found

REM Setup Backend
echo.
echo === Setting up Backend ===
cd /d e:\FlutterProject\backend

REM Create .env if it doesn't exist
if not exist .env (
    echo ℹ️ Creating .env file...
    (
        echo FLASK_ENV=development
        echo SECRET_KEY=dev-secret-key-change-in-production
        echo DEBUG=True
        echo.
        echo DB_NAME=asha_db
        echo DB_USER=postgres
        echo DB_PASSWORD=postgres
        echo DB_HOST=localhost
        echo DB_PORT=5432
        echo.
        echo JWT_SECRET_KEY=jwt-secret-key-change-in-production
        echo JWT_ACCESS_TOKEN_EXPIRES=3600
        echo.
        echo CORS_ORIGINS=http://localhost,http://localhost:3000,http://localhost:8080,http://10.0.2.2
        echo.
        echo PORT=5000
    ) > .env
    echo ✅ .env file created
) else (
    echo ℹ️ .env file already exists
)

REM Create virtual environment
if not exist venv (
    echo ℹ️ Creating Python virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ℹ️ Virtual environment already exists
)

REM Install dependencies
echo ℹ️ Installing backend dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
echo ✅ Backend dependencies installed

REM Start Database with Docker
echo.
echo === Starting Database ===
docker --version >nul 2>&1
if not errorlevel 1 (
    echo ℹ️ Starting PostgreSQL with Docker...
    docker compose up -d
    echo ✅ PostgreSQL started
    timeout /t 3 /nobreak
) else (
    echo ⚠️  Docker not found. Please start PostgreSQL manually or install Docker Desktop
)

REM Start Backend
echo.
echo === Starting Backend ===
echo ℹ️ Backend will start in a new window...
echo.
start "ASHA Backend" python app.py
timeout /t 2 /nobreak

REM Setup Frontend
echo.
echo === Setting up Frontend ===
cd /d e:\FlutterProject\asha_app
echo ℹ️ Getting Flutter dependencies...
flutter pub get >nul 2>&1
echo ✅ Frontend dependencies installed

echo.
echo ✅ Setup complete!
echo.
echo To start the frontend, open a new Command Prompt and run:
echo   cd e:\FlutterProject\asha_app
echo   flutter run -d chrome --web-port=8080
echo.
echo 📱 Access Points:
echo   Backend API: http://localhost:5000
echo   Frontend Web: http://localhost:8080
echo   Default Login: mobile=0000000000, password=admin123
echo.
pause
