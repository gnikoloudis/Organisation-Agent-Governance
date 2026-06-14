@echo off
title Agent Hub - Decoupled REST API Mode
echo =======================================================
echo Starting FastAPI REST API backend on port 8080...
echo =======================================================

:: Start the FastAPI server in a new window
start "FastAPI Backend" .\.venv\Scripts\uvicorn main_api:app --host 127.0.0.1 --port 8080

:: Give the FastAPI server a few seconds to spin up and bind to port 8080
echo Waiting for API backend to initialize...
timeout /t 3 /nobreak >nul

echo =======================================================
echo Starting Streamlit UI client in API-driven mode...
echo =======================================================
set STREAMLIT_MODE=api
set DEPLOYMENT_ENV=local
set API_BASE_URL=http://127.0.0.1:8080

.\.venv\Scripts\streamlit run app.py
pause
