@echo off
REM 05_reprocess.bat - BUTUN snapshotlari yeniden emal edir (bina.az-dan yeniden toplamadan).
REM Ne vaxt lazimdir: temizleme qaydasi (clean.py) ve ya view-lar (02_views.sql) deyisende.
REM Addimlar: temizleme (hamisi) -> Oracle (hamisi, yeniden) -> maas -> ixrac -> SQL yoxlamasi -> sayt (GitHub)
REM Netice: logs\reprocess.log
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist logs mkdir logs
set LOG=logs\reprocess.log
echo ==== %date% %time% yeniden emal basladi ==== >> %LOG%

REM 1) Butun xam snapshotlar eyni qaydalarla yeniden temizlenir
.venv\Scripts\python.exe src\clean.py --all >> %LOG% 2>&1
if errorlevel 1 goto :error
REM 2) Hamisi Oracle-a yeniden yazilir (--reload: kohne setirler silinib yenisi yazilir, tranzaksiya ile)
.venv\Scripts\python.exe src\load_oracle.py --all --reload >> %LOG% 2>&1
if errorlevel 1 goto :error
REM 3) Maas melumati (alinmasa, evvelki qalir)
.venv\Scripts\python.exe src\fetch_salary.py >> %LOG% 2>&1
.venv\Scripts\python.exe src\load_salary.py >> %LOG% 2>&1
REM 4) CSV ixraci (Power BI ve sayt ucun)
.venv\Scripts\python.exe src\export_data.py >> %LOG% 2>&1
if errorlevel 1 goto :error
REM 5) Mudafie sorgulari isleyirmi (yalniz yoxlama, xeta olsa dayanmir)
.venv\Scripts\python.exe src\db.py --selftest >> %LOG% 2>&1

REM ---- Sayti yenile: yeni CSV-leri GitHub-a gonder (run_pipeline.bat-daki ile eyni addimlar)
set GIT_TERMINAL_PROMPT=0
set GCM_INTERACTIVE=Never
where git >nul 2>&1
if errorlevel 1 (
  echo SAYT: git tapilmadi - sayt yenilenmedi >> %LOG%
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
git commit -q -m "Yeniden emal: butun snapshotlar yeni qaydalarla" >> %LOG% 2>&1
git pull -q --rebase --autostash origin main >> %LOG% 2>&1
git push -q origin main >> %LOG% 2>&1
if errorlevel 1 (
  echo SAYT XETA: GitHub-a gonderilmedi >> %LOG%
  goto :done
)
echo SAYT: yeni melumat GitHub-a gonderildi, sayt 1-2 deqiqeye yenilenecek >> %LOG%

:done
echo ==== %date% %time% ugurla bitdi ==== >> %LOG%
exit /b 0

:error
echo ==== %date% %time% XETA: yuxaridaki setirlere baxin ==== >> %LOG%
exit /b 1
