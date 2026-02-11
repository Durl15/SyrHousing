# 🚀 SyrHousing Deployment Guide

Complete guide to deploying SyrHousing to the cloud for friends to access anywhere.

---

## Quick Deploy to Render.com (Recommended)

Render.com offers **free tier** for both frontend and backend. Perfect for sharing with friends!

### Prerequisites

1. **GitHub Account** - Your code is already at: https://github.com/Durl15/SyrHousing
2. **Render Account** - Sign up free at: https://render.com

---

## Step-by-Step Deployment

### Part 1: Deploy Backend (5 minutes)

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Click **New +** → **Web Service**

2. **Connect GitHub Repository**
   - Click **Connect account** (if first time)
   - Search for: `Durl15/SyrHousing`
   - Click **Connect**

3. **Configure Backend Service**
   ```
   Name: syrhousing-backend
   Region: Choose closest to you (e.g., Oregon)
   Branch: main
   Root Directory: (leave blank)
   Runtime: Python 3
   Build Command: pip install -r backend/requirements.txt
   Start Command: cd backend && gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
   ```

4. **Select Free Plan**
   - Instance Type: **Free**
   - Click **Advanced** to add environment variables

5. **Add Environment Variables** (Click "Add Environment Variable" for each):
   ```
   SECRET_KEY = your-random-secret-key-here-use-any-long-string
   CORS_ORIGINS = ["*"]
   DEBUG = false
   DISCOVERY_ENABLED = true
   DISCOVERY_SOURCES = rss_feed
   FRONTEND_URL = https://syrhousing-frontend.onrender.com
   ```

   Optional (for AI features):
   ```
   ANTHROPIC_API_KEY = your-claude-api-key
   LLM_PROVIDER = anthropic
   ```

6. **Create Web Service**
   - Click **Create Web Service**
   - Wait 5-10 minutes for deployment
   - **Copy your backend URL**: `https://syrhousing-backend-XXXX.onrender.com`

---

### Part 2: Deploy Frontend (5 minutes)

1. **Create Static Site**
   - In Render Dashboard, click **New +** → **Static Site**
   - Select same repository: `Durl15/SyrHousing`

2. **Configure Frontend**
   ```
   Name: syrhousing-frontend
   Branch: main
   Root Directory: frontend
   Build Command: npm install && npm run build
   Publish Directory: dist
   ```

3. **Add Environment Variable**
   - Click **Advanced**
   - Add variable:
     ```
     VITE_API_URL = https://syrhousing-backend-XXXX.onrender.com
     ```
     ⚠️ **Replace XXXX with your actual backend URL from Part 1**

4. **Create Static Site**
   - Click **Create Static Site**
   - Wait 5-10 minutes for build
   - **Your app is live!** 🎉

5. **Get Your Public URL**
   - Copy the URL: `https://syrhousing-frontend-XXXX.onrender.com`
   - **Share this with friends!**

---

### Part 3: Update Backend CORS (2 minutes)

1. **Go back to Backend Service**
   - In Render Dashboard → syrhousing-backend
   - Click **Environment** tab

2. **Update FRONTEND_URL**
   - Find `FRONTEND_URL` variable
   - Change to: `https://syrhousing-frontend-XXXX.onrender.com`
   - (Use your actual frontend URL)

3. **Redeploy Backend**
   - Render will auto-redeploy
   - Wait 2-3 minutes

---

## ✅ Verification

### Test Your Deployment

1. **Visit Frontend URL**
   - Open: `https://syrhousing-frontend-XXXX.onrender.com`
   - You should see the landing page

2. **Register New Account**
   - Click "Get Started"
   - Fill in details
   - If registration works, backend is connected! ✅

3. **Login as Admin**
   - Email: `admin@syrhousing.com`
   - Password: Your admin password from local database
   - Note: You may need to create a new admin in production

---

## 🔧 Common Issues & Fixes

### Issue 1: "Network Error" when trying to login

**Cause**: Backend URL not set correctly in frontend

**Fix**:
1. Go to frontend service → Environment
2. Check `VITE_API_URL` is your backend URL
3. Rebuild: Settings → Manual Deploy → Clear cache & deploy

### Issue 2: CORS Error in browser console

**Cause**: Backend CORS not allowing frontend domain

**Fix**:
1. Go to backend service → Environment
2. Update `CORS_ORIGINS` to: `["https://syrhousing-frontend-XXXX.onrender.com"]`
3. Or use `["*"]` to allow all (less secure but easier for testing)

### Issue 3: Backend shows "Application failed to respond"

**Cause**: Database not initialized

**Fix**:
1. Go to backend service → Shell
2. Run: `cd backend && python -c "from database import init_db; init_db()"`
3. Restart service

### Issue 4: Discovery page shows no data

**Cause**: Fresh database has no discovery runs yet

**Fix**:
1. Login as admin
2. Go to Discovery Management
3. Click "Run Discovery Now"
4. Wait 1-2 minutes and refresh

---

## 💾 Database Setup (Optional)

The free tier uses SQLite by default, which resets on restart. For persistent data:

### Option A: PostgreSQL on Render (Recommended)

1. In Render Dashboard → **New +** → **PostgreSQL**
2. Name: `syrhousing-db`
3. Plan: **Free**
4. Create Database
5. Copy **Internal Database URL**
6. Add to backend environment:
   ```
   DATABASE_URL = <paste internal database URL>
   ```
7. Redeploy backend

### Option B: External PostgreSQL

Free options:
- **Supabase**: https://supabase.com (1GB free)
- **Neon**: https://neon.tech (3GB free)
- **ElephantSQL**: https://elephantsql.com (20MB free)

---

## 📧 Email Notifications (Optional)

To enable email notifications for discovery:

1. **Get SendGrid API Key**
   - Sign up: https://sendgrid.com (Free: 100 emails/day)
   - Create API key
   - Verify sender email

2. **Add to Backend Environment**
   ```
   SENDGRID_API_KEY = your-sendgrid-api-key
   SENDER_EMAIL = noreply@yourdomain.com
   ```

3. **Redeploy backend**

---

## 🎯 Free Tier Limits

**Render Free Tier:**
- ✅ Web Service: 750 hours/month (enough for one app)
- ✅ Static Sites: Unlimited
- ✅ 100GB bandwidth/month
- ⚠️ Spins down after 15 min of inactivity (30 second cold start)
- ⚠️ SQLite resets on restart (use PostgreSQL for persistence)

**Upgrade if needed:**
- Starter Plan: $7/month (no sleep, 400 hours)

---

## 🔐 Security Checklist

Before sharing with friends:

- [ ] Changed `SECRET_KEY` to random string (not "change-me")
- [ ] Set `DEBUG = false`
- [ ] Using PostgreSQL (not SQLite) for data persistence
- [ ] Updated `CORS_ORIGINS` to specific frontend domain
- [ ] Created strong admin password
- [ ] SendGrid sender email verified (if using email)

---

## 📊 Alternative Deployment Options

### Vercel (Frontend) + Render (Backend)

**Frontend on Vercel:**
```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```
Set environment variable: `VITE_API_URL=<your-backend-url>`

**Backend on Render:** Same as above

### Railway (Full Stack)

1. Sign up: https://railway.app
2. New Project → Deploy from GitHub
3. Add both services (backend + frontend)
4. Configure environment variables
5. Deploy

### Fly.io (Docker)

```bash
fly launch
fly deploy
```

---

## 🎉 You're Live!

**Share with friends:**
```
🏠 SyrHousing Grant Finder
https://syrhousing-frontend-XXXX.onrender.com

Find housing grants in Syracuse, NY
- Browse 50+ programs
- AI chatbot assistance
- Application tracking
- Automated grant discovery
```

---

## 📞 Need Help?

- **Render Docs**: https://render.com/docs
- **Check Logs**: Render Dashboard → Your Service → Logs
- **GitHub Issues**: https://github.com/Durl15/SyrHousing/issues

---

**Total Deployment Time: ~15 minutes**

**Cost: $0/month** (free tier)

**Your app is accessible worldwide!** 🌍
