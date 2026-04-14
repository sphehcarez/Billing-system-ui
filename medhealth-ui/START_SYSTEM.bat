@echo off
REM Med Directory Billing System - Startup Script for Windows

echo ============================================================================
echo Med Directory Billing System - FULL SYSTEM STARTUP
echo ============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/4] Installing backend dependencies...
cd /d "%~dp0backend"
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Starting backend API server on port 8001...
echo.
start "Backend - FastAPI Server" python main.py

REM Wait for backend to start
echo.
echo [3/4] Waiting for backend to initialize...
timeout /t 3 /nobreak

echo.
echo [4/4] Backend API is starting up at http://localhost:8001
echo.
echo ============================================================================
echo SETUP COMPLETE
echo ============================================================================
echo.
echo Frontend:   http://localhost:8000
echo Backend API: http://localhost:8001
echo API Docs:   http://localhost:8001/docs
echo API Info:   http://localhost:8001/api/docs
echo.
echo Demo Credentials:
echo   - username: demo.user or admin
echo   - password: password123 or admin123
echo.
echo The frontend (port 8000) should already be running in another terminal.
echo If not, open another terminal and run:
echo   python -m http.server 8000
echo.
echo Press any key to view the system...
pause

start http://localhost:8000

echo.
echo System is ready! You can now:
echo 1. Login with demo credentials
echo 2. Create/view patients, providers, claims
echo 3. Run readiness checks and close claims
echo 4. Generate reports
echo.
echo Keep both terminal windows open while using the system.
echo Close this script to stop the servers.
