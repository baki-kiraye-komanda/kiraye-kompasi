@echo off
REM 05_reprocess.bat - yeniden toplamadan (scrape olmadan) son snapshotu yeniden emal edir:
REM temizleme -> Oracle (--reload) -> ixrac. Temizleme qaydasi deyisende istifade olunur.
REM Netice: logs\reprocess.log. Pencere ozu baglanir.
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist logs mkdir logs
set LOG=logs\reprocess.log
echo ==== %date% %time% basladi ==== > %LOG%
.venv\Scripts\python.exe src\clean.py >> %LOG% 2>&1
if errorlevel 1 goto :error
.venv\Scripts\python.exe src\load_oracle.py --reload >> %LOG% 2>&1
if errorlevel 1 goto :error
.venv\Scripts\python.exe src\export_data.py >> %LOG% 2>&1
if errorlevel 1 goto :error
echo ==== %date% %time% ugurla bitdi ==== >> %LOG%
exit /b 0
:error
echo ==== %date% %time% XETA: yuxaridaki setirlere baxin ==== >> %LOG%
exit /b 1
