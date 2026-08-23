@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
title PDF Magic App - Reset
cd /d "%~dp0"

echo.
echo   =========================================
echo       PDF Magic App - Reset
echo   =========================================
echo.
echo   WARNING: All data will be deleted!
echo   Project folders, database, settings.
echo   Libraries and venv are NOT touched.
echo.
echo   Make sure Flask is NOT running (close Launch window)!
echo.

set /p confirm="   Continue? (yes/no): "
if /i not "!confirm!"=="yes" (
    echo   Cancelled.
    pause
    exit /b 0
)

echo.

:: Kill any process on port 5000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    echo   Killing PID %%a on port 5000...
    taskkill /PID %%a /F >nul 2>&1
)

python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo   [X] Python not found!
    echo   Run Launch.bat first.
    pause
    exit /b 1
)

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python reset_project.py --force

echo.
echo   Reset complete.
pause
