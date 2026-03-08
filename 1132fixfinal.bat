@echo off
chcp 65001 >nul
color 0f
setlocal enabledelayedexpansion

:: --- PIXEL-PERFECT BLOCK HEADER ---
cls
echo ###############################################################
echo #                                                             #
echo #  M   M  EEEEE  L      BBBB   SSSSS  L       AAA   M   M     #
echo #  MM MM  E      L      B   B  S      L      A   A  MM MM     #
echo #  M M M  EEE    L      BBBB    SSS   L      AAAAA  M M M     #
echo #  M   M  E      L      B   B      S  L      A   A  M   M     #
echo #  M   M  EEEEE  LLLLL  BBBB   SSSSS  LLLLL  A   A  M   M     #
echo #                                                             #
echo #              AUTHOR: MELB SLAM ^| VERSION: 1132             #
echo #           WINDOWS 11 ZOOM SANDBOX OVERRIDE v2.0             #
echo ###############################################################
echo.

:: --- CONFIGURATION ---
set "targetUser=testuser69"
set "password=mickszoomhack"
set "psexecPath=C:\Windows\System32\PsExec.exe"
set "zoomDestExe=C:\ZoomPortable\bin\Zoom.exe"
set "logFile=C:\ZoomSetup.log"

net session >nul 2>&1 || (echo [ERROR] Run as Admin & pause & exit /b 1)

:: Initial Cleanup
echo [STEP 1/3] Preparing clean environment...
call :nuclearCleanup

echo [STEP 2/3] Setting up sandbox user...
echo [%date% %time%] Creating sandbox... >> "%logFile%"
net user %targetUser% %password% /add >nul 2>&1
net localgroup administrators %targetUser% /add >nul 2>&1

if exist "%psexecPath%" (
    echo [STEP 3/3] Launching Zoom...
    "%psexecPath%" -accepteula -u %targetUser% -p %password% -i -d "%zoomDestExe%" --darkmode
) else (
    echo [ERROR] PsExec missing at %psexecPath%
    pause & exit /b 1
)

color ff
echo.
echo ---------------------------------------------------------------
echo [MONITORING] Zoom is currently active as %targetUser%.
echo [MONITORING] Waiting for Zoom to close to begin auto-wipe...
echo ---------------------------------------------------------------

color 0D
:monitor
timeout /t 5 /nobreak >nul
tasklist /FI "USERNAME eq %targetUser%" /FI "IMAGENAME eq Zoom.exe" | find /i "Zoom.exe" >nul
if %errorlevel%==0 goto :monitor

echo.
echo [!] Zoom closure detected.
echo [!] Starting Secure Data Wipe...
timeout /t 3 >nul

call :nuclearCleanup

echo [PROGRESS] Clearing Recent Files trace...
del /f /q /s "%AppData%\Microsoft\Windows\Recent\*.*" >nul 2>&1

echo [%date% %time%] Cleanup Complete. >> "%logFile%"
echo.
echo ###############################################################
echo #          SUCCESS: SYSTEM IS NOW CLEAN AND SECURE            #
echo ###############################################################
timeout /t 5 >nul
exit /b

:: --- THE NUCLEAR CLEANUP BLOCK ---
:nuclearCleanup
echo [PROGRESS] Suspending Windows locking services...
net stop WSearch >nul 2>&1
net stop AeLookupSvc >nul 2>&1

echo [PROGRESS] Terminating lingering processes...
taskkill /F /FI "USERNAME eq %targetUser%" /T >nul 2>&1

echo [PROGRESS] Deleting sandbox user account...
net user %targetUser% /delete >nul 2>&1

echo [PROGRESS] Scrubbing Registry Profile headers...
for /f "tokens=*" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList" /s /f "%targetUser%" ^| findstr "HKEY_LOCAL_MACHINE"') do (
    reg delete "%%a" /f >nul 2>&1
)

echo [PROGRESS] Force-purging leftover profile folders...
for /d %%G in ("C:\Users\%targetUser%*") do (
    takeown /f "%%G" /r /d y >nul 2>&1
    icacls "%%G" /grant administrators:F /t /l /q >nul 2>&1
    attrib -h -r -s "%%G" /s /d >nul 2>&1
    rd /s /q "%%G" >nul 2>&1
    if exist "%%G" move "%%G" "%temp%\zombie_%random%" >nul 2>&1
)

echo [PROGRESS] Resuming system services...
net start WSearch >nul 2>&1
net start AeLookupSvc >nul 2>&1
ipconfig /flushdns >nul
echo [DONE] Environment reset.
echo.
exit /b