@echo off
cd /d %~dp0\..
echo Starting Nexora Sentinel backend and frontend...
start "Nexora Backend" cmd /k "cd /d %cd%\backend && python main.py"
start "Nexora Frontend" cmd /k "cd /d %cd%\frontend && python -m http.server 3000"
timeout /t 3 >nul
start http://localhost:3000
