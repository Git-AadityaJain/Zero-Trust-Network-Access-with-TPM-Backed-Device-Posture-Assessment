@echo off
REM ZTNA Platform Setup Script for Windows

echo 🔒 ZTNA Platform Setup
echo ======================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop.
    exit /b 1
)

echo ✅ Docker is running

REM Create necessary directories
echo 📁 Creating directories...
if not exist "infra\nginx\conf.d" mkdir infra\nginx\conf.d
if not exist "infra\nginx\ssl" mkdir infra\nginx\ssl

REM Copy realm export if it doesn't exist in infra
if not exist "infra\realm-export.json" (
    if exist "realm-export.json" (
        echo 📋 Copying Keycloak realm export...
        copy realm-export.json infra\realm-export.json
    )
)

REM Check if backend .env exists
if not exist "backend\.env" (
    echo ⚙️  Creating backend .env file...
    if exist "backend\.env.example" (
        copy backend\.env.example backend\.env
        echo ✅ Created backend\.env from .env.example
    ) else (
        echo ⚠️  backend\.env.example not found. Please create backend\.env manually.
    )
) else (
    echo ✅ backend\.env already exists
)

REM Start services
echo.
echo 🚀 Starting services...
cd infra
docker-compose up -d

echo.
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check service status
echo.
echo 📊 Service Status:
docker-compose ps

echo.
echo ✅ Setup complete!
echo.
echo 📝 Next steps:
echo 1. Wait 30-60 seconds for Keycloak to fully start
echo 2. Run database migrations: make migrate
echo 3. Access the application:
echo    - Frontend: http://localhost:3000
echo    - Backend API: http://localhost:8000/docs
echo    - Keycloak: http://localhost:8080
echo.
echo 📖 See QUICKSTART.md for detailed instructions

