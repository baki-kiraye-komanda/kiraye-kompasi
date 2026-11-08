@echo off
REM ============================================================
REM setup.bat - Layihe muhitinin bir defelik qurulmasi (Addim 0)
REM 1) Virtual muhit (.venv) yaradir
REM 2) requirements.txt-deki paketleri qurur
REM 3) Oracle-da layihenin istifadecisini yaradir (lazim olsa)
REM 4) Butun aletleri yoxlayir -> logs\check_env.log
REM ============================================================
chcp 65001 >nul
REM Python cixisini UTF-8 edir (Azerbaycan herfleri log fayllarinda pozulmasin)
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist logs mkdir logs

if exist .env.txt goto envready
if not exist .env (
  copy env.example.txt .env >nul
  echo .env yaradildi. Notepad-da ORACLE_PASSWORD ve GEMINI_API_KEY-i doldurun, saxlayin ^(Ctrl+S^) ve Notepad-i baglayin.
  notepad .env
  echo Doldurub saxladiqdan sonra bu pencerede istenilen duymeni basin.
  pause >nul
)
:envready

echo [1/4] Virtual muhit yaradilir...
if not exist .venv\Scripts\python.exe (
  py -3.11 -m venv .venv 2>nul
  if not exist .venv\Scripts\python.exe py -3 -m venv .venv 2>nul
  if not exist .venv\Scripts\python.exe python -m venv .venv
)
if not exist .venv\Scripts\python.exe (
  echo XETA: Python tapilmadi. > logs\check_env.log
  echo XETA: Python tapilmadi.
  pause
  exit /b 1
)

echo [2/4] Paketler qurasdirilir (1-3 deqiqe)...
.venv\Scripts\python.exe -m pip install --upgrade pip > logs\setup_pip.log 2>&1
.venv\Scripts\python.exe -m pip install -r requirements.txt >> logs\setup_pip.log 2>&1

echo [3/4] Oracle istifadecisi yoxlanilir...
.venv\Scripts\python.exe src\create_db_user.py

echo [4/4] Muhit yoxlanilir...
.venv\Scripts\python.exe src\check_env.py

echo [+] DSK maas cedveli yuklenir...
.venv\Scripts\python.exe src\fetch_salary.py > logs\fetch_salary.log 2>&1
type logs\fetch_salary.log

echo.
echo Hazirdir. Bu pencereni baglaya bilersiniz.
pause
