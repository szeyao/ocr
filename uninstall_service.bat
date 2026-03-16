@echo off
SET PROJ_DIR=%~dp0
cd /d "%PROJ_DIR%"
SET SERVICE_NAME=InvoiceProcessor

echo [1/3] Force-killing Service and Subprocesses...

:: 1. Specifically find the PID for this service
set "SERVICE_PID="
for /f "tokens=3" %%a in ('sc queryex %SERVICE_NAME% ^| findstr "PID"') do (
    set SERVICE_PID=%%a
)

:: 2. Kill the PID if it exists and isn't 0
if defined SERVICE_PID (
    if not "%SERVICE_PID%"=="0" (
        echo [INFO] Found Zombie PID: %SERVICE_PID%. Killing process tree...
        taskkill /F /T /PID %SERVICE_PID% >nul 2>&1
    )
)

:: 3. Kill any other python processes just in case
taskkill /F /IM python.exe /T >nul 2>&1

echo [2/3] Removing Service Entry...
:: Use NSSM to stop/remove
"%PROJ_DIR%bin\nssm.exe" stop %SERVICE_NAME% >nul 2>&1
"%PROJ_DIR%bin\nssm.exe" remove %SERVICE_NAME% confirm >nul 2>&1

:: The "Nuclear Option" for the Service Database
sc stop %SERVICE_NAME% >nul 2>&1
sc delete %SERVICE_NAME% >nul 2>&1

echo [3/3] Cleaning up Files...
:: Wait for Windows to release the file handle on log.txt
timeout /t 5 >nul

if exist "log.txt" (
    del /f /q "log.txt"
)

:: Re-check if log.txt still exists (if it does, it's still locked)
if exist "log.txt" (
    echo [ERROR] log.txt is STILL locked. 
    echo Closing any open Notepads or Editors...
    taskkill /F /IM notepad.exe /T >nul 2>&1
    del /f /q "log.txt" >nul 2>&1
)

echo.
echo ---------------------------------------------------
echo Uninstall Complete. 
echo Verify with: sc query %SERVICE_NAME%
echo ---------------------------------------------------
pause