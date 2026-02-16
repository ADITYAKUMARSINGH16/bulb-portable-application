@echo off
cd /d "%~dp0"
echo Starting Discovery Toolkit...
".venv\Scripts\python.exe" tools/find_bulb_ui.py
pause
