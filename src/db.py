"""
db.py — Oracle bağlantısı və SQL fayllarının icrası (digər skriptlər bunu istifadə edir).

Niyə ayrıca modul: bağlantı parametrləri .env-dən bir yerdə oxunur, parol koda yazılmır.
python-oracledb "thin" rejimində işləyir: Oracle Client quraşdırmağa ehtiyac yoxdur.

Yoxlama:  python src/db.py --selftest
  sql/04_defense_queries.sql və sql/03_budget_query.sql-dəki bütün sorğuları işlədir və hər biri üçün
  "OK / XETA" yazır — müdafiədən əvvəl sorğuların işlədiyinə əmin olmaq üçün.
"""
import os
import re
from pathlib import Path

import oracledb

from config import load_env

load_env()


def connect() -> oracledb.Connection:
    """Oracle-a qoşulur. İstifadəçi, parol və ünvan .env faylından oxunur (koda yazılmır, GitHub-a getmir)."""
    return oracledb.connect(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"],
    )


def split_sql(path: Path) -> list[str]:
    """SQL faylını ayrı əmrlərə bölür: şərhləri atır, ';' ilə bitən blokları ayırır."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"--[^\n]*", "", text)
    return [s.strip() for s in text.split(";") if s.strip()]


def run_sql_file(conn: oracledb.Connection, path: Path) -> int:
    """SQL faylındakı əmrləri ardıcıl icra edir (cədvəl və view yaratmaq üçün). Qaytarır: əmr sayı."""
    cur = conn.cursor()
    statements = split_sql(path)
    for stmt in statements:
        cur.execute(stmt)
    return len(statements)


def selftest() -> int:
    """Müdafiə sorğularının hamısını bir-bir işlədir. Qaytarır: xətalı sorğu sayı."""
    root = Path(__file__).resolve().parents[1] / "sql"
    binds = {"budget": 415, "people": 1, "rooms": "2"}  # 03_budget_query.sql-in parametrləri (nümunə)
    errors = 0
    with connect() as conn:
        cur = conn.cursor()
        for fname in ("04_defense_queries.sql", "03_budget_query.sql"):
            for i, stmt in enumerate(split_sql(root / fname), 1):
                try:
                    cur.execute(stmt, binds if ":budget" in stmt else {})
                    rows = cur.fetchmany(3)
                    print(f"OK   {fname} #{i}: {len(rows)}+ sətir, ilk sətir: {rows[0] if rows else '—'}")
                except oracledb.Error as e:
                    errors += 1
                    print(f"XETA {fname} #{i}: {str(e).splitlines()[0]}")
    print(f"Yekun: {errors} xəta")
    return errors


if __name__ == "__main__":
    import sys

    if "--selftest" in sys.argv:
        sys.exit(1 if selftest() else 0)
    print("İstifadə: python src/db.py --selftest")
