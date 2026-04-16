#!/bin/bash
###############################################################################
# WSL System Startup Script for Medhealth Claims Platform
#
# This script starts both backend (FastAPI) and frontend (http.server)
# in the WSL environment.
#
# Usage: bash wsl_start_system.sh
# Or:    medhealth-start (if alias configured)
###############################################################################

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/.venv"

echo "============================================================================"
echo "Medhealth Claims Platform - WSL System Startup"
echo "============================================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ ERROR: Virtual environment not found at $VENV_PATH"
    echo ""
    echo "Please run setup first:"
    echo "  bash $PROJECT_ROOT/wsl_setup.sh"
    exit 1
fi

echo "✓ Project root: $PROJECT_ROOT"
echo "✓ Virtual environment: $VENV_PATH"
echo ""

# Activate virtual environment
echo "[1/4] Activating virtual environment..."
source "$VENV_PATH/bin/activate"
echo "✓ Virtual environment activated"
echo ""

# Check Python
echo "[2/4] Verifying Python..."
python --version
echo ""

# Start backend in background
echo "[3/4] Starting Backend API Server (FastAPI on port 8001)..."
cd "$SCRIPT_DIR/backend"
python main.py &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID)"
echo ""

# Wait for backend to initialize
echo "[4/4] Waiting for backend to initialize (3 seconds)..."
sleep 3
echo ""

# Start frontend in background
echo "Starting Frontend Server (http.server on port 8000)..."
cd "$SCRIPT_DIR"
python -m http.server 8000 &
FRONTEND_PID=$!
echo "✓ Frontend started (PID: $FRONTEND_PID)"
echo ""

echo "============================================================================"
echo "✅ Medhealth Claims Platform is Running!"
echo "============================================================================"
echo ""
echo "Access Points:"
echo "  - Frontend:        http://localhost:8000"
echo "  - Backend API:     http://localhost:8001"
echo "  - API Docs:        http://localhost:8001/docs"
echo "  - API Info:        http://localhost:8001/api/docs"
echo ""
echo "Demo Credentials:"
echo "  - Username: admin"
echo "  - Password: admin123"
echo ""
echo "Process IDs:"
echo "  - Backend:  $BACKEND_PID"
echo "  - Frontend: $FRONTEND_PID"
echo ""
echo "To stop the system, press Ctrl+C"
echo "============================================================================"
echo ""

# Wait for both processes
wait

echo ""
echo "System shutdown."
