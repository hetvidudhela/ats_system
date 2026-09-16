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
for /f "tokens=5" %%a in ('netstat -ano -p tcp 2^>nul ^| findstr /c:":8000 " ^| findstr "LISTENING"') do (
    echo Stopping backend process with PID %%a...
    taskkill /F /T /PID %%a >nul 2>&1
)

:: 3. Terminate the frontend process specifically bound to port 57720
echo Checking port 57720 (Flutter Web)...
for /f "tokens=5" %%a in ('netstat -ano -p tcp 2^>nul ^| findstr /c:":57720 " ^| findstr "LISTENING"') do (
    echo Stopping Flutter Web process with PID %%a...
    taskkill /F /T /PID %%a >nul 2>&1
)

:: 4. Brief delay to allow socket cleanup
ping 127.0.0.1 -n 2 >nul 2>&1

:: 5. Verify ports are completely released
set "PORT_8000_FREE=1"
netstat -ano -p tcp 2>nul | findstr /c:":8000 " | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! equ 0 set "PORT_8000_FREE=0"

set "PORT_57720_FREE=1"
netstat -ano -p tcp 2>nul | findstr /c:":57720 " | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! equ 0 set "PORT_57720_FREE=0"

echo.
if "!PORT_8000_FREE!"=="1" (
    echo  - port 8000  -^> free
) else (
    echo  - port 8000  -^> STILL BUSY
)

if "!PORT_57720_FREE!"=="1" (
    echo  - port 57720 -^> free
) else (
    echo  - port 57720 -^> STILL BUSY
)

echo.
echo ===================================================
echo   ATS services stopped successfully.
echo ===================================================
echo.
