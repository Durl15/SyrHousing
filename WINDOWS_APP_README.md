# SyrHousing Windows Manager

A graphical Windows application to manage the SyrHousing backend server and automated grant discovery system.

## Features

✅ **Server Management**
- Start/Stop/Restart backend server with one click
- Real-time server status monitoring
- Live server logs display
- Auto-start on application launch

✅ **Discovery System Control**
- Trigger manual discovery runs
- View discovery statistics
- Monitor scheduled discovery status
- Real-time discovery logs

✅ **Quick Access**
- Open API documentation in browser
- Open frontend application
- Open project folder
- Quick status overview

## Installation & Setup

### Option 1: Automated Setup (Recommended)

1. **Run the setup script:**
   ```powershell
   Right-click on Setup_SyrHousing.ps1 → Run with PowerShell
   ```

2. **Follow the prompts:**
   - Setup will check Python installation
   - Install missing dependencies
   - Create desktop shortcut
   - Optionally enable auto-start on Windows boot

3. **Launch the app:**
   - Double-click the desktop shortcut "SyrHousing Manager"
   - Or run: `python syrhousing_manager.py`

### Option 2: Manual Setup

1. **Install dependencies:**
   ```bash
   pip install requests
   ```

2. **Run the manager:**
   ```bash
   python syrhousing_manager.py
   ```

3. **Create shortcut manually:**
   - Right-click on `syrhousing_manager.py`
   - Send to → Desktop (create shortcut)

## Usage

### Starting the Server

1. Launch **SyrHousing Manager**
2. Click **"▶ Start Backend"**
3. Wait for green status indicator
4. Server runs on: http://localhost:8000

The backend will auto-start if the checkbox is enabled (default).

### Running Discovery

**Manual Discovery:**
1. Click **"🔍 Run Discovery Now"**
2. Watch progress in logs
3. Get notification when complete

**Automatic Discovery:**
- Runs daily at 2 AM automatically
- No action needed!

### Viewing Statistics

1. Click **"📊 View Statistics"**
2. See discovery runs, grants found, duplicates
3. View active programs count

### Quick Access Links

- **🌐 Open API Docs** - Interactive API documentation
- **💻 Open Frontend** - React frontend application (if running)
- **📁 Open Project Folder** - File explorer to project directory

## Auto-Start on Windows Boot

### Enable Auto-Start

**During Setup:**
- Run `Setup_SyrHousing.ps1` and answer "Y" to auto-start

**Manually:**
1. Press `Win+R`
2. Type: `shell:startup`
3. Create shortcut to `syrhousing_manager.py` in that folder

### Disable Auto-Start

1. Press `Win+R`
2. Type: `shell:startup`
3. Delete "SyrHousing Manager" shortcut

## Advanced: Windows Service Setup

To run as a Windows Service (always running in background):

### Option 1: Using NSSM (Recommended)

1. **Download NSSM** (Non-Sucking Service Manager):
   - https://nssm.cc/download
   - Extract to `C:\SyrHousing\nssm`

2. **Install service:**
   ```cmd
   cd C:\SyrHousing\nssm
   nssm install SyrHousing
   ```

3. **Configure in NSSM GUI:**
   - Path: `C:\Python312\python.exe` (your Python path)
   - Startup directory: `C:\SyrHousing`
   - Arguments: `-m uvicorn backend.main:app --host 0.0.0.0 --port 8000`
   - Service name: `SyrHousing`

4. **Start service:**
   ```cmd
   nssm start SyrHousing
   ```

### Option 2: Windows Task Scheduler

1. Open **Task Scheduler**
2. Create Basic Task:
   - Name: `SyrHousing Backend`
   - Trigger: **At startup**
   - Action: **Start a program**
   - Program: `python`
   - Arguments: `-m uvicorn backend.main:app --port 8000`
   - Start in: `C:\SyrHousing`
3. Check "Run whether user is logged on or not"
4. Check "Run with highest privileges"

## Troubleshooting

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
1. Stop any running backend instances
2. Or change port in manager code (line 32)
3. Or kill process using port:
   ```cmd
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

### Python Not Found

**Error:** `'python' is not recognized`

**Solution:**
1. Install Python 3.10+ from python.org
2. During install, check "Add Python to PATH"
3. Restart computer
4. Verify: `python --version`

### Permission Denied

**Error:** Cannot start server

**Solution:**
- Run as Administrator (right-click → Run as administrator)
- Check firewall settings
- Ensure port 8000 is not blocked

### Backend Won't Stop

**Solution:**
1. Click "⏹ Stop Backend"
2. If hung, use Task Manager:
   - Find "python.exe" process
   - End task
3. Restart the manager

## Files

```
C:\SyrHousing\
├── syrhousing_manager.py       # Main GUI application
├── SyrHousing_Manager.bat      # Quick launcher
├── Setup_SyrHousing.ps1        # Automated setup script
├── WINDOWS_APP_README.md       # This file
└── backend/                    # Backend code
```

## Configuration

Edit `backend/.env` to configure:

```bash
# Discovery settings
DISCOVERY_ENABLED=true
DISCOVERY_SCHEDULE_CRON=0 2 * * *
DISCOVERY_SOURCES=rss_feed

# Server settings
DATABASE_URL=sqlite:///./syrhousing.db
DEBUG=false
```

## Support

For issues or questions:
1. Check logs in the manager window
2. Check `backend/discovery_runs.log`
3. Open an issue on GitHub

## Features Coming Soon

- 📱 System tray minimization
- 📧 Email notification configuration
- 🔔 Desktop notifications for discoveries
- 📊 Built-in discovery dashboard
- 🔐 Admin user management UI
- 🎨 Theme customization

---

**Enjoy automated grant discovery!** 🎉
