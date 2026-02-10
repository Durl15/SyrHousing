# SyrHousing - Syracuse Housing Grant Agent

A comprehensive grant management system for Syracuse, NY housing assistance programs. Helps homeowners find, track, and apply for housing grants with AI-powered matching and eligibility screening.

## Features

✅ **Comprehensive Grant Database**
- 16+ Syracuse-area housing grants (SHARP, RESTORE, T-HIP, NYSERDA, HHQ programs, etc.)
- Detailed eligibility requirements, income limits, and application checklists
- Categorized by type: Emergency Repairs, Energy Efficiency, Accessibility, Historic Preservation

✅ **Smart Matching & Eligibility**
- AI-powered eligibility screening
- Personalized match scores based on user profile
- Filter grants by category and repair needs

✅ **Downloadable Reports**
- Generate PDF reports of matching grants
- Export to CSV for spreadsheet analysis
- Create pre-filled application checklists per grant

✅ **Modern Web Interface**
- Clean, professional dashboard
- Grant status badges (Open/Closing Soon/Closed)
- Deadline countdown timers
- Mobile-responsive design

✅ **Notification System**
- Email alerts for grants closing within 30 days
- Notifications for new grant availability
- Deadline change tracking via web monitoring

✅ **Application Tracking**
- Track your grant applications
- Monitor application status
- Receive updates on progress

## Prerequisites

### Windows 10 Requirements

- **Python 3.10+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **Git** (optional) - [Download Git](https://git-scm.com/download/win)

## Installation

### Quick Start (Windows 10)

1. **Clone or download the project**
   ```bash
   git clone https://github.com/yourusername/SyrHousing.git
   cd SyrHousing
   ```

2. **Install Python dependencies**
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On Windows Command Prompt:
   venv\Scripts\activate.bat
   # On Windows PowerShell:
   venv\Scripts\Activate.ps1

   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Install Frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Configure environment**
   ```bash
   # Copy example environment file
   copy backend\.env.example backend\.env

   # Edit backend\.env with your settings (optional)
   notepad backend\.env
   ```

5. **Initialize the database**
   ```bash
   cd backend
   python -m scripts.seed_syracuse_grants
   cd ..
   ```

## Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Access the application at: **http://localhost:5173**

API documentation at: **http://localhost:8000/docs**

### Production Mode

1. **Build frontend:**
   ```bash
   cd frontend
   npm run build
   cd ..
   ```

2. **Run backend with Gunicorn (Linux/Mac):**
   ```bash
   cd backend
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

   **Or with Uvicorn (Windows):**
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Configuration

### Backend Configuration (backend/.env)

```env
# Database
DATABASE_URL=sqlite:///./syrhousing.db

# CORS (for frontend)
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Notifications (SendGrid)
SENDGRID_API_KEY=your-sendgrid-api-key
SENDER_EMAIL=noreply@syrhousing.com
SENDER_NAME=SyrHousing Grant Agent

# AI/LLM (Optional)
LLM_PROVIDER=anthropic  # or "openai" or "none"
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key

# Frontend URL
FRONTEND_URL=http://localhost:5173
```

### Frontend Configuration (frontend/.env)

```env
VITE_API_URL=http://localhost:8000
```

## Usage Guide

### For Homeowners

1. **Create an account** - Register with your email
2. **Complete your profile** - Enter your location, age, income, and repair needs
3. **Browse grants** - View personalized grant recommendations
4. **Download reports** - Generate PDF or CSV reports of matching grants
5. **Track applications** - Keep track of grants you've applied for
6. **Get notifications** - Receive email alerts for closing deadlines

### For Administrators

1. **Access admin panel** - Navigate to `/admin`
2. **Manage grants** - Add, edit, or deactivate grant programs
3. **Monitor scans** - View web monitoring results for grant websites
4. **Send alerts** - Send custom notifications to users
5. **View analytics** - Track user activity and grant popularity

## Grant Database

Currently includes 16+ Syracuse-area grants:

**Emergency & Safety:**
- SHARP Grant (Syracuse)
- NYS RESTORE Program (Senior 60+)
- Home HeadQuarters Urgent Care
- T-HIP (Onondaga County)
- HEAP (Heating Assistance)

**Energy Efficiency:**
- NYSERDA EmPower+
- PEACE Inc. Weatherization

**Accessibility:**
- NYS Access to Home
- AccessCNY E-Mods

**Health Hazards:**
- Syracuse Lead Program
- Onondaga County Lead Reduction

**Other Programs:**
- Homebuyer Dream Program
- Historic Preservation Programs
- USDA Section 504 (Rural)

## API Endpoints

### Public Endpoints
- `GET /health` - Health check
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login

### Protected Endpoints (Require Authentication)
- `GET /programs` - List all grants
- `GET /ranking/ranked-programs` - Get personalized grant rankings
- `GET /export/pdf` - Export grants to PDF
- `GET /export/csv` - Export grants to CSV
- `POST /applications` - Create application tracking
- `GET /notifications/closing-soon` - Get grants closing soon

### Admin Endpoints
- `POST /admin/programs` - Create/update grants
- `POST /scanner/scan` - Run manual grant website scan
- `POST /notifications/send-custom-alert` - Send notifications to users

Full API documentation available at: `http://localhost:8000/docs`

## Troubleshooting

### Common Issues

**Issue: "Module not found" errors**
- Solution: Make sure virtual environment is activated and dependencies are installed
  ```bash
  pip install -r requirements.txt
  ```

**Issue: "Port already in use"**
- Solution: Stop other processes using ports 8000 or 5173, or change the port
  ```bash
  # Backend on different port
  uvicorn main:app --port 8001

  # Frontend on different port
  npm run dev -- --port 5174
  ```

**Issue: Database errors**
- Solution: Delete and recreate the database
  ```bash
  del backend\syrhousing.db
  cd backend
  python -m scripts.seed_syracuse_grants
  ```

**Issue: PDF export fails**
- Solution: Install PDF dependencies
  ```bash
  pip install reportlab fpdf2 Pillow
  ```

**Issue: Email notifications not working**
- Solution: Configure SendGrid API key in backend/.env
  ```env
  SENDGRID_API_KEY=your-key-here
  SENDER_EMAIL=your-email@domain.com
  ```

### Windows-Specific Issues

**PowerShell execution policy error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Python not found:**
- Add Python to PATH during installation, or use full path:
  ```bash
  C:\Python310\python.exe -m venv venv
  ```

## Development

### Project Structure

```
SyrHousing/
├── backend/                # FastAPI backend
│   ├── api/               # API endpoints
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   ├── schemas/           # Pydantic schemas
│   ├── scripts/           # Utility scripts
│   ├── utils/             # Helper utilities
│   ├── main.py            # Application entry point
│   ├── database.py        # Database configuration
│   └── requirements.txt   # Python dependencies
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── contexts/     # React contexts
│   │   └── lib/          # Utilities
│   ├── package.json      # Node dependencies
│   └── vite.config.js    # Vite configuration
├── Data/                 # Data files (legacy)
├── Logs/                 # Application logs
├── requirements.txt      # Root Python dependencies
└── README.md             # This file
```

### Running Tests

```bash
cd backend
pytest
```

### Code Style

- Backend: Follow PEP 8 style guide
- Frontend: ESLint configuration in `frontend/eslint.config.js`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Email: support@syrhousing.com
- Documentation: [docs.syrhousing.com](https://docs.syrhousing.com)

## Acknowledgments

- City of Syracuse Housing Programs
- Home HeadQuarters Inc.
- NYSERDA
- PEACE Inc.
- Onondaga County Community Development

## Version History

### v1.1.0 (Current)
- ✅ Enhanced grant database with 16+ Syracuse programs
- ✅ PDF/CSV export functionality
- ✅ Status badges and deadline countdown timers
- ✅ Email notification system
- ✅ Comprehensive error handling and logging
- ✅ Windows 10 compatibility improvements

### v1.0.0
- Initial release
- Basic grant database
- User authentication
- Profile management
- Grant ranking system
- Web monitoring

## Roadmap

- [ ] Mobile app (iOS/Android)
- [ ] Spanish language support
- [ ] Integration with NYS grant databases
- [ ] Automated application form filling
- [ ] Grant application document storage
- [ ] SMS notifications
- [ ] Voice assistant integration

---

**Built with ❤️ for Syracuse homeowners**
