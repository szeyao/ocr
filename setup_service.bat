@echo off
SET PROJ_DIR=%~dp0
cd /d "%PROJ_DIR%"
SET SERVICE_NAME=InvoiceProcessor

echo [1/4] Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed.
    pause
    exit /b
)

echo [2/4] Creating Virtual Environment...
if not exist ".venv" (
    python -m venv .venv
)
:: Small wait to ensure Windows folder creation is finished
timeout /t 2 >nul

echo [3/4] Installing Dependencies...
:: Using the absolute path to python.exe inside the venv is the safest way
"%PROJ_DIR%.venv\Scripts\python.exe" -m pip install --upgrade pip
"%PROJ_DIR%.venv\Scripts\python.exe" -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo !!!!!!!!! ERROR !!!!!!!!!
    echo Dependency installation failed. Check your internet or requirements.txt
    pause
    exit /b
)

echo [4/4] Configuring Windows Service...
:: Clean up old service first
"%PROJ_DIR%bin\nssm.exe" stop %SERVICE_NAME% >nul 2>&1
"%PROJ_DIR%bin\nssm.exe" remove %SERVICE_NAME% confirm >nul 2>&1

:: Install Service
"%PROJ_DIR%bin\nssm.exe" install %SERVICE_NAME% "%PROJ_DIR%.venv\Scripts\python.exe" "\"%PROJ_DIR%api.py\""
"%PROJ_DIR%bin\nssm.exe" set %SERVICE_NAME% AppDirectory "%PROJ_DIR%\"
"%PROJ_DIR%bin\nssm.exe" set %SERVICE_NAME% AppStdout "%PROJ_DIR%log.txt"
"%PROJ_DIR%bin\nssm.exe" set %SERVICE_NAME% AppStderr "%PROJ_DIR%log.txt"

:: AUTO-RESTART LOGIC (This fixes your Task Manager kill issue)
"%PROJ_DIR%bin\nssm.exe" set %SERVICE_NAME% AppExit Default Restart
"%PROJ_DIR%bin\nssm.exe" set %SERVICE_NAME% AppRestartDelay 2000

echo [SUCCESS] Starting the service...
"%PROJ_DIR%bin\nssm.exe" start %SERVICE_NAME%

echo ---------------------------------------------------
echo API is now running as a background service!
echo Access it at: http://localhost:8000/docs
echo ---------------------------------------------------
echo.
echo If the link above doesn't work, check log.txt for errors.
pause