"""
create_db_user.py — Layihənin Oracle istifadəçisini yaradır (Addım 0).

Nə edir:
  .env-dəki ORACLE_USER ilə qoşulmağa çalışır. Alınırsa, istifadəçi artıq var.
  Alınmırsa, admin (SYSTEM) parolunu ekranda göstərmədən soruşur və
  ayrıca layihə istifadəçisi yaradır.

Niyə ayrıca istifadəçi:
  Layihə cədvəlləri SYSTEM sxemində saxlanmamalıdır. Ayrı sxem təhlükəsizdir,
  səliqəlidir və layihəni sistem obyektlərindən ayırır. Admin parolu heç
  yerdə saxlanmır, yalnız bir dəfə daxil edilir.
"""
import getpass
import os
import re
import sys

import oracledb
from config import load_env

ENV_PATH = load_env()

DSN = os.getenv("ORACLE_DSN", "localhost:1521/XEPDB1")
USER = os.getenv("ORACLE_USER", "BAKU_RENT")
PASSWORD = os.getenv("ORACLE_PASSWORD", "")


def main() -> int:
    if ENV_PATH is None:
        print("XETA: .env fayli tapilmadi. setup.bat-i yeniden isledin.")
        return 1
    if not PASSWORD or PASSWORD.startswith("BURAYA"):
        print("XETA: .env faylinda ORACLE_PASSWORD doldurulmayib.")
        return 1
    # Ad və parol SQL-ə birbaşa yazıldığı üçün formatı yoxlayırıq (SQL injection qarşısı)
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,29}", USER):
        print("XETA: ORACLE_USER yalniz herf, reqem ve _ olmalidir.")
        return 1
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{7,29}", PASSWORD):
        print("XETA: ORACLE_PASSWORD herfle baslamali, yalniz herf/reqem olmali, 8+ simvol.")
        return 1

    # 1) İstifadəçi artıq varmı?
    try:
        with oracledb.connect(user=USER, password=PASSWORD, dsn=DSN):
            print(f"OK: {USER} istifadecisi artiq movcuddur.")
            return 0
    except oracledb.Error as e:
        print(f"{USER} ile qosulmaq olmadi ({str(e).splitlines()[0]}). Yaradilacaq.")

    # 2) Admin ilə qoşulub istifadəçini yaradırıq
    admin = input("Oracle admin istifadecisi [SYS]: ").strip() or "SYS"
    admin_pw = getpass.getpass(f"{admin} parolu (ekranda gorunmeyecek): ")
    try:
        # SYS yalnız SYSDBA rolu ilə qoşula bilir (SQL Developer-dəki "Role: SYSDBA" kimi)
        mode = oracledb.AUTH_MODE_SYSDBA if admin.upper() == "SYS" else oracledb.AUTH_MODE_DEFAULT
        with oracledb.connect(user=admin, password=admin_pw, dsn=DSN, mode=mode) as conn:
            cur = conn.cursor()
            cur.execute(
                f'CREATE USER {USER} IDENTIFIED BY "{PASSWORD}" '
                f"DEFAULT TABLESPACE USERS QUOTA UNLIMITED ON USERS"
            )
            cur.execute(
                f"GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, "
                f"CREATE SEQUENCE, CREATE PROCEDURE TO {USER}"
            )
            print(f"OK: {USER} yaradildi.")
            return 0
    except oracledb.Error as e:
        print(f"XETA Oracle: {e}")
        print("Ipucu: Oracle xidmeti islemir ve ya DSN sehvdir (meselen localhost:1521/XE).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
