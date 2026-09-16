@echo off
setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo ===================================================
echo       ATS Resume Analyzer - One-Click Launcher
echo ===================================================
echo.
echo Starting ATS Resume Analyzer...
echo.

:: 1. Verify Prerequisites
echo Checking Python...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found in PATH.
    echo Please install Python 3.10+ and ensure "Add python.exe to PATH" is checked.
    pause
    exit /b 1
)

echo Checking Flutter...
where flutter >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Flutter was not found in PATH.
    echo Please install Flutter SDK and add its bin folder to PATH.
    pause
    exit /b 1
)

echo Checking Chrome...
set "CHROME_FOUND=0"
where chrome >nul 2>&1 && set "CHROME_FOUND=1"
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME_FOUND=1"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_FOUND=1"
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME_FOUND=1"
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" >nul 2>&1 && set "CHROME_FOUND=1"
reg query "HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" >nul 2>&1 && set "CHROME_FOUND=1"

if "!CHROME_FOUND!"=="0" (
    echo [WARNING] Google Chrome was not detected in standard installation paths.
    echo Flutter Web and the ATS Chrome Extension require Google Chrome.
)

:: 2. Stop stale processes on project ports (8000 and 57720)
echo.
echo Cleaning stale project ports...
taskkill /FI "WINDOWTITLE eq ATS FastAPI Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq ATS Flutter Web (Chrome)*" /T /F >nul 2>&1

for /f "tokens=5" %%a in ('netstat -ano -p tcp 2^>nul ^| findstr /c:":8000 " ^| findstr "LISTENING"') do (
    taskkill /F /T /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano -p tcp 2^>nul ^| findstr /c:":57720 " ^| findstr "LISTENING"') do (
    taskkill /F /T /PID %%a >nul 2>&1
)

:: 3. Safe cleanup of ephemeral file locks on Windows if present
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

:: 4. Resolve Python environment & dependencies
set "PYTHON_CMD=python"
if exist "%ROOT_DIR%backend\.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%ROOT_DIR%backend\.venv\Scripts\python.exe"
) else if exist "%ROOT_DIR%.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%ROOT_DIR%.venv\Scripts\python.exe"
)

"!PYTHON_CMD!" -c "import fastapi, uvicorn" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo Setting up backend virtual environment...
    if not exist "%ROOT_DIR%backend\.venv" (
        python -m venv "%ROOT_DIR%backend\.venv"
    )
    set "PYTHON_CMD=%ROOT_DIR%backend\.venv\Scripts\python.exe"
    echo Installing backend dependencies...
    "!PYTHON_CMD!" -m pip install -r "%ROOT_DIR%backend\requirements.txt"
)

:: 5. Resolve Flutter dependencies only if not already resolved
if not exist "%ROOT_DIR%flutter_app\.dart_tool\package_config.json" (
    echo Resolving Flutter dependencies...
    pushd "%ROOT_DIR%flutter_app"
    call flutter pub get >nul 2>&1
    popd
)

:: 6. Launch FastAPI backend in dedicated window
echo.
echo Starting FastAPI...
start "ATS FastAPI Backend" cmd /k "cd /d ""%ROOT_DIR%backend"" && echo Starting FastAPI Backend on http://127.0.0.1:8000... && ""!PYTHON_CMD!"" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: 7. Actively poll backend health until HTTP 200 is confirmed
echo Waiting for backend...
set "BACKEND_READY=0"
for /l %%i in (1,1,30) do (
    if "!BACKEND_READY!"=="0" (
        powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health/' -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
        if !ERRORLEVEL! equ 0 (
            set "BACKEND_READY=1"
        ) else (
            ping 127.0.0.1 -n 2 >nul 2>&1
        )
    )
)

if "!BACKEND_READY!"=="0" (
    echo [ERROR] FastAPI backend did not respond on http://127.0.0.1:8000/health/ within 30 seconds.
    echo Please inspect the "ATS FastAPI Backend" window for details.
    pause
    exit /b 1
)

echo.
echo Backend ready on:
echo http://127.0.0.1:8000

:: 8. Launch Flutter Web explicitly on port 57720
echo.
echo Starting Flutter Web...
start "ATS Flutter Web (Chrome)" cmd /k "cd /d ""%ROOT_DIR%flutter_app"" && echo Starting Flutter Web on Chrome (port 57720)... && flutter run -d chrome --web-port 57720"

:: 9. Actively poll until port 57720 is listening
set "FLUTTER_READY=0"
for /l %%i in (1,1,60) do (
    if "!FLUTTER_READY!"=="0" (
        netstat -ano -p tcp 2>nul | findstr /c:":57720 " | findstr "LISTENING" >nul 2>&1
        if !ERRORLEVEL! equ 0 (
            set "FLUTTER_READY=1"
        ) else (
            ping 127.0.0.1 -n 2 >nul 2>&1
        )
    )
)

if not "!FLUTTER_READY!"=="1" (
    echo [ERROR] Flutter Web did not start listening on port 57720 within 60 seconds.
    echo Please inspect the "ATS Flutter Web (Chrome)" window for build/compilation errors.
    pause
    exit /b 1
)

echo.
echo Flutter ready on:
echo http://localhost:57720/

echo.
echo Opening ATS Analyzer...
echo DONE.

echo.
echo ===================================================
echo       ATS Resume Analyzer - ALL SERVICES READY
echo ===================================================
echo  - Backend API:    http://127.0.0.1:8000
echo  - Swagger Docs:   http://127.0.0.1:8000/docs
echo  - Health Check:   http://127.0.0.1:8000/health/
echo  - Flutter Web:    http://localhost:57720/
echo  - Chrome Ext:     Load unpacked from extension\ folder
echo.
echo  The ATS Analyzer extension can now be clicked in Chrome
echo  and will open http://localhost:57720/ seamlessly.
echo.
echo  To stop all services cleanly:
echo    - Press any key below, OR
echo    - Run stop_project.bat
echo ===================================================
echo.
echo Press any key to stop all ATS services...
pause >nul
call "%ROOT_DIR%stop_project.bat"
