@echo off
title SyrHousing Full Stack
color 0B

echo ================================================
echo    Starting SyrHousing Full Stack
echo ================================================
echo.

:: Start backend in new window
echo [1/2] Starting backend server...
start "SyrHousing Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --reload --port 8000"
timeout /t 5 /nobreak >nul

:: Start frontend in new window
echo [2/2] Starting frontend dev server...
start "SyrHousing Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ================================================
echo    Both servers starting!
echo ================================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Press any key to open frontend in browser...
pause >nul

start http://localhost:5173

echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
pause
