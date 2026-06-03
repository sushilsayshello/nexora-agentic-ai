@echo off
cd /d %~dp0\..
echo ============================================
echo Nexora Sentinel Setup
echo ============================================
python --version >nul 2>&1
if errorlevel 1 (
  echo Python not found. Install Python 3.10+ first.
  pause
  exit /b 1
)
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Setup complete.
echo Run scripts\run_all.bat next.
pause
