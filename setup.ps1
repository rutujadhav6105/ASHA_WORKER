# ASHA App - Quick Start Script (Windows PowerShell)
# Run this script to set up and start the entire project

param(
    [switch]$UseLocalPostgres = $false
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "ASHA App - Local Development Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Colors
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"

function Write-Success {
    param($Message)
    Write-Host "✅ $Message" -ForegroundColor $SuccessColor
}

function Write-Error-Custom {
    param($Message)
    Write-Host "❌ $Message" -ForegroundColor $ErrorColor
}

function Write-Info {
    param($Message)
    Write-Host "ℹ️  $Message" -ForegroundColor $InfoColor
}

# Check Prerequisites
Write-Info "Checking prerequisites..."

# Check Python
$pythonCheck = python --version 2>$null
if ($pythonCheck) {
    Write-Success "Python found: $pythonCheck"
} else {
    Write-Error-Custom "Python not found. Please install Python 3.11 or 3.12"
    exit 1
}

# Check Flutter
$flutterCheck = flutter --version 2>$null
if ($flutterCheck) {
    Write-Success "Flutter found"
} else {
    Write-Error-Custom "Flutter not found. Please install Flutter SDK"
    exit 1
}

# Check Docker
$dockerCheck = docker --version 2>$null
if ($dockerCheck -and -not $UseLocalPostgres) {
    Write-Success "Docker found: $dockerCheck"
} elseif ($UseLocalPostgres) {
    Write-Info "Using local PostgreSQL (Docker not required)"
}

# Setup Backend
Write-Host "`n=== Setting up Backend ===" -ForegroundColor Cyan

$backendDir = "e:\FlutterProject\backend"
$backendEnv = "$backendDir\.env"

if (Test-Path $backendEnv) {
    Write-Info ".env file already exists, skipping creation"
} else {
    Write-Info "Creating .env file..."
    $envContent = @"
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
"@
    Set-Content -Path $backendEnv -Value $envContent
    Write-Success ".env file created at $backendEnv"
}

# Create virtual environment
Write-Info "Setting up Python virtual environment..."
$venvDir = "$backendDir\venv"

if (Test-Path $venvDir) {
    Write-Info "Virtual environment already exists"
} else {
    Push-Location $backendDir
    python -m venv venv
    Write-Success "Virtual environment created"
    Pop-Location
}

# Install dependencies
Write-Info "Installing backend dependencies..."
Push-Location $backendDir
& ".\venv\Scripts\activate.ps1"
pip install -r requirements.txt --quiet
Write-Success "Backend dependencies installed"
Pop-Location

# Start Database
Write-Host "`n=== Starting Database ===" -ForegroundColor Cyan

if (-not $UseLocalPostgres) {
    Write-Info "Starting PostgreSQL with Docker..."
    Push-Location $backendDir
    docker compose up -d
    Write-Success "PostgreSQL started in Docker"
    Write-Info "Waiting for database to be ready..."
    Start-Sleep -Seconds 3
    Pop-Location
} else {
    Write-Info "Skipping Docker (using local PostgreSQL)"
}

# Start Backend
Write-Host "`n=== Starting Backend ===" -ForegroundColor Cyan
Write-Info "Backend will start in a new terminal..."
Write-Info "Press Ctrl+C to stop the backend server"

$backendScript = @"
cd $backendDir
`& ".\venv\Scripts\activate.ps1"
python app.py
"@

$backendScript | Out-File "$env:TEMP\start_backend.ps1" -Encoding UTF8
Start-Process powershell -ArgumentList "-NoExit -File `"$env:TEMP\start_backend.ps1`""

Write-Success "Backend starting in new window..."
Start-Sleep -Seconds 2

# Setup Frontend
Write-Host "`n=== Setting up Frontend ===" -ForegroundColor Cyan

$frontendDir = "e:\FlutterProject\asha_app"

Write-Info "Getting Flutter dependencies..."
Push-Location $frontendDir
flutter pub get
Write-Success "Frontend dependencies installed"

Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "`nTo start the frontend, open a new terminal and run:" -ForegroundColor Cyan
Write-Host "  cd $frontendDir" -ForegroundColor White
Write-Host "  flutter run -d chrome --web-port=8080" -ForegroundColor White

Write-Host "`n📱 Access Points:" -ForegroundColor Cyan
Write-Host "  Backend API: http://localhost:5000" -ForegroundColor White
Write-Host "  Frontend Web: http://localhost:8080" -ForegroundColor White
Write-Host "  Default Login: mobile=0000000000, password=admin123" -ForegroundColor White

Pop-Location
