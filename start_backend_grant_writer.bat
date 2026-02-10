@echo off
cd /d C:\SyrHousing
venv\Scripts\python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
