@echo off
echo Revizto Data Exporter - Project Management Integration
echo ===================================================
echo.

REM Check if the executable exists
if not exist "ReviztoDataExporter.exe" (
    echo ERROR: ReviztoDataExporter.exe not found in current directory
    echo Please ensure all files are extracted to the same folder
    pause
    exit /b 1
)

REM Check if configuration exists
if not exist "appsettings.json" (
    echo ERROR: appsettings.json not found
    echo Please ensure the configuration file is in the same folder
    pause
    exit /b 1
)

echo Starting Revizto Data Exporter...
echo.
echo Options:
echo   1. GUI Mode (Interactive)
echo   2. Console Mode (Export All Projects)
echo   3. Exit
echo.
set /p choice="Select option (1-3): "

if "%choice%"=="1" (
    echo Starting GUI mode...
    ReviztoDataExporter.exe
) else if "%choice%"=="2" (
    echo Starting console mode - exporting all projects...
    ReviztoDataExporter.exe --console
) else if "%choice%"=="3" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice. Starting GUI mode by default...
    ReviztoDataExporter.exe
)

echo.
echo Export completed. Check the logs folder for details.
pause