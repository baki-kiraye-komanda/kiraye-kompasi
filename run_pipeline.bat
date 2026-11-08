@echo off
REM run_pipeline.bat - butun hefelik yenileme: toplama -> temizleme -> Oracle -> maas -> ixrac
REM Windows Task Scheduler bu fayli hefede bir defe isledir. Pencere acmadan islemek ucun "pause" yoxdur.
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist logs mkdir logs
set LOG=logs\pipeline.log
echo ==== %date% %time% basladi ==== >> %LOG%

.venv\Scripts\python.exe src\scrape.py >> %LOG% 2>&1
if errorlevel 1 goto :error
.venv\Scripts\python.exe src\clean.py >> %LOG% 2>&1
if errorlevel 1 goto :error
.venv\Scripts\python.exe src\load_oracle.py >> %LOG% 2>&1
if errorlevel 1 goto :error
.venv\Scripts\python.exe src\fetch_salary.py >> %LOG% 2>&1
.venv\Scripts\python.exe src\load_salary.py >> %LOG% 2>&1
.venv\Scripts\python.exe src\export_data.py >> %LOG% 2>&1
if errorlevel 1 goto :error

echo ==== %date% %time% ugurla bitdi ==== >> %LOG%
exit /b 0

:error
REM Xeta olsa: evvelki CSV-ler deyismir, Power BI ve sayt kohne (amma duzgun) melumati gosterir
echo ==== %date% %time% XETA: yuxaridaki setirlere baxin ==== >> %LOG%
exit /b 1
