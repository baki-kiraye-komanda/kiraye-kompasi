"""
config.py — Layihənin ümumi parametrləri (bir yerdə saxlanılır ki, hər skriptdə təkrarlanmasın).

Niyə ayrıca fayl: rayon siyahısı, qovluqlar və qaydalar dəyişərsə,
yalnız burada dəyişmək kifayətdir.
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows konsolu/log faylları üçün: Azərbaycan hərfləri (ə, ı, ş) çapda xəta verməsin
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_CLEAN = ROOT / "data" / "clean"
DATA_REF = ROOT / "data" / "ref"
APP_DATA = ROOT / "app" / "data"
LOGS = ROOT / "logs"

BAKU_TZ = timezone(timedelta(hours=4))  # Azərbaycanda yay/qış vaxtı yoxdur: həmişə UTC+4

# bina.az-ın öz məkan lüğətindəki rayon ID-ləri (locationGroupId = 2).
# Abşeron inzibati cəhətdən Bakıya aid deyil, amma bina.az onu "Bakı" axtarışına
# daxil edir və kirayəçilər üçün real seçimdir (Masazır, Xırdalan yolu və s.).
# Ona görə saxlayırıq, amma is_baku_city = "N" kimi işarələyirik.
DISTRICTS = {
    "58": ("Binəqədi", "Y"),
    "16": ("Xətai", "Y"),
    "15": ("Xəzər", "Y"),
    "57": ("Qaradağ", "Y"),
    "10": ("Nərimanov", "Y"),
    "190": ("Nəsimi", "Y"),
    "11": ("Nizami", "Y"),
    "249": ("Pirallahı", "Y"),
    "13": ("Sabunçu", "Y"),
    "12": ("Səbail", "Y"),
    "14": ("Suraxanı", "Y"),
    "56": ("Yasamal", "Y"),
    "197": ("Abşeron", "N"),
}

# bina.az kateqoriyaları: 2 = Yeni tikili, 3 = Köhnə tikili
BUILDING_TYPES = {"2": "Yeni tikili", "3": "Köhnə tikili"}

# Sabit məzənnə: AZN 2017-dən USD-yə 1.70 səviyyəsində bağlıdır (AMB)
USD_TO_AZN = 1.70


def load_env() -> Path | None:
    """.env faylını yükləyir. Notepad bəzən faylı ".env.txt" kimi saxlayır - onu da qəbul edirik."""
    from dotenv import load_dotenv

    for name in (".env", ".env.txt"):
        path = ROOT / name
        if path.exists():
            load_dotenv(path, override=True)
            return path
    return None


def new_snapshot_id() -> tuple[str, str]:
    """Snapshot ID (məs. 20261108_0130) və ISO vaxt (Bakı vaxtı ilə) qaytarır."""
    now = datetime.now(BAKU_TZ)
    return now.strftime("%Y%m%d_%H%M"), now.isoformat(timespec="seconds")
