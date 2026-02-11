# 🏠 SyrHousing - Automated Grant Management System

> Syracuse housing grant discovery and management platform with automated daily grant discovery, AI-powered assistance, and comprehensive admin tools.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

- 🔍 **Automated Grant Discovery** - Daily discovery from Grants.gov RSS feeds
- 🖥️ **Windows GUI Manager** - One-click server management
- 🤖 **AI-Powered Chatbot** - Claude/OpenAI integration for grant guidance
- ✍️ **Grant Writing Assistant** - AI-powered application drafting
- 📊 **Admin Dashboard** - Comprehensive management tools
- 📧 **Email Notifications** - Deadline alerts and discovery updates
- 🔄 **Auto-Deduplication** - Fuzzy matching prevents duplicates
- 📈 **Confidence Scoring** - Quality assessment for discovered grants

## 🚀 Quick Start (Windows)

### Prerequisites
- Python 3.10 or higher
- Windows 10/11

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/SyrHousing.git
cd SyrHousing
```

2. **Run the installer:**
```bash
Install_SyrHousing.bat
```

3. **Launch the GUI manager:**
```bash
SyrHousing_Manager.bat
```

That's it! The backend will auto-start and discovery will run daily at 2 AM.

## 📖 Documentation

- **Quick Start:** [QUICKSTART_WINDOWS.md](QUICKSTART_WINDOWS.md)
- **Full Manual:** [WINDOWS_APP_README.md](WINDOWS_APP_README.md)
- **Feature Overview:** [WINDOWS_APP_SUMMARY.md](WINDOWS_APP_SUMMARY.md)
- **Setup Guide:** [WINDOWS_SETUP_GUIDE.txt](WINDOWS_SETUP_GUIDE.txt)

## 🎮 Usage

### GUI Manager
```bash
python syrhousing_manager.py
```

Features:
- ▶️ Start/Stop backend with one click
- 🔍 Manual discovery trigger
- 📊 Real-time statistics
- 📜 Live server logs
- 🌐 Quick access to API docs

### Manual Discovery
```bash
python -m backend.scripts.run_discovery
```

### API Server Only
```bash
cd backend
python -m uvicorn backend.main:app --reload
```

API documentation: http://localhost:8000/docs

## ⚙️ Configuration

Edit `backend/.env`:

```bash
# Discovery Settings
DISCOVERY_ENABLED=true
DISCOVERY_SCHEDULE_CRON=0 2 * * *
DISCOVERY_SOURCES=rss_feed

# Optional: Email Notifications
SENDGRID_API_KEY=your_key_here
SENDER_EMAIL=noreply@syrhousing.com

# Optional: AI Features
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here
```

## 🏗️ Architecture

```
SyrHousing/
├── syrhousing_manager.py          # Windows GUI Manager
├── backend/                       # FastAPI Backend
│   ├── main.py                   # Application entry
│   ├── services/discovery/       # Automated discovery
│   ├── api/                      # REST endpoints
│   ├── models/                   # Database models
│   └── .env                      # Configuration
├── frontend/                      # React Frontend (optional)
└── syrhousing.db                 # SQLite Database
```

## 🔧 Tech Stack

**Backend:**
- FastAPI - Web framework
- SQLAlchemy - ORM
- APScheduler - Task scheduling
- RapidFuzz - Fuzzy matching
- BeautifulSoup - Web scraping
- SendGrid - Email service

**Frontend:**
- React - UI framework
- Tailwind CSS - Styling
- Vite - Build tool

**AI:**
- Anthropic Claude - Chatbot & grant writing
- OpenAI GPT - Alternative LLM

## 📊 Features in Detail

### Automated Discovery
- Fetches grants from Grants.gov RSS feeds
- Extracts structured data (deadlines, amounts, contacts)
- Fuzzy deduplication (85% name + 70% agency matching)
- Confidence scoring (0.0-1.0)
- Admin review workflow

### Windows Manager
- Beautiful GUI with tkinter
- Real-time status monitoring
- Live log display
- One-click operations
- Auto-start capability

### API Endpoints
- 13 REST routers
- Full CRUD operations
- Admin authentication
- Interactive documentation

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - Feel free to use and modify!

## 🙏 Acknowledgments

- Built with Claude Code
- Grant data from Grants.gov
- Syracuse housing programs database

## 📧 Support

For issues or questions:
- Open an issue on GitHub
- Check documentation in `/docs`
- Review API docs at `/docs` endpoint

## 🎯 Roadmap

- [ ] Frontend admin dashboard
- [ ] Additional grant sources (state, local)
- [ ] Machine learning for categorization
- [ ] Mobile app
- [ ] Multi-tenant support

---

**Made with ❤️ for Syracuse homeowners**
