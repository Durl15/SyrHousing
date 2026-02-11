# 🌐 SyrHousing Web Application Guide

Complete guide to running, using, and deploying the SyrHousing web application.

---

## 🎯 What You Have

A complete **full-stack web application** with:

### Frontend (React + Vite + Tailwind)
- **Landing Page** - Welcome and features
- **User Dashboard** - Personalized grant recommendations
- **Grant Browser** - Search, filter, and explore grants
- **AI Chatbot** - Get grant assistance
- **Grant Writer** - AI-powered application drafting
- **Application Tracking** - Manage your applications
- **Profile Management** - Update user info

### Admin Panel
- **Admin Dashboard** - Statistics and overview
- **User Management** - Manage all users
- **Program Management** - CRUD operations for grants
- **Application Management** - Review user applications
- **Scanner Management** - Monitor web scraping
- **🆕 Discovery Management** - Review discovered grants (NEW!)

### Backend (FastAPI + SQLAlchemy)
- REST API with 13 routers
- JWT authentication
- Automated grant discovery
- AI integration (Claude/OpenAI)
- Email notifications
- Scheduled tasks

---

## 🚀 Quick Start

### Method 1: One-Click Launcher (Easiest)

```bash
# Double-click this file:
Start_Web_App.bat
```

This automatically:
1. Starts backend on port 8000
2. Starts frontend on port 5173
3. Opens browser to http://localhost:5173

### Method 2: Windows Manager + Frontend

**Terminal 1 - Backend (via Manager):**
```bash
python syrhousing_manager.py
# Click "Start Backend"
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install  # First time only
npm run dev
```

### Method 3: Manual (Full Control)

**Terminal 1 - Backend:**
```bash
cd C:\SyrHousing
python -m uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd C:\SyrHousing\frontend
npm install  # First time only
npm run dev
```

---

## 📦 First-Time Setup

### 1. Install Frontend Dependencies

```bash
cd C:\SyrHousing\frontend
npm install
```

This installs:
- React 19
- React Router v7
- Axios (HTTP client)
- Tailwind CSS v4
- Recharts (for graphs)
- Vite (build tool)

### 2. Configure Frontend API URL (Optional)

If your backend is NOT on `localhost:8000`, edit:

**File:** `frontend/src/lib/api.js`

```javascript
const API_BASE_URL = 'http://localhost:8000/api';
// Change to your backend URL if different
```

### 3. Start Both Servers

See "Quick Start" above.

---

## 🎮 Using the Web App

### For Regular Users

**1. Register an Account**
- Visit: http://localhost:5173
- Click "Get Started" or "Register"
- Fill in: Name, Email, Password
- Verify email (if configured)

**2. Browse Grants**
- Navigate to "Programs"
- Use filters: Category, Type, Jurisdiction
- Use advanced search
- Click grant to see details

**3. Get AI Help**
- Click "Chat" in navigation
- Ask questions like:
  - "What grants am I eligible for?"
  - "Help me understand SHARP grant"
  - "What documents do I need?"

**4. Write Applications**
- From grant detail page, click "Apply"
- Use AI Grant Writer to draft application
- Edit the generated content
- Save as draft or submit

**5. Track Applications**
- Go to "My Applications"
- See status: Draft, Submitted, Under Review, Approved, Denied
- Get deadline countdowns
- Receive email notifications

### For Administrators

**1. Login as Admin**
```
Email: admin@syrhousing.com
Password: (your admin password)
```

**2. Access Admin Panel**
- Click your name → "Admin Dashboard"
- Or visit: http://localhost:5173/admin

**3. Manage Discovered Grants (NEW!)**
- Go to: Admin → Discovery Management
- View statistics: Total runs, discovered, pending
- See recent discovery runs
- Review pending grants:
  - **✓ Approve** - Creates a Program
  - **✗ Reject** - Marks as not relevant
  - **🔄 Duplicate** - Links to existing program
- Run manual discovery
- Check confidence scores

**4. Manage Programs**
- Admin → Program Management
- Add, edit, delete grants
- Set priority ranking
- Change active status

**5. Review Applications**
- Admin → Application Management
- See all user applications
- Change status
- Add admin notes

**6. Manage Users**
- Admin → User Management
- View all users
- Promote to admin
- Deactivate accounts

---

## 🎨 Web App Features

### User Features

#### 1. Advanced Search
- **Multi-select Categories:**
  - Urgent Safety
  - Health Hazards
  - Aging in Place
  - Energy & Bills
  - Historic Restoration
  - Buying Help

- **Filters:**
  - Program Type (Grant, Loan, Rebate)
  - Jurisdiction (Syracuse, County, State, Federal)
  - Benefit Amount Range
  - Has Deadline
  - Search by Keywords

- **Sorting:**
  - Priority
  - Name
  - Deadline
  - Benefit Amount
  - Recently Added

#### 2. AI Chatbot
- Powered by Claude or OpenAI
- Context-aware responses
- Grant eligibility questions
- Document requirement help
- Application guidance

#### 3. Grant Writer
- AI-powered draft generation
- Takes user profile into account
- Generates application essays
- Editable rich text editor
- Save and export functionality

#### 4. Application Tracking
- Dashboard view of all applications
- Status badges (color-coded)
- Deadline countdowns
- Email reminders
- Document checklist

#### 5. Profile Management
- Personal information
- Income verification
- Property details
- Eligibility factors
- Saved grant preferences

### Admin Features

#### 1. Discovery Management 🆕
```
Features:
- Statistics Dashboard
  * Total discovery runs
  * Grants discovered
  * Pending review count
  * Average confidence score

- Recent Runs Table
  * Started time
  * Status (completed, running, failed)
  * Sources checked
  * Grants found
  * Duplicates detected
  * Error count

- Discovered Grants List
  * Filter by status (pending, approved, rejected, duplicate)
  * Confidence badges (color-coded)
  * Source type indicators
  * Jurisdiction tags
  * All extracted data displayed
  * Eligibility summaries

- Actions
  * ✓ Approve - Creates Program in database
  * ✗ Reject - Mark with reason
  * 🔄 Duplicate - Link to existing program
  * ▶ Run Discovery Now - Manual trigger

- Confidence Indicators
  * Green (80%+) - High quality
  * Yellow (50-80%) - Medium quality
  * Red (<50%) - Low quality
```

#### 2. Program Management
- Full CRUD operations
- Bulk operations
- Import/export
- Priority ranking
- Category assignment

#### 3. User Management
- User list with search
- Role assignment
- Account activation/deactivation
- Registration statistics

#### 4. Application Management
- All applications view
- Filter by status
- Bulk status updates
- Admin notes
- Export functionality

#### 5. Scanner Management
- Web scraping monitoring
- Deadline change detection
- Scan history
- Error logs

---

## 🌍 Deployment Options

### Option 1: Local Network (Share on WiFi)

**1. Find your local IP:**
```cmd
ipconfig
# Look for "IPv4 Address" (e.g., 192.168.1.100)
```

**2. Start backend with host binding:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**3. Start frontend with host:**
```bash
cd frontend
npm run dev -- --host
```

**4. Share with friends:**
```
Backend:  http://192.168.1.100:8000
Frontend: http://192.168.1.100:5173
```

Anyone on your WiFi can access it!

### Option 2: Cloud Deployment (Free Tier)

#### Render.com (Recommended - Free Tier)

**Backend:**
1. Go to https://render.com
2. New → Web Service
3. Connect GitHub repo: `Durl15/SyrHousing`
4. Settings:
   - Name: `syrhousing-backend`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn backend.main:app -k uvicorn.workers.UvicornWorker`
5. Environment Variables (add from `.env`)
6. Click "Create Web Service"
7. Get URL: `https://syrhousing-backend.onrender.com`

**Frontend:**
1. Render → New → Static Site
2. Connect same GitHub repo
3. Settings:
   - Name: `syrhousing-frontend`
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `dist`
4. Environment Variables:
   - `VITE_API_URL=https://syrhousing-backend.onrender.com/api`
5. Click "Create Static Site"
6. Get URL: `https://syrhousing-frontend.onrender.com`

**Done!** Share the frontend URL with anyone!

#### Vercel (Frontend) + Render (Backend)

**Backend on Render** (same as above)

**Frontend on Vercel:**
```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```

Follow prompts, set:
- Build Command: `npm run build`
- Output Directory: `dist`
- Environment Variable: `VITE_API_URL=<your-backend-url>`

### Option 3: Docker (Advanced)

**Build and run:**
```bash
cd C:\SyrHousing
docker-compose up -d
```

Access at:
- Frontend: http://localhost:80
- Backend: http://localhost:8000

**Deploy to cloud:**
- AWS ECS
- Google Cloud Run
- Azure Container Apps
- DigitalOcean App Platform

---

## 📝 Environment Variables for Production

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/syrhousing  # Use PostgreSQL in production

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
DEBUG=false

# CORS
CORS_ORIGINS=["https://your-frontend-url.com"]

# Email
SENDGRID_API_KEY=your_key_here
SENDER_EMAIL=noreply@syrhousing.com

# AI (optional)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here

# Discovery
DISCOVERY_ENABLED=true
DISCOVERY_SCHEDULE_CRON=0 2 * * *
DISCOVERY_SOURCES=rss_feed,grants_gov_api
GRANTS_GOV_API_KEY=your_key_here
```

### Frontend (.env)
```bash
VITE_API_URL=https://your-backend-url.com/api
```

---

## 🐛 Troubleshooting

### Frontend Won't Start

**Error:** `npm: command not found`
```bash
# Install Node.js from nodejs.org
# Restart terminal
node --version
npm --version
```

**Error:** `Module not found`
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Error:** `Port 5173 already in use`
```bash
# Edit vite.config.js
server: {
  port: 3000  // Change port
}
```

### Backend Won't Connect

**Error:** `Network Error` in browser console

**Fix:** Check CORS settings in `backend/config.py`
```python
CORS_ORIGINS: str = '["http://localhost:5173"]'
```

**Error:** `401 Unauthorized`

**Fix:** Clear browser storage and login again
```javascript
// In browser console
localStorage.clear()
location.reload()
```

### Discovery Page Not Working

**Error:** `404 Not Found` on `/api/discovery/`

**Fix:** Make sure backend is running the latest code
```bash
cd C:\SyrHousing
git pull
# Restart backend
```

---

## 📊 Performance Tips

### Development
```bash
# Backend: auto-reload enabled
uvicorn backend.main:app --reload

# Frontend: HMR (Hot Module Replacement) enabled
npm run dev
```

### Production
```bash
# Backend: multiple workers
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Frontend: build for production
npm run build
# Serve with nginx or static host
```

---

## 🎯 Summary

**You now have:**

✅ **Full-Stack Web App** - Backend + Frontend
✅ **Admin Panel** - Complete management interface
✅ **Discovery UI** - Review discovered grants visually
✅ **User Features** - Browse, chat, apply, track
✅ **Mobile Responsive** - Works on phones/tablets
✅ **Production Ready** - Deploy anywhere
✅ **Open Source** - On GitHub for sharing

**To run locally:**
```bash
Start_Web_App.bat
```

**To deploy:**
- Render.com (free tier)
- Vercel + Render
- Your own server

**Live URL (when deployed):**
Share with anyone: `https://your-app-url.com`

---

**🎉 Your complete grant management platform is ready for the web!**

No desktop app needed - accessible from any device, anywhere! 🌍
