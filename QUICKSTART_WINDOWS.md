# 🚀 SyrHousing Windows Quick Start

Get SyrHousing up and running in 3 easy steps!

## Step 1: Install (One-Time Setup)

Double-click: **`Install_SyrHousing.bat`**

This will:
- ✓ Check Python installation
- ✓ Install all dependencies
- ✓ Initialize database
- ✓ Seed Syracuse grant data

**Time:** ~2-3 minutes

---

## Step 2: Setup Shortcuts (Optional)

Right-click **`Setup_SyrHousing.ps1`** → **Run with PowerShell**

This will:
- ✓ Create desktop shortcut
- ✓ Optionally enable auto-start on Windows boot
- ✓ Launch the manager

**Time:** ~30 seconds

---

## Step 3: Launch & Use

### Option A: Desktop Shortcut (Recommended)
Double-click **"SyrHousing Manager"** on your desktop

### Option B: Batch File
Double-click **`SyrHousing_Manager.bat`**

### Option C: Python Direct
```bash
python syrhousing_manager.py
```

---

## 🖥️ Using the Manager

### First Launch

1. **SyrHousing Manager window opens**
2. Backend auto-starts (if enabled)
3. Watch status indicators turn green
4. Backend is ready! 🎉

### Control Panel

**Server Status:**
- 🟢 Green = Running
- 🔴 Red = Error
- ⚪ Gray = Stopped

**Buttons:**
- **▶ Start Backend** - Start the server
- **⏹ Stop Backend** - Stop the server
- **🔄 Restart** - Restart server
- **🔍 Run Discovery Now** - Manual discovery
- **📊 View Statistics** - See discovery stats

**Quick Access:**
- **🌐 Open API Docs** → http://localhost:8000/docs
- **💻 Open Frontend** → http://localhost:5173
- **📁 Open Project Folder** → File explorer

---

## 📋 Common Tasks

### Start the Backend
1. Open SyrHousing Manager
2. Click **"▶ Start Backend"**
3. Wait for green status (5-10 seconds)
4. Done! Server running on port 8000

### Run Discovery Manually
1. Make sure backend is running (green)
2. Click **"🔍 Run Discovery Now"**
3. Watch logs in the window
4. Get popup notification when done

### View Discovery Stats
1. Click **"📊 View Statistics"**
2. See:
   - Total discovery runs
   - Grants discovered
   - Active programs
   - Pending reviews

### Check Logs
- Logs display automatically in the main window
- Real-time server output
- Discovery progress updates
- Error messages (if any)

---

## 🔧 Configuration

### Backend Settings
Edit **`backend\.env`**:

```bash
# Discovery
DISCOVERY_ENABLED=true
DISCOVERY_SCHEDULE_CRON=0 2 * * *
DISCOVERY_SOURCES=rss_feed

# Email (optional)
SENDGRID_API_KEY=your_key_here
SENDER_EMAIL=noreply@syrhousing.com

# AI Features (optional)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here
```

### Manager Settings
In the Manager window:
- ☑ **Auto-start backend on launch** - Starts server automatically
- Change ports in code if needed (default: 8000)

---

## 🏁 Auto-Start on Windows Boot

### Enable Auto-Start

**Method 1: During Setup**
Run `Setup_SyrHousing.ps1` and answer "Y"

**Method 2: Manually**
1. Press `Win+R`
2. Type: `shell:startup`
3. Copy the desktop shortcut here

### Disable Auto-Start
1. Press `Win+R`
2. Type: `shell:startup`
3. Delete "SyrHousing Manager" shortcut

---

## 🐛 Troubleshooting

### "Python not found"
**Fix:**
1. Install Python from python.org
2. Check "Add Python to PATH"
3. Restart computer

### "Port already in use"
**Fix:**
```cmd
netstat -ano | findstr :8000
taskkill /PID <number> /F
```

### Backend won't start
**Fix:**
1. Check logs in manager window
2. Try clicking "🔄 Restart"
3. Close manager and reopen

### Discovery not running
**Fix:**
1. Make sure backend is running (green)
2. Check `DISCOVERY_ENABLED=true` in `.env`
3. View logs for errors

---

## 📊 What Happens Automatically

Once set up:

1. **On Windows Boot** (if auto-start enabled):
   - Manager launches
   - Backend starts automatically
   - Discovery scheduler activates

2. **Daily at 2 AM**:
   - Discovery runs automatically
   - Fetches new grants from sources
   - Extracts and normalizes data
   - Detects duplicates
   - Saves to database
   - (Optional) Emails admin notification

3. **No Manual Intervention Needed!** 🎉

---

## 🔗 Quick Links

Once backend is running:

- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health
- **Programs:** http://localhost:8000/api/programs
- **Frontend:** http://localhost:5173 (if running separately)

---

## 📁 File Structure

```
C:\SyrHousing\
│
├── syrhousing_manager.py       ← Main GUI application
├── SyrHousing_Manager.bat      ← Quick launcher
├── Install_SyrHousing.bat      ← One-time installer
├── Setup_SyrHousing.ps1        ← Creates shortcuts/auto-start
│
├── backend/                    ← Backend code
│   ├── main.py                 ← FastAPI application
│   ├── .env                    ← Configuration
│   └── services/discovery/     ← Discovery system
│
└── syrhousing.db               ← SQLite database
```

---

## 🎯 Next Steps

After setup:

1. ✅ **Test the System**
   - Start backend
   - Open API docs
   - Run manual discovery

2. ✅ **Configure (Optional)**
   - Set up email notifications
   - Add API keys for Grants.gov
   - Enable AI features

3. ✅ **Use Daily**
   - Manager runs in background
   - Discovery happens automatically
   - Review discoveries in admin panel

---

## 💡 Tips

- **Keep Manager Open:** Minimizes to taskbar, backend keeps running
- **Check Logs:** Logs show all activity - great for debugging
- **Manual Discovery:** Safe to run anytime - won't create duplicates
- **Auto-Start:** Set it and forget it - discovery runs daily

---

## 🆘 Need Help?

- Check **WINDOWS_APP_README.md** for detailed docs
- View logs in the Manager window
- Check `backend/discovery_runs.log` file
- Review API docs at http://localhost:8000/docs

---

**That's it! You're ready to discover grants automatically! 🎉**
