@echo off
cd /d "%~dp0"
echo Starting Bulb Control...
".venv\Scripts\python.exe" main.py
if errorlevel 1 (
    echo.
    echo Script crashed!
    pause
)
