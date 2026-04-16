# WSL Development Setup for Medhealth Claims Platform

## Prerequisites

### On Windows
1. **WSL 2 installed** and running a Linux distribution (Ubuntu 20.04+ recommended)
   ```powershell
   wsl --list --verbose
   wsl --install -d Ubuntu  # If not installed
   ```

2. **VS Code Remote - WSL extension** installed
   - Open VS Code → Extensions → Search "Remote - WSL" → Install

### Inside WSL
These will be auto-installed by the setup script:
- Python 3.8+
- pip / python-venv
- Node.js (optional, for future frontend dev)
- git

---

## Quick Start: Open in WSL

### Method 1: VS Code Command Palette (Easiest)
1. Open this folder in Windows VS Code (if not already open)
2. Press `Ctrl+Shift+P` → Type **"WSL: Open Folder in WSL"** → Select your distro
3. VS Code reconnects to run inside WSL
4. Open a new terminal (`Ctrl+` ` `) — it will be inside WSL

### Method 2: WSL Command Line
```powershell
# From Windows PowerShell in this folder
wsl code .
```

### Method 3: From WSL Terminal
```bash
cd /mnt/c/pe/MEDHEALTH\ FINAL/Billing\ system\ ui
code .
```

---

## Setup Steps Inside WSL

Once you've opened the folder in WSL via VS Code:

### Step 1: Run the WSL Setup Script
```bash
cd ~/workspaces/medhealth  # Or wherever WSL mounted the folder
bash wsl_setup.sh
```

This script will:
- Update package lists
- Install Python 3.10+, pip, venv, curl, git
- Create Python virtual environment at `.venv/`
- Install backend dependencies from `requirements.txt`
- Create alias shortcuts for common commands

### Step 2: Activate Virtual Environment
```bash
source .venv/bin/activate
```

### Step 3: Start the System

**Terminal 1 (Backend):**
```bash
cd medhealth-ui/backend
python main.py
```
Runs on: `http://localhost:8001`

**Terminal 2 (Frontend):**
```bash
cd medhealth-ui
python -m http.server 8000
```
Runs on: `http://localhost:8000`

### Step 4: Access the Application
- **Frontend:** `http://localhost:8000`
- **API Docs:** `http://localhost:8001/docs`
- **Demo Login:** `admin` / `admin123`

---

## Convenience Commands

After running `wsl_setup.sh`, these aliases are available:

```bash
# Start full system (both backend & frontend)
medhealth-start

# Start only backend
medhealth-backend

# Start only frontend
medhealth-frontend

# Run backend tests
medhealth-test

# Check system status
medhealth-status

# Activate venv
medhealth-venv
```

Add the following to `~/.bashrc` or `~/.zshrc` manually if aliases don't work:
```bash
source /path/to/medhealth/.venv/bin/activate
alias medhealth-venv="source .venv/bin/activate"
alias medhealth-start="cd medhealth-ui && bash wsl_start_system.sh"
alias medhealth-backend="cd medhealth-ui/backend && python main.py"
alias medhealth-frontend="cd medhealth-ui && python -m http.server 8000"
alias medhealth-test="cd medhealth-ui/backend && python -m unittest discover -s tests -v"
```

---

## File Structure in WSL

```
/mnt/c/pe/MEDHEALTH FINAL/Billing system ui/
├── medhealth-ui/
│   ├── backend/
│   │   ├── main.py
│   │   ├── platform_core.py
│   │   ├── platform_api.py
│   │   ├── requirements.txt
│   │   └── tests/
│   ├── js/
│   ├── css/
│   ├── *.html
│   └── wsl_start_system.sh  (new)
├── .venv/  (created by setup)
├── wsl_setup.sh  (new)
└── WSL_SETUP.md  (this file)
```

---

## Port Access from Windows

When running servers inside WSL, they're accessible from Windows via `localhost`:
- Backend: `http://localhost:8001`
- Frontend: `http://localhost:8000`

**No extra configuration needed** for WSL 2!

---

## Troubleshooting

### "Permission Denied" on Script
```bash
chmod +x wsl_setup.sh
chmod +x medhealth-ui/wsl_start_system.sh
bash wsl_setup.sh
```

### Python Not Found
```bash
python3 --version  # Use python3 instead of python
# Or update PATH in WSL ~/.bashrc
```

### Port 8000/8001 Already in Use
```bash
# Kill process on port 8001
lsof -ti :8001 | xargs kill -9
# Kill process on port 8000
lsof -ti :8000 | xargs kill -9
```

### Slow Performance
- Use WSL 2 (not WSL 1)
- Store project inside WSL filesystem (`~/projects/`) rather than `/mnt/c/`
- Use `--bind=127.0.0.1` when starting servers

### VS Code Remote Connection Lost
- Reconnect: `Ctrl+Shift+P` → "WSL: Connect to WSL"
- Restart WSL: `wsl --shutdown` (from Windows PowerShell), then reopen

---

## Best Practices

1. **Use Virtual Environment**: Always activate `.venv/` before working
   ```bash
   source .venv/bin/activate
   ```

2. **Keep Servers Running**: Use `tmux` or `screen` for persistent sessions
   ```bash
   tmux new-session -d -s backend "python medhealth-ui/backend/main.py"
   tmux new-session -d -s frontend "cd medhealth-ui && python -m http.server 8000"
   ```

3. **Store Large Files Outside `/mnt/c/`**: Access `/mnt/c/` is slower; copy project to `~` if needed

4. **Sync Back to Windows**: After WSL changes, sync back to Windows workspace
   ```bash
   cp -r ~/medhealth-updated /mnt/c/pe/MEDHEALTH\ FINAL/Billing\ system\ ui/
   ```

5. **Use VS Code Terminal**: The integrated VS Code terminal in WSL mode runs commands directly in the distro

---

## Next Steps

- [ ] Install WSL 2 (if needed)
- [ ] Install VS Code Remote - WSL extension
- [ ] Open folder in WSL via `Ctrl+Shift+P`
- [ ] Run `bash wsl_setup.sh`
- [ ] Start servers and verify at `http://localhost:8000`
- [ ] Login with `admin` / `admin123`

Happy coding! 🚀
