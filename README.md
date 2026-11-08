# Kirayə Kompası — Bakıda kirayə: maaş nəyə çatır?

Data final layihəsi. bina.az-dakı bütün aylıq kirayə elanları (22 262 xam → 17 347 unikal) Python ilə toplanır,
təmizlənir, Oracle-a yazılır, SQL view-larında hesablanır və iki yerdə göstərilir:
**Power BI dashboard** və **Streamlit saytı** (Gemini AI izahı ilə). Maaş: Dövlət Statistika Komitəsi.

## Quruluş
| Qovluq | Nə var |
|---|---|
| `src/` | Python: `scrape.py` (toplama), `clean.py` (10 qayda), `load_oracle.py`, `fetch_salary.py`, `load_salary.py`, `export_data.py` |
| `sql/` | Oracle: cədvəllər, view-lar, büdcə sorğusu, müdafiə sorğuları |
| `exports/`, `app/data/` | Bazadan çıxarılan CSV-lər (Power BI və sayt eyni faylları oxuyur) |
| `powerbi/` | Dashboard (PBIP) |
| `app/` | Sayt: `app.py` (Streamlit), `core.py` (hesablamalar), `ui.py` (dizayn), `ai.py` (Gemini) |
| `docs/` | Komanda üçün izah sənədi |

## Lokal işə salma (Windows)
1. `setup.bat` — mühit və paketlər (bir dəfə).
2. `run_pipeline.bat` — toplama → təmizləmə → Oracle → maaş → ixrac.
3. Power BI: `powerbi/BakuKiraye.pbip` → **Refresh**.
4. Sayt: `run_site.bat` → brauzerdə `http://localhost:8501`.

Gizli parametrlər `.env` faylındadır (`env.example.txt`-ə baxın) və GitHub-a yüklənmir.

## Saytı internetdə yayımlamaq (Streamlit Community Cloud)
1. GitHub-da repo yaradın və bu qovluğu yükləyin (`.gitignore` gizli faylları avtomatik çıxarır).
2. [share.streamlit.io](https://share.streamlit.io) → **Create app** → repo seçin → *Main file path*: `app/app.py`.
3. **Advanced settings → Secrets**: `.streamlit/secrets.toml.example`-dəki iki sətri öz Gemini açarınızla yazın.
4. **Deploy**. Paketlər `app/requirements.txt`-dən quraşdırılır.

Məlumat həftəlik yenilənəndə (`run_pipeline.bat`) `app/data/` qovluğunu GitHub-a yenidən yükləmək kifayətdir — sayt özü yenilənir.
