@echo off
REM setup_autoupdate.bat - hefelik avtomatik yenilemeni BIR DEFE qurur
REM 1) Bu qovlugu GitHub reposu ile elaqelendirir (fayllar deyismir)
REM 2) GitHub-a giris (brauzerde bir defe)
REM 3) Windows Task Scheduler-de "her bazar 12:00" tapsirigi yaradir
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\setup_autoupdate.ps1"
echo.
pause
