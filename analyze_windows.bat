@echo off
REM Network Monitor Windows Data Analysis Script
REM This script provides basic analysis of collected network monitoring data

echo ========================================
echo Network Monitor Data Analysis
echo ========================================
echo.

REM Set data directory
set "DATA_DIR=%USERPROFILE%\AppData\Local\NetworkMonitor\data"
set "SPEED_CSV=%DATA_DIR%\speed_tests.csv"
set "PING_CSV=%DATA_DIR%\ping_tests.csv"

REM Check if data directory exists
if not exist "%DATA_DIR%" (
    echo Data directory not found: %DATA_DIR%
    echo Make sure the network monitor has run at least once.
    pause
    exit /b 1
)

echo Data directory: %DATA_DIR%
echo.

REM Speed test analysis
if exist "%SPEED_CSV%" (
    echo Speed Test Analysis:
    echo ====================

    REM Count lines (subtract 1 for header)
    for /f %%i in ('type "%SPEED_CSV%" ^| find /c /v ""') do set /a "SPEED_TESTS=%%i-1"
    echo Total speed tests: %SPEED_TESTS%

    if %SPEED_TESTS% gtr 0 (
        echo.
        echo Latest test:
        for /f "skip=1 tokens=1-8 delims=," %%a in ('type "%SPEED_CSV%"') do (
            set "LATEST_TIME=%%a"
            set "LATEST_DOWN=%%b"
            set "LATEST_UP=%%c"
            set "LATEST_PING=%%d"
            set "LATEST_SERVER=%%e"
            set "LATEST_LOCATION=%%f"
            set "LATEST_ISP=%%g"
        )
        echo   Date/Time: %LATEST_TIME%
        echo   Download: %LATEST_DOWN% Mbps
        echo   Upload: %LATEST_UP% Mbps
        echo   Ping: %LATEST_PING% ms
        echo   Server: %LATEST_SERVER% ^(%LATEST_LOCATION%^)
        echo   ISP: %LATEST_ISP%

        echo.
        echo Recent Tests ^(last 10^):
        echo   Date/Time                Download    Upload     Ping
        echo   --------------------------------------------------------

        REM Show last 10 tests (this is a simplified version)
        for /f "skip=1 tokens=1-4 delims=," %%a in ('type "%SPEED_CSV%"') do (
            set "TEST_TIME=%%a"
            set "TEST_DOWN=%%b"
            set "TEST_UP=%%c"
            set "TEST_PING=%%d"

            REM Extract just date and time part
            for /f "tokens=1,2 delims=T" %%x in ("!TEST_TIME!") do (
                set "DATE_PART=%%x"
                for /f "tokens=1 delims=." %%z in ("%%y") do set "TIME_PART=%%z"
            )

            call echo   !DATE_PART! !TIME_PART!    !TEST_DOWN!      !TEST_UP!     !TEST_PING!
        )
    ) else (
        echo No speed test data available yet.
    )
) else (
    echo Speed test file not found: %SPEED_CSV%
)

echo.

REM Ping test analysis
if exist "%PING_CSV%" (
    echo Ping Test Analysis:
    echo ==================

    REM Count lines (subtract 1 for header)
    for /f %%i in ('type "%PING_CSV%" ^| find /c /v ""') do set /a "PING_TESTS=%%i-1"
    echo Total ping tests: %PING_TESTS%

    if %PING_TESTS% gtr 0 (
        echo.
        echo Latest ping results by target:

        REM This is a simplified analysis - for full analysis, use Python script
        for /f "skip=1 tokens=2,3,6 delims=," %%a in ('type "%PING_CSV%"') do (
            echo   %%a: %%b ms ^(loss: %%c%%^)
        )
    ) else (
        echo No ping test data available yet.
    )
) else (
    echo Ping test file not found: %PING_CSV%
)

echo.
echo ========================================
echo Data Files:
echo ========================================
echo Speed tests: %SPEED_CSV%
echo Ping tests:  %PING_CSV%

if exist "%SPEED_CSV%" (
    for %%a in ("%SPEED_CSV%") do echo Speed test file size: %%~za bytes
)

if exist "%PING_CSV%" (
    for %%a in ("%PING_CSV%") do echo Ping test file size: %%~za bytes
)

echo.
echo Commands:
echo - Run single test: python "%ProgramFiles%\NetworkMonitor\network_monitor.py" --single
echo - Start dashboard: python "%ProgramFiles%\NetworkMonitor\dashboard.py"
echo - Generate charts: python "%ProgramFiles%\NetworkMonitor\visualize.py"

echo.
pause