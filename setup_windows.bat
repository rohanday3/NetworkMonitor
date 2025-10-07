@echo off
REM Quick Windows Setup Script
REM Run this script to prepare all Windows files

echo ========================================
echo Network Monitor Windows Quick Setup
echo ========================================
echo.

echo Setting up Windows-specific files...

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Python not found in PATH
    echo Please install Python 3.7+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
)

echo Files prepared for Windows installation:
echo.
echo Installation:
echo   install_windows.bat       - Main installation script ^(run as admin^)
echo.
echo Core Application:
echo   network_monitor_windows.py - Main monitoring application
echo   dashboard_windows.py       - Web dashboard for Windows
echo   visualize.py              - Chart generation
echo.
echo Analysis Tools:
echo   analyze_windows.bat       - Data analysis script
echo.
echo Documentation:
echo   README_windows.md         - Windows-specific documentation
echo   requirements_windows.txt  - Python dependencies
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo.
echo 1. Download Speedtest CLI:
echo    https://www.speedtest.net/apps/cli
echo.
echo 2. Install ^(run as administrator^):
echo    install_windows.bat
echo.
echo 3. Use desktop shortcuts or:
echo    python network_monitor_windows.py --single
echo    python dashboard_windows.py
echo.

pause