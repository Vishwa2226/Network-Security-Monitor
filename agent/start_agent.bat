@echo off
setlocal
cd /d "%~dp0"
title Network Security Monitor - Windows Sensor
echo ================================================
echo   NETWORK SECURITY MONITOR - WINDOWS SENSOR
echo ================================================
if not exist ".venv\Scripts\python.exe" (
  echo Creating the helper environment...
  py -3.11 -m venv .venv
  if errorlevel 1 (
    echo Python 3.11 was not found. Install Python 3.11 and try again.
    pause
    exit /b 1
  )
)
echo Checking helper dependencies...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" agent.py
endlocal
