@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
title PDF Magic App
cd /d "%~dp0"

echo.
echo   =========================================
echo          PDF Magic App - Launch
echo   =========================================
echo.

where uv >nul 2>&1
if !errorlevel! neq 0 (
    echo   [..] uv not found - installing...
    winget install --id astral-sh.uv --silent --accept-package-agreements --accept-source-agreements 2>nul
    if !errorlevel! neq 0 (
        powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex" 2>nul
    )
    set "PATH=!USERPROFILE!\.cargo\bin;!PATH!"
    where uv >nul 2>&1
    if !errorlevel! neq 0 (
        echo   [X] Failed to install uv.
        pause
        exit /b 1
    )
)
echo   [OK] uv ready

python --version >nul 2>&1
if !errorlevel! equ 0 (
    echo   [OK] System Python found
) else (
    echo   [..] Installing Python 3.12 via uv...
    uv python install 3.12
    if !errorlevel! neq 0 (
        echo   [X] Failed to install Python.
        pause
        exit /b 1
    )
    echo   [OK] Python 3.12 installed
)

if not exist ".venv\Scripts\python.exe" (
    echo   [..] Creating .venv...
    uv venv
    if !errorlevel! neq 0 (
        echo   [X] Failed to create .venv
        pause
        exit /b 1
    )
    echo   [OK] .venv created
) else (
    echo   [OK] .venv found
)
call .venv\Scripts\activate.bat

echo   [..] Installing dependencies...
uv pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo   [X] Failed to install dependencies
    pause
    exit /b 1
)
echo   [OK] Dependencies installed

java -version >nul 2>&1
if !errorlevel! equ 0 (
    echo   [OK] Java found
) else (
    echo   [!] Java not found - PDF converter will not work
)

echo.
echo   =========================================
echo     Launching app... http://localhost:5000
echo   =========================================
echo.
echo   Close this window to exit.
echo.
python run.py
pause
