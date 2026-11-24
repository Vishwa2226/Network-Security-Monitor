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
    echo Python 3.11 was not found or the virtual environment could not be created.
    echo Install Python 3.11 from python.org with pip enabled, then try again.
    pause
    exit /b 1
  )
)

".venv\Scripts\python.exe" -m pip --version >nul 2>&1
if errorlevel 1 (
  echo Pip is missing from the helper environment. Repairing it...
  ".venv\Scripts\python.exe" -m ensurepip --upgrade
  if errorlevel 1 (
    echo Repair failed. Rebuilding the helper environment...
    rmdir /s /q ".venv"
    py -3.11 -m venv .venv
    if errorlevel 1 (
      echo Could not rebuild the environment. Check your Python 3.11 installation.
      pause
      exit /b 1
    )
  )
)

".venv\Scripts\python.exe" -m pip --version >nul 2>&1
if errorlevel 1 (
  echo Pip is still unavailable.
  echo Reinstall Python 3.11 from python.org and make sure pip and venv are selected.
  pause
  exit /b 1
)

echo Installing or checking helper dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo Pip upgrade failed. Continuing with the installed pip version...
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. Check your internet connection and try again.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" agent.py
endlocal
