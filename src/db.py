"""
db.py — Oracle bağlantısı və SQL fayllarının icrası (digər skriptlər bunu istifadə edir).

Niyə ayrıca modul: bağlantı parametrləri .env-dən bir yerdə oxunur, parol koda yazılmır.
python-oracledb "thin" rejimində işləyir: Oracle Client quraşdırmağa ehtiyac yoxdur.
"""
import os
import re
from pathlib import Path

import oracledb

from config import load_env

load_env()


def connect() -> oracledb.Connection:
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
    cur = conn.cursor()
    statements = split_sql(path)
    for stmt in statements:
        cur.execute(stmt)
    return len(statements)
