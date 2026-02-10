# SyrHousing Installation Guide for Windows 10

Complete step-by-step installation guide for Windows 10 users.

## Prerequisites Check

Before starting, verify you have or install the following:

### 1. Python 3.10 or Higher

**Check if Python is installed:**
```cmd
python --version
```

**If not installed:**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
4. Verify installation: `python --version`

### 2. Node.js 18 or Higher

**Check if Node.js is installed:**
```cmd
node --version
npm --version
```

**If not installed:**
1. Download from [nodejs.org](https://nodejs.org/)
2. Run the installer (use LTS version)
3. Verify installation: `node --version` and `npm --version`

### 3. Git (Optional but recommended)

**Check if Git is installed:**
```cmd
git --version
```

**If not installed:**
1. Download from [git-scm.com](https://git-scm.com/download/win)
2. Run the installer
3. Verify installation: `git --version`

## Installation Steps

### Step 1: Get the Project Files

**Option A: Using Git (Recommended)**
```cmd
cd C:\
git clone https://github.com/yourusername/SyrHousing.git
cd SyrHousing
```

**Option B: Download ZIP**
1. Download the ZIP file from GitHub
2. Extract to `C:\SyrHousing`
3. Open Command Prompt
4. Navigate to the project:
   ```cmd
   cd C:\SyrHousing
   ```

### Step 2: Set Up Python Virtual Environment

```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
# For Command Prompt:
venv\Scripts\activate.bat

# For PowerShell:
venv\Scripts\Activate.ps1

# You should see (venv) before your prompt
```

**PowerShell Users - If you get an execution policy error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Install Python Dependencies

```cmd
# Make sure virtual environment is activated (you should see (venv))
pip install --upgrade pip
pip install -r requirements.txt
```

This will take a few minutes. You should see packages being installed.

### Step 4: Install Frontend Dependencies

```cmd
# Navigate to frontend directory
cd frontend

# Install Node packages
npm install

# Go back to project root
cd ..
```

This will take a few minutes and create a `node_modules` folder.

### Step 5: Configure Environment Variables

```cmd
# Copy the example environment file
copy backend\.env.example backend\.env

# Edit the file with Notepad
notepad backend\.env
```

**Minimum configuration (for local development):**
```env
DATABASE_URL=sqlite:///./syrhousing.db
SECRET_KEY=your-random-secret-key-change-this
DEBUG=True
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

**Optional configurations:**

For email notifications (optional):
```env
SENDGRID_API_KEY=your-sendgrid-api-key
SENDER_EMAIL=noreply@syrhousing.com
```

For AI features (optional):
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### Step 6: Initialize the Database

```cmd
cd backend
python -m scripts.seed_syracuse_grants
cd ..
```

You should see output showing grants being added to the database.

### Step 7: Verify Installation

**Test backend:**
```cmd
cd backend
uvicorn main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Test in browser:**
- Open: http://localhost:8000/docs
- You should see the API documentation

Press `Ctrl+C` to stop the backend.

**Test frontend:**
```cmd
cd ..\frontend
npm run dev
```

You should see:
```
VITE vX.X.X  ready in XXX ms
➜  Local:   http://localhost:5173/
```

**Test in browser:**
- Open: http://localhost:5173
- You should see the SyrHousing homepage

Press `Ctrl+C` to stop the frontend.

## Running the Application

### Method 1: Using Two Command Prompt Windows

**Window 1 - Backend:**
```cmd
cd C:\SyrHousing\backend
venv\Scripts\activate.bat
uvicorn main:app --reload
```

**Window 2 - Frontend:**
```cmd
cd C:\SyrHousing\frontend
npm run dev
```

Access the app at: **http://localhost:5173**

### Method 2: Using PowerShell Script (Advanced)

Create a file `start.ps1` in the project root:

```powershell
# Start Backend
$backend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload" -PassThru

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start Frontend
$frontend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -PassThru

Write-Host "SyrHousing is starting..."
Write-Host "Backend PID: $($backend.Id)"
Write-Host "Frontend PID: $($frontend.Id)"
Write-Host ""
Write-Host "Access the application at: http://localhost:5173"
Write-Host ""
Write-Host "To stop, close both PowerShell windows or press Ctrl+C in each"
```

Then run:
```powershell
.\start.ps1
```

## First-Time Setup

1. **Open the application**: http://localhost:5173

2. **Register an account:**
   - Click "Register"
   - Enter your information
   - Click "Create Account"

3. **Complete your profile:**
   - Navigate to "Profile" in the menu
   - Enter your location, age, income, and repair needs
   - Click "Save Profile"

4. **Browse grants:**
   - Go to "Programs"
   - See your personalized grant matches
   - Click on any grant for details

5. **Export reports:**
   - Filter grants by category
   - Click "Export PDF" or "Export CSV"

## Troubleshooting

### Problem: "Python is not recognized"

**Solution:**
1. Reinstall Python and check "Add to PATH"
2. Or add Python manually to PATH:
   - Right-click "This PC" → Properties
   - Advanced system settings → Environment Variables
   - Edit PATH, add: `C:\Python310` and `C:\Python310\Scripts`

### Problem: "pip install" fails with SSL errors

**Solution:**
```cmd
python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org pip setuptools
pip install --upgrade pip
pip install -r requirements.txt
```

### Problem: "Cannot activate virtual environment"

**Solution for Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

**Solution for PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1
```

### Problem: "Port 8000 is already in use"

**Solution 1 - Find and stop the process:**
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

**Solution 2 - Use a different port:**
```cmd
uvicorn main:app --reload --port 8001
```

Update `frontend/.env`:
```env
VITE_API_URL=http://localhost:8001
```

### Problem: "npm ERR! code ENOENT"

**Solution:**
```cmd
cd frontend
del package-lock.json
rmdir /s /q node_modules
npm install
```

### Problem: Database errors

**Solution - Reset database:**
```cmd
cd backend
del syrhousing.db
del syrhousing.db-shm
del syrhousing.db-wal
python -m scripts.seed_syracuse_grants
```

### Problem: Frontend shows "Network Error"

**Solution:**
1. Make sure backend is running: http://localhost:8000/docs
2. Check `frontend/.env` has correct API URL:
   ```env
   VITE_API_URL=http://localhost:8000
   ```
3. Restart frontend:
   ```cmd
   npm run dev
   ```

## Getting Help

If you encounter issues not covered here:

1. **Check the logs:**
   - Backend: Look at the terminal running `uvicorn`
   - Frontend: Look at browser console (F12)

2. **Check backend logs folder:**
   ```cmd
   cd backend\logs
   type syrhousing_errors.log
   ```

3. **Verify all services are running:**
   - Backend: http://localhost:8000/docs should load
   - Frontend: http://localhost:5173 should load

4. **Common fixes:**
   - Restart both backend and frontend
   - Deactivate and reactivate virtual environment
   - Clear browser cache
   - Check firewall/antivirus isn't blocking ports

## Next Steps

✅ Application is running!

**What to do next:**
1. ✅ Register an account
2. ✅ Complete your profile
3. ✅ Browse available grants
4. ✅ Download PDF reports
5. ✅ Track applications

**For administrators:**
- Access admin panel: http://localhost:5173/admin
- First user is automatically an admin

**Enable email notifications:**
1. Sign up for SendGrid (free tier available)
2. Get API key from SendGrid dashboard
3. Add to `backend/.env`:
   ```env
   SENDGRID_API_KEY=your-key-here
   SENDER_EMAIL=noreply@yourdomain.com
   ```
4. Restart backend

**Enable AI features:**
1. Get API key from Anthropic or OpenAI
2. Add to `backend/.env`:
   ```env
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=your-key-here
   ```
3. Restart backend

---

**Congratulations! 🎉**

Your SyrHousing installation is complete!

For more information, see the main README.md file.
