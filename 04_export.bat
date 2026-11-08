@echo off
REM 04_export.bat - Oracle view-larindan exports\ ve app\data\ qovluqlarina CSV ixrac edir
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
.venv\Scripts\python.exe src\export_data.py > logs\export.log 2>&1
type logs\export.log
pause
