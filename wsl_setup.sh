#!/bin/bash
###############################################################################
# WSL Setup Script for Medhealth Claims Platform
# 
# This script initializes a WSL development environment with:
# - Python 3.10+
# - Virtual environment (.venv/)
# - Backend dependencies
# - Convenience aliases
#
# Usage: bash wsl_setup.sh
###############################################################################

set -e  # Exit on error

echo "============================================================================"
echo "Medhealth Claims Platform - WSL Development Setup"
echo "============================================================================"
echo ""

# Detect distro
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    DISTRO="unknown"
fi

echo "[1/6] Updating package manager..."
case $DISTRO in
    ubuntu|debian)
        sudo apt-get update -qq
        sudo apt-get upgrade -y
        ;;
    fedora)
        sudo dnf update -y
        ;;
    arch)
        sudo pacman -Syu --noconfirm
        ;;
    *)
        echo "⚠ Unknown distro: $DISTRO. Skipping package manager update."
        ;;
esac

echo "[2/6] Installing system dependencies (Python, pip, venv, curl, git)..."
case $DISTRO in
    ubuntu|debian)
        sudo apt-get install -y \
            python3.10 python3-pip python3-venv \
            curl git build-essential \
            2>/dev/null || true
        ;;
    fedora)
        sudo dnf install -y \
            python3.10 python3-pip \
            curl git gcc \
            2>/dev/null || true
        ;;
    arch)
        sudo pacman -S --noconfirm python python-pip \
            curl git base-devel \
            2>/dev/null || true
        ;;
esac

echo "[3/6] Verifying Python installation..."
python3 --version
pip3 --version

echo ""
echo "[4/6] Creating Python virtual environment at .venv/..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo "[5/6] Installing backend dependencies from requirements.txt..."
source .venv/bin/activate
pip install --upgrade pip
if [ -f "medhealth-ui/backend/requirements.txt" ]; then
    pip install -r medhealth-ui/backend/requirements.txt
    echo "✓ Backend dependencies installed"
else
    echo "⚠ requirements.txt not found at medhealth-ui/backend/requirements.txt"
fi

echo ""
echo "[6/6] Setting up convenience aliases in ~/.bashrc..."
BASHRC="$HOME/.bashrc"

# Create aliases string
ALIASES="
# Medhealth Development Aliases
alias medhealth-venv='source $(pwd)/.venv/bin/activate'
alias medhealth-start='cd $(pwd)/medhealth-ui && bash wsl_start_system.sh'
alias medhealth-backend='cd $(pwd)/medhealth-ui/backend && python main.py'
alias medhealth-frontend='cd $(pwd)/medhealth-ui && python -m http.server 8000'
alias medhealth-test='cd $(pwd)/medhealth-ui/backend && python -m unittest discover -s tests -v'
alias medhealth-status='echo \"Frontend: http://localhost:8000\" && echo \"Backend: http://localhost:8001\" && echo \"API Docs: http://localhost:8001/docs\"'
"

# Add aliases if not already present
if ! grep -q "medhealth-venv" "$BASHRC"; then
    echo "" >> "$BASHRC"
    echo "# --- Medhealth Development Aliases (added by wsl_setup.sh) ---" >> "$BASHRC"
    echo "$ALIASES" >> "$BASHRC"
    echo "✓ Aliases added to ~/.bashrc"
else
    echo "✓ Aliases already present in ~/.bashrc"
fi

# For zsh users
if [ -f "$HOME/.zshrc" ]; then
    if ! grep -q "medhealth-venv" "$HOME/.zshrc"; then
        echo "" >> "$HOME/.zshrc"
        echo "# --- Medhealth Development Aliases (added by wsl_setup.sh) ---" >> "$HOME/.zshrc"
        echo "$ALIASES" >> "$HOME/.zshrc"
        echo "✓ Aliases added to ~/.zshrc"
    fi
fi

echo ""
echo "============================================================================"
echo "✅ WSL Setup Complete!"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Start the system:"
echo "     bash medhealth-ui/wsl_start_system.sh"
echo ""
echo "  3. Or use convenience aliases (after reloading shell):"
echo "     medhealth-start       # Start both backend & frontend"
echo "     medhealth-backend     # Start only backend"
echo "     medhealth-frontend    # Start only frontend"
echo "     medhealth-test        # Run backend tests"
echo "     medhealth-status      # Show service URLs"
echo ""
echo "Access URLs:"
echo "  - Frontend:   http://localhost:8000"
echo "  - Backend:    http://localhost:8001"
echo "  - API Docs:   http://localhost:8001/docs"
echo ""
echo "Demo Credentials:"
echo "  - Username: admin"
echo "  - Password: admin123"
echo ""
echo "============================================================================"
echo ""

