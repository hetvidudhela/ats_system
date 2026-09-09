@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo       ATS Resume Analyzer - Stopping Services
echo ===================================================
echo.

:: 1. Close the dedicated cmd launcher windows by title
echo Stopping ATS command windows...
taskkill /FI "WINDOWTITLE eq ATS FastAPI Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq ATS Flutter Web (Chrome)*" /T /F >nul 2>&1

:: 2. Terminate the backend process specifically bound to port 8000
echo Checking port 8000 (FastAPI)...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr /c:":8000 " ^| findstr "LISTENING"') do (
    echo Stopping backend process with PID %%a...
    taskkill /F /T /PID %%a >nul 2>&1
)

echo.
echo ===================================================
echo   ATS services stopped successfully.
echo ===================================================
echo.
