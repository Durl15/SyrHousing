@echo off
REM SyrHousing Quick Start Script for Windows
REM This script sets up and runs the SyrHousing application

echo ================================
echo SyrHousing Quick Start
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

echo Python and Node.js detected!
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created!
    echo.
)

REM Activate virtual environment and install dependencies
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment activation script not found
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if backend dependencies are installed
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Python dependencies...
    echo This may take a few minutes...
    pip install --upgrade pip
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install Python dependencies
        pause
        exit /b 1
    )
    echo Python dependencies installed!
    echo.
)

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules\" (
    echo Installing frontend dependencies...
    echo This may take a few minutes...
    cd frontend
    call npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo Frontend dependencies installed!
    echo.
)

REM Check if database exists
if not exist "backend\syrhousing.db" (
    echo Initializing database with Syracuse grants...
    cd backend
    python -m scripts.seed_syracuse_grants
    if %errorlevel% neq 0 (
        echo ERROR: Failed to initialize database
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo Database initialized!
    echo.
)

REM Check if .env file exists
if not exist "backend\.env" (
    echo Creating default .env file...
    (
        echo DATABASE_URL=sqlite:///./syrhousing.db
        echo SECRET_KEY=change-this-in-production-use-openssl-rand-hex-32
        echo DEBUG=True
        echo CORS_ORIGINS=[\"http://localhost:5173\",\"http://localhost:3000\"]
        echo LLM_PROVIDER=none
        echo FRONTEND_URL=http://localhost:5173
    ) > backend\.env
    echo .env file created with default settings
    echo.
)

echo ================================
echo Setup Complete!
echo ================================
echo.
echo Starting SyrHousing...
echo.
echo Opening 2 command windows:
echo   1. Backend API (http://localhost:8000)
echo   2. Frontend App (http://localhost:5173)
echo.
echo To stop, close both windows or press Ctrl+C in each
echo.
pause

REM Start backend in new window
start "SyrHousing Backend" cmd /k "cd /d %~dp0backend && ..\venv\Scripts\activate.bat && uvicorn main:app --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
start "SyrHousing Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo SyrHousing is starting!
echo.
echo Backend API: http://localhost:8000/docs
echo Frontend App: http://localhost:5173
echo.
echo Check the 2 new command windows for status
echo.
pause
