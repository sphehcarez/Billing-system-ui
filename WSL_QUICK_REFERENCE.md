# WSL Quick Reference - Medhealth Claims Platform

## One-Time Setup

```bash
# 1. Open in WSL (from Windows VS Code)
Ctrl+Shift+P → "WSL: Open Folder in WSL" → Select Ubuntu

# 2. Run setup (in WSL terminal)
bash wsl_setup.sh

# Done! ✅
```

---

## Daily Development Workflow

### Terminal 1 - Backend
```bash
cd medhealth-ui/backend
python main.py
# Runs on http://localhost:8001
```

### Terminal 2 - Frontend
```bash
cd medhealth-ui
python -m http.server 8000
# Runs on http://localhost:8000
```

### Or Use Convenience Aliases (after setup)
```bash
medhealth-start       # Starts both automatically
medhealth-backend     # Backend only
medhealth-frontend    # Frontend only
medhealth-test        # Run tests
medhealth-status      # Show URLs
```

---

## Access the App

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8000 |
| Backend API | http://localhost:8001 |
| API Documentation | http://localhost:8001/docs |

**Login:** `admin` / `admin123`

---

## Common Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install new Python package
pip install <package>

# Run backend tests
cd medhealth-ui/backend && python -m unittest discover -s tests -v

# Check what's running
lsof -i :8000  # Frontend
lsof -i :8001  # Backend

# Stop a service (if backgrounded)
kill -9 <PID>

# Restart WSL (from Windows PowerShell)
wsl --shutdown
# Then reopen the folder in WSL
```

---

## Useful VS Code Extensions in WSL

- **Remote - WSL** (required)
- **Python** - IntelliSense, linting, debugging
- **REST Client** - Test API endpoints
- **Thunder Client** or **Postman** - API testing
- **SQLite** - View database (when added)

Install in WSL: `Ctrl+Shift+X` → Install → WSL prompt

---

## File Paths

- **Windows:** `C:\pe\MEDHEALTH FINAL\Billing system ui\`
- **WSL:** `/mnt/c/pe/MEDHEALTH\ FINAL/Billing\ system\ ui/`
- **Home dir:** `~` or `/home/<username>`

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Port already in use" | `lsof -ti :8000 \| xargs kill -9` |
| "Permission denied" script | `chmod +x *.sh` |
| Slow performance | Use WSL 2, store in `~` not `/mnt/c/` |
| Python not found | Use `python3` or update `PATH` |
| Can't connect to localhost | Ensure WSL 2 is installed: `wsl -l -v` |
| vs Code disconnects | `Ctrl+Shift+P` → "WSL: Connect to WSL" |

---

## Key Files

- **Setup script:** `wsl_setup.sh`
- **Startup script:** `medhealth-ui/wsl_start_system.sh`
- **Documentation:** `WSL_SETUP.md` (this file)
- **Backend:** `medhealth-ui/backend/main.py`
- **Frontend:** `medhealth-ui/index.html`
- **Dependencies:** `medhealth-ui/backend/requirements.txt`

---

## Next: Develop Inside WSL

1. All terminals in VS Code are now WSL shells
2. Clone repos, install tools, run commands natively
3. Files sync automatically with Windows
4. Enjoy native Linux development! 🐧

Happy coding!
