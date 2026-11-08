@echo off
REM 03_salary.bat - DSK orta emek haqqi cedvelini yukleyir ve Oracle-a yazir
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist logs mkdir logs
.venv\Scripts\python.exe src\fetch_salary.py > logs\salary.log 2>&1
if exist src\load_salary.py .venv\Scripts\python.exe src\load_salary.py >> logs\salary.log 2>&1
type logs\salary.log
pause
