@echo off
REM run_pipeline.bat - butun hefelik yenileme: toplama -> temizleme -> Oracle -> maas -> ixrac -> sayt
REM Windows Task Scheduler bu fayli hefede bir defe isledir (setup_autoupdate.bat qurur).
REM Pencere acmadan islemek ucun "pause" yoxdur. Netice: logs\pipeline.log
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist logs mkdir logs
set LOG=logs\pipeline.log
echo ==== %date% %time% basladi ==== >> %LOG%

REM scrape.py elanlarin 95%%-den azini toplasa xeta qaytarir - yarimciq melumat istifade olunmur
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

REM ---- Sayti yenile: yeni CSV-leri GitHub-a gonder (Streamlit Cloud 1-2 deqiqeye ozu yenilenir)
REM Sual vermesin (gizli pencerede gozleyib qalmasin)
set GIT_TERMINAL_PROMPT=0
set GCM_INTERACTIVE=Never
where git >nul 2>&1
if errorlevel 1 (
  echo SAYT: git tapilmadi - sayt yenilenmedi, setup_autoupdate.bat-a baxin >> %LOG%
  goto :done
)
if not exist .git (
  echo SAYT: qovluq GitHub-a bagli deyil - setup_autoupdate.bat isledin >> %LOG%
  goto :done
)
git add app/data exports >> %LOG% 2>&1
git diff --cached --quiet
if not errorlevel 1 (
  echo SAYT: melumat deyismeyib, gondermeye ehtiyac yoxdur >> %LOG%
  goto :done
)
git commit -q -m "Heftelik yenileme: yeni bina.az melumati" >> %LOG% 2>&1
git pull -q --rebase --autostash origin main >> %LOG% 2>&1
git push -q origin main >> %LOG% 2>&1
if errorlevel 1 (
  echo SAYT XETA: GitHub-a gonderilmedi - giris muddeti bitib ola biler, setup_autoupdate.bat-i yeniden isledin >> %LOG%
  goto :done
)
echo SAYT: yeni melumat GitHub-a gonderildi, sayt 1-2 deqiqeye yenilenecek >> %LOG%

:done
echo ==== %date% %time% ugurla bitdi ==== >> %LOG%
exit /b 0

:error
REM Xeta olsa: evvelki CSV-ler deyismir, Power BI ve sayt kohne (amma duzgun) melumati gosterir
echo ==== %date% %time% XETA: yuxaridaki setirlere baxin ==== >> %LOG%
exit /b 1
