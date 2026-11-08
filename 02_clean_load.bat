@echo off
REM 02_clean_load.bat - son snapshotu temizleyir ve Oracle-a yukleyir (Addim 2)
chcp 65001 >nul
REM Python cixisini UTF-8 edir (Azerbaycan herfleri log fayllarinda pozulmasin)
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist logs mkdir logs
.venv\Scripts\python.exe src\clean.py > logs\clean.log 2>&1
type logs\clean.log
REM --reload: eyni snapshot yeniden temizlenibse, bazadaki kohne setirler evez olunur (tekrar sayilmir)
.venv\Scripts\python.exe src\load_oracle.py --reload > logs\load.log 2>&1
type logs\load.log
pause
