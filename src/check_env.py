"""
check_env.py — Mühit yoxlaması (Addım 0).

Nə edir: Python-u, paketləri, Oracle bağlantısını və Azərbaycan hərflərini,
bina.az-a çıxışı və Gemini API açarını yoxlayır.
Nəticə: logs/check_env.log (parollar və açarlar loga YAZILMIR).
Niyə: işə başlamazdan əvvəl hər alətin işlədiyinə əmin olmaq üçün.
"""
import datetime
import importlib
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs" / "check_env.log"
lines: list[str] = []


def log(msg: str) -> None:
    print(msg)
    lines.append(msg)


def check_packages() -> None:
    for pkg in ["requests", "pandas", "oracledb", "dotenv", "streamlit", "google.genai"]:
        try:
            m = importlib.import_module(pkg)
            log(f"OK   paket {pkg} {getattr(m, '__version__', '')}")
        except Exception as e:  # noqa: BLE001
            log(f"XETA paket {pkg}: {e}")


def check_oracle() -> None:
    import oracledb

    dsn, user, pw = os.getenv("ORACLE_DSN"), os.getenv("ORACLE_USER"), os.getenv("ORACLE_PASSWORD")
    log(f"Oracle DSN={dsn} USER={user}")
    try:
        with oracledb.connect(user=user, password=pw, dsn=dsn) as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM nls_database_parameters WHERE parameter='NLS_CHARACTERSET'")
            log(f"OK   Oracle qosuldu, server versiyasi {conn.version}, charset {cur.fetchone()[0]}")
            sample = "Yasamal ə ş ğ ı ö ü ç Ə Ş"
            cur.execute("SELECT :s FROM dual", s=sample)
            back = cur.fetchone()[0]
            log(f"{'OK  ' if back == sample else 'XETA'} Azərbaycan hərfləri: {back}")
            cur.execute("SELECT privilege FROM session_privs ORDER BY 1")
            log("     huquqlar: " + ", ".join(r[0] for r in cur.fetchall()))
    except Exception as e:  # noqa: BLE001
        log(f"XETA Oracle: {e}")


def check_bina() -> None:
    import requests

    try:
        r = requests.get(
            "https://bina.az/",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36"},
            timeout=20,
        )
        log(
            f"{'OK  ' if r.ok else 'XETA'} bina.az status={r.status_code} size={len(r.content)} "
            f"server={r.headers.get('server')} cf={'cf-ray' in r.headers}"
        )
    except Exception as e:  # noqa: BLE001
        log(f"XETA bina.az: {e}")


def check_gemini() -> None:
    key = os.getenv("GEMINI_API_KEY", "")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    if not key or key.startswith("BURAYA"):
        log("XETA Gemini: GEMINI_API_KEY .env-də doldurulmayıb")
        return
    try:
        from google import genai

        client = genai.Client(api_key=key)
        try:
            resp = client.models.generate_content(model=model, contents="Bir sözlə cavab ver: salam")
            log(f"OK   Gemini ({model}) cavab verdi: {resp.text.strip()[:40]}")
        except Exception as e:  # noqa: BLE001
            log(f"XETA Gemini model {model}: {str(e)[:200]}")
            names = [m.name for m in client.models.list() if "flash" in m.name]
            log("     movcud flash modelleri: " + ", ".join(names[:15]))
    except Exception as e:  # noqa: BLE001
        log(f"XETA Gemini: {str(e)[:200]}")


def main() -> None:
    log(f"Tarix: {datetime.datetime.now().isoformat(timespec='seconds')}")
    log(f"Python: {sys.version.split()[0]} | {platform.platform()}")
    check_packages()
    from config import load_env

    env_path = load_env()
    log(f"{'OK  ' if env_path else 'XETA'} .env faylı: {env_path.name if env_path else 'tapılmadı'}")
    check_oracle()
    check_bina()
    check_gemini()
    LOG.parent.mkdir(exist_ok=True)
    LOG.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nLog: {LOG}")


if __name__ == "__main__":
    main()
