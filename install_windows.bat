@echo off
REM Network Monitor Windows Installation Script
REM This script sets up the network monitoring application on Windows

echo ========================================
echo Network Monitor Windows Installation
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires administrator privileges.
    echo Please run as administrator.
    pause
    exit /b 1
)

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.7+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

REM Check if Speedtest CLI is installed
echo Checking Speedtest CLI...
speedtest --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Speedtest CLI not found.
    echo.
    echo Please download and install Speedtest CLI from:
    echo https://www.speedtest.net/apps/cli
    echo.
    echo After installation, make sure 'speedtest.exe' is in your PATH
    echo or place it in the same directory as this script.
    pause
    exit /b 1
)

echo Speedtest CLI found.

REM Install Python dependencies
echo.
echo Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install pandas matplotlib seaborn numpy

if %errorlevel% neq 0 (
    echo Failed to install Python dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

REM Create application directory
set "INSTALL_DIR=%ProgramFiles%\NetworkMonitor"
echo.
echo Creating application directory: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy Python script
echo Copying application files...
copy "network_monitor_windows.py" "%INSTALL_DIR%\network_monitor.py" >nul
copy "dashboard.py" "%INSTALL_DIR%\dashboard.py" >nul
copy "visualize.py" "%INSTALL_DIR%\visualize.py" >nul

REM Create Windows service script
echo Creating Windows service scripts...

REM Create service installation script
(
echo @echo off
echo REM Install Network Monitor as Windows Service
echo.
echo set "SERVICE_NAME=NetworkMonitor"
echo set "SERVICE_DISPLAY=Network Monitor Service"
echo set "SERVICE_DESC=Monitors internet speed and latency"
echo set "PYTHON_PATH=%INSTALL_DIR%\network_monitor.py"
echo.
echo echo Installing Network Monitor as Windows Service...
echo.
echo REM Create service using SC command
echo sc create "%%SERVICE_NAME%%" binPath= "python \"%%PYTHON_PATH%%\" --interval 10" DisplayName= "%%SERVICE_DISPLAY%%" start= auto
echo.
echo if %%errorlevel%% equ 0 ^(
echo     echo Service installed successfully.
echo     echo Starting service...
echo     sc start "%%SERVICE_NAME%%"
echo     echo.
echo     echo Service commands:
echo     echo   Start:   sc start "%%SERVICE_NAME%%"
echo     echo   Stop:    sc stop "%%SERVICE_NAME%%"
echo     echo   Status:  sc query "%%SERVICE_NAME%%"
echo     echo   Remove:  sc delete "%%SERVICE_NAME%%"
echo ^) else ^(
echo     echo Failed to install service.
echo     echo You can run the monitor manually with:
echo     echo   python "%INSTALL_DIR%\network_monitor.py"
echo ^)
echo.
echo pause
) > "%INSTALL_DIR%\install_service.bat"

REM Create manual run script
(
echo @echo off
echo REM Run Network Monitor manually
echo.
echo echo Starting Network Monitor...
echo echo Press Ctrl+C to stop
echo.
echo python "%INSTALL_DIR%\network_monitor.py"
echo.
echo pause
) > "%INSTALL_DIR%\run_monitor.bat"

REM Create dashboard script
(
echo @echo off
echo REM Start Network Monitor Web Dashboard
echo.
echo echo Starting Network Monitor Dashboard...
echo echo Open your browser to: http://localhost:8080
echo echo Press Ctrl+C to stop
echo.
echo python "%INSTALL_DIR%\dashboard.py"
echo.
echo pause
) > "%INSTALL_DIR%\start_dashboard.bat"

REM Create analysis script
(
echo @echo off
echo REM Analyze Network Monitor Data
echo.
echo python "%INSTALL_DIR%\visualize.py" --output-dir "%%USERPROFILE%%\Documents\NetworkMonitor_Reports"
echo.
echo echo Charts saved to: %%USERPROFILE%%\Documents\NetworkMonitor_Reports
echo echo.
echo pause
) > "%INSTALL_DIR%\analyze_data.bat"

REM Create desktop shortcuts
echo Creating desktop shortcuts...

REM Create shortcut for manual run
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%PUBLIC%\Desktop\Network Monitor.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\run_monitor.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = 'shell32.dll,14'; $Shortcut.Save()"

REM Create shortcut for dashboard
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%PUBLIC%\Desktop\Network Monitor Dashboard.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\start_dashboard.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = 'shell32.dll,220'; $Shortcut.Save()"

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo Installation directory: %INSTALL_DIR%
echo Data will be stored in: %%USERPROFILE%%\AppData\Local\NetworkMonitor
echo.
echo Available options:
echo.
echo 1. Install as Windows Service (recommended):
echo    Run: %INSTALL_DIR%\install_service.bat
echo.
echo 2. Run manually:
echo    Double-click "Network Monitor" desktop shortcut
echo    Or run: %INSTALL_DIR%\run_monitor.bat
echo.
echo 3. Web Dashboard:
echo    Double-click "Network Monitor Dashboard" desktop shortcut
echo    Or run: %INSTALL_DIR%\start_dashboard.bat
echo.
echo 4. Generate Charts:
echo    Run: %INSTALL_DIR%\analyze_data.bat
echo.
echo Data files location:
echo   Speed tests: %%USERPROFILE%%\AppData\Local\NetworkMonitor\data\speed_tests.csv
echo   Ping tests:  %%USERPROFILE%%\AppData\Local\NetworkMonitor\data\ping_tests.csv
echo   Logs:        %%USERPROFILE%%\AppData\Local\NetworkMonitor\logs\network_monitor.log
echo.

pause