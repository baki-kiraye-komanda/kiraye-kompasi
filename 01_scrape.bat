@echo off
REM 01_scrape.bat - Addim 1: DSK maas cedvelini ve bina.az elanlarini toplayir
chcp 65001 >nul
REM Python cixisini UTF-8 edir (Azerbaycan herfleri log fayllarinda pozulmasin)
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist logs mkdir logs
echo [1/2] DSK maas cedveli...
.venv\Scripts\python.exe src\fetch_salary.py > logs\fetch_salary.log 2>&1
type logs\fetch_salary.log
echo [2/2] bina.az elanlari (15-20 deqiqe)...
.venv\Scripts\python.exe src\scrape.py
pause
