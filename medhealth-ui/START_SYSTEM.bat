@echo off
setlocal
REM Medhealth Claims Platform - Local startup script for Windows

echo ============================================================================
echo Medhealth Claims Platform - LOCAL STARTUP
echo ============================================================================
echo.

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%backend"
set "PYTHON_CMD=python"

REM Preferred interpreter: workspace virtual environment one level above medhealth-ui
if exist "%ROOT%..\.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%ROOT%..\.venv\Scripts\python.exe"
)

"%PYTHON_CMD%" --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not available.
    echo Expected either `python` on PATH or `.venv\Scripts\python.exe` one level above this folder.
    pause
    exit /b 1
)

echo [1/4] Verifying core backend dependencies...
"%PYTHON_CMD%" -c "import fastapi, uvicorn, jose, pydantic" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Core backend dependencies are missing for the selected Python interpreter.
    echo Install FastAPI, Uvicorn, python-jose and Pydantic, then rerun this script.
    pause
    exit /b 1
)

echo [2/4] Starting backend API on http://localhost:8001 ...
start "Medhealth Backend" cmd /k "cd /d \"%BACKEND_DIR%\" && \"%PYTHON_CMD%\" main.py"

echo [3/4] Starting frontend on http://localhost:8000 ...
start "Medhealth Frontend" cmd /k "cd /d \"%ROOT%\" && \"%PYTHON_CMD%\" -m http.server 8000"

echo [4/4] Waiting for services to initialize...
timeout /t 3 /nobreak >nul

echo.
echo ============================================================================
echo SERVICES
echo ============================================================================
echo Frontend:    http://localhost:8000
echo Backend API: http://localhost:8001
echo Health:      http://localhost:8001/health
echo API Docs:    http://localhost:8001/docs
echo.
echo Runtime notes:
echo - Local-only runtime overrides can be placed in `backend\.env.local`.
echo - Example: `MEDHEALTH_STORE_MODE=inmemory` for localhost UI testing.
echo.
echo Demo credentials:
echo - admin / admin123
echo - demo.user / password123
echo - billing / billing123
echo - provider / provider123
echo - finance / finance123
echo - auditor / auditor123
echo.

start http://localhost:8000
