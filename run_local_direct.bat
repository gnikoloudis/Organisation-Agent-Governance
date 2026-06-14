@echo off
title Agent Hub - Direct SQLite Mode
echo =======================================================
echo Starting Agent Customization Hub in Direct Local Mode...
echo Database: SQLite (agent_customizations.db)
echo Mode: Direct Core Execution
echo =======================================================
set STREAMLIT_MODE=direct
set DEPLOYMENT_ENV=local

.\.venv\Scripts\streamlit run app.py
pause
