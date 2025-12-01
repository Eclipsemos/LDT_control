@echo off
REM Startup script for MAVLink Gateway (Windows)

echo ============================================
echo   LDT MAVLink Gateway - Starting...
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if dependencies are installed
pip show pymavlink >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting MAVLink Gateway...
echo Press Ctrl+C to stop
echo.

REM Run the gateway
python mavlink_gateway.py

pause

