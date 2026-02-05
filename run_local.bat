@echo off
echo Starting Local Server...
echo Static Source: Frontend Directory

cd backend
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
pause
