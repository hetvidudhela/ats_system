@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo       ATS Resume Analyzer - One-Click Launcher
echo ===================================================
echo.

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: 1. Verify Prerequisites
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found in your PATH. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

where flutter >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Flutter was not found in your PATH. Please install Flutter SDK and add it to PATH.
    pause
    exit /b 1
)

:: 2. Safely clean stale Flutter build artifacts (fixes Windows/OneDrive build\flutter_assets locks)
echo Cleaning stale Flutter build artifacts...

:: Strip read-only, system, and hidden attributes from build and ephemeral directories
if exist "flutter_app\build" (
    attrib -r -s -h /s /d "flutter_app\build\*" >nul 2>&1
)
if exist "flutter_app\ios\Flutter\ephemeral" (
    attrib -r -s -h /s /d "flutter_app\ios\Flutter\ephemeral\*" >nul 2>&1
)
if exist "flutter_app\macos\Flutter\ephemeral" (
    attrib -r -s -h /s /d "flutter_app\macos\Flutter\ephemeral\*" >nul 2>&1
)
if exist "flutter_app\windows\flutter\ephemeral" (
    attrib -r -s -h /s /d "flutter_app\windows\flutter\ephemeral\*" >nul 2>&1
)
if exist "flutter_app\linux\flutter\ephemeral" (
    attrib -r -s -h /s /d "flutter_app\linux\flutter\ephemeral\*" >nul 2>&1
)

:: Run flutter clean to reset generated artifacts
pushd "%ROOT_DIR%flutter_app"
call flutter clean >nul 2>&1
popd

:: Safely remove any remaining generated build and ephemeral artifacts if locked
if exist "flutter_app\build" (
    attrib -r -s -h /s /d "flutter_app\build\*" >nul 2>&1
    rd /s /q "flutter_app\build" >nul 2>&1
)
if exist "flutter_app\build\flutter_assets" (
    attrib -r -s -h /s /d "flutter_app\build\flutter_assets\*" >nul 2>&1
    rd /s /q "flutter_app\build\flutter_assets" >nul 2>&1
)
if exist "flutter_app\ios\Flutter\ephemeral" (
    rd /s /q "flutter_app\ios\Flutter\ephemeral" >nul 2>&1
)
if exist "flutter_app\macos\Flutter\ephemeral" (
    rd /s /q "flutter_app\macos\Flutter\ephemeral" >nul 2>&1
)
if exist "flutter_app\windows\flutter\ephemeral" (
    rd /s /q "flutter_app\windows\flutter\ephemeral" >nul 2>&1
)
if exist "flutter_app\linux\flutter\ephemeral" (
    rd /s /q "flutter_app\linux\flutter\ephemeral" >nul 2>&1
)

:: Resolve Flutter dependencies cleanly before launch
pushd "%ROOT_DIR%flutter_app"
call flutter pub get >nul 2>&1
popd

:: 3. Launch Backend in separate titled window
echo [1/2] Launching FastAPI backend on http://127.0.0.1:8000 ...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr /c:":8000 " ^| findstr "LISTENING"') do (
    taskkill /F /T /PID %%a >nul 2>&1
)
start "ATS FastAPI Backend" cmd /k "cd /d ""%ROOT_DIR%backend"" && echo Starting FastAPI Backend on http://127.0.0.1:8000... && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: 4. Brief delay to allow backend startup
ping 127.0.0.1 -n 3 >nul 2>&1

:: 5. Launch Flutter Web in Chrome in separate titled window
echo [2/2] Launching Flutter Web in Chrome ...
start "ATS Flutter Web (Chrome)" cmd /k "cd /d ""%ROOT_DIR%flutter_app"" && echo Starting Flutter Web on Chrome... && flutter run -d chrome"

echo.
echo ===================================================
echo       ATS System successfully started!
echo ===================================================
echo  - Backend:      http://127.0.0.1:8000
echo  - Swagger Docs: http://127.0.0.1:8000/docs
echo  - Health Check: http://127.0.0.1:8000/health/
echo  - Frontend:     Google Chrome (auto-opening)
echo.
echo  To cleanly stop all services, run: stop_project.bat
echo ===================================================
echo.
