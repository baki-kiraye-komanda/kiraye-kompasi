@echo off
REM run_site.bat - saytı kompüterdə açır: http://localhost:8501
REM Bağlamaq üçün bu pəncərəni bağlayın.
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0app"
"..\.venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
