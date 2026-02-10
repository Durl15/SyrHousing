@echo off
title SyrHousing Installer
color 0A

echo ========================================
echo    SyrHousing Windows Installation
echo ========================================
echo.

:: Check for Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo   X Python not found!
    echo   Please install Python 3.10+ from python.org
    echo   Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)
python --version
echo   √ Python found
echo.

:: Install backend dependencies
echo [2/5] Installing backend dependencies...
cd backend
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo   X Failed to install dependencies
    pause
    exit /b 1
)
cd ..
echo   √ Backend dependencies installed
echo.

:: Install GUI dependencies
echo [3/5] Installing GUI dependencies...
pip install requests --quiet --disable-pip-version-check
echo   √ GUI dependencies installed
echo.

:: Initialize database
echo [4/5] Initializing database...
python -c "from backend.database import Base, engine; Base.metadata.create_all(engine); print('  √ Database initialized')"
echo.

:: Seed initial data
echo [5/5] Seeding initial grant data...
python -m backend.scripts.seed_syracuse_grants >nul 2>&1
if errorlevel 1 (
    echo   ! No seed data available (optional)
) else (
    echo   √ Grant data seeded
)
echo.

echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Run: Setup_SyrHousing.ps1 (creates shortcuts)
echo   2. Or run: python syrhousing_manager.py
echo   3. Or double-click: SyrHousing_Manager.bat
echo.
echo To set up auto-start and shortcuts:
echo   Right-click Setup_SyrHousing.ps1 ^> Run with PowerShell
echo.

pause
