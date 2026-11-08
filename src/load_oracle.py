"""
load_oracle.py — Təmiz məlumatı Oracle-a yükləyir (Addım 2).

Ardıcıllıq:
  1. Cədvəllər yoxdursa, sql/01_schema.sql ilə yaradılır.
  2. Ölçü cədvəlləri (rayon, məkan, tikili növü) MERGE ilə yenilənir:
     yeni dəyər əlavə olunur, mövcud dəyər yenilənir, heç nə silinmir.
  3. Snapshot artıq yüklənibsə, təkrar yüklənmir (eyni məlumat iki dəfə sayılmasın).
     "--reload" ilə işlədilsə: həmin snapshotun köhnə sətirləri silinib yenidən yazılır
     (təmizləmə qaydaları dəyişəndə lazımdır).
  4. Elanlar 2000-lik paketlərlə (executemany + bind parametrləri) yazılır.
     Bind parametrləri: sürətlidir və SQL injection-dan qoruyur.
  5. Hər şey bir tranzaksiyadır: xəta olarsa ROLLBACK, uğurda COMMIT.
  6. sql/02_views.sql ilə view-lar yenilənir.
  Miqrasiya: köhnə bazada yeni sütun/cədvəl yoxdursa, ALTER TABLE / CREATE TABLE ilə əlavə edilir
  (məlumat silinmir).
"""
import csv
import json
import sys
from datetime import datetime

from config import BUILDING_TYPES, DATA_CLEAN, DATA_RAW, DATA_REF, DISTRICTS, ROOT
from db import connect, run_sql_file

BATCH = 2000


def latest_clean_snapshot() -> str:
    snaps = sorted(p.name for p in DATA_CLEAN.iterdir() if (p / "listings_clean.csv").exists())
    if not snaps:
        raise SystemExit("data/clean-də snapshot yoxdur. Əvvəl clean.py işlədin.")
    return snaps[-1]


def ts(value: str | None) -> datetime | None:
    """ISO vaxtı (+04:00 ilə) Bakı vaxtı ilə sadə TIMESTAMP-a çevirir."""
    if not value:
        return None
    return datetime.fromisoformat(value).replace(tzinfo=None)


def num(value: str | None) -> float | None:
    return float(value) if value not in (None, "", "nan") else None


def ensure_schema(cur) -> None:
    cur.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'FACT_LISTING'")
    if cur.fetchone()[0] == 0:
        n = run_sql_file(cur.connection, ROOT / "sql" / "01_schema.sql")
        print(f"Sxem yaradıldı ({n} əmr).")


def column_exists(cur, table: str, column: str) -> bool:
    cur.execute("SELECT COUNT(*) FROM user_tab_columns WHERE table_name = :1 AND column_name = :2",
                [table.upper(), column.upper()])
    return cur.fetchone()[0] > 0


def migrate(cur) -> None:
    """Köhnə versiyada yaradılmış bazaya yeni sütun və cədvəlləri əlavə edir (məlumat itmir)."""
    if not column_exists(cur, "fact_listing", "is_duplicate"):
        cur.execute("ALTER TABLE fact_listing ADD (is_duplicate CHAR(1) DEFAULT 'N' NOT NULL "
                    "CHECK (is_duplicate IN ('Y', 'N')))")
        print("Miqrasiya: fact_listing.is_duplicate əlavə olundu.")
    if not column_exists(cur, "snapshot", "rows_duplicate"):
        cur.execute("ALTER TABLE snapshot ADD (rows_duplicate NUMBER(10) DEFAULT 0 NOT NULL)")
        print("Miqrasiya: snapshot.rows_duplicate əlavə olundu.")
    cur.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'SALARY_REGION'")
    if cur.fetchone()[0] == 0:
        cur.execute("""CREATE TABLE salary_region (
            year NUMBER(4) NOT NULL, region_name VARCHAR2(200 CHAR) NOT NULL,
            avg_salary_azn NUMBER(10,2) NOT NULL CHECK (avg_salary_azn > 0),
            source_url VARCHAR2(300) NOT NULL,
            CONSTRAINT pk_salary_region PRIMARY KEY (year, region_name))""")
        print("Miqrasiya: salary_region cədvəli yaradıldı.")


def merge_dimensions(cur) -> set[int]:
    cur.executemany(
        """MERGE INTO dim_building_type t USING (SELECT :1 id, :2 name FROM dual) s
           ON (t.building_type_id = s.id)
           WHEN MATCHED THEN UPDATE SET t.building_type = s.name
           WHEN NOT MATCHED THEN INSERT VALUES (s.id, s.name)""",
        [(int(k), v) for k, v in BUILDING_TYPES.items()],
    )
    with open(DATA_REF / "locations.csv", encoding="utf-8-sig") as f:
        locs = list(csv.DictReader(f))
    coords = {r["location_id"]: (num(r["latitude"]), num(r["longitude"])) for r in locs}
    cur.executemany(
        """MERGE INTO dim_district t USING (SELECT :1 id, :2 name, :3 baku, :4 lat, :5 lon FROM dual) s
           ON (t.district_id = s.id)
           WHEN MATCHED THEN UPDATE SET t.district_name = s.name, t.is_baku_city = s.baku,
                                        t.latitude = s.lat, t.longitude = s.lon
           WHEN NOT MATCHED THEN INSERT VALUES (s.id, s.name, s.baku, s.lat, s.lon)""",
        [(int(k), n, b, *coords.get(k, (None, None))) for k, (n, b) in DISTRICTS.items()],
    )
    cur.executemany(
        """MERGE INTO dim_location t USING (SELECT :1 id, :2 name, :3 typ, :4 dist FROM dual) s
           ON (t.location_id = s.id)
           WHEN MATCHED THEN UPDATE SET t.location_name = s.name, t.location_type = s.typ,
                                        t.district_id = s.dist
           WHEN NOT MATCHED THEN INSERT VALUES (s.id, s.name, s.typ, s.dist)""",
        [(int(r["location_id"]), r["location_name"], r["location_type"],
          int(r["district_id"]) if r["district_id"] else None) for r in locs],
    )
    return {int(r["location_id"]) for r in locs}


def main(snapshot_id: str | None = None, reload: bool = False) -> int:
    snapshot_id = snapshot_id or latest_clean_snapshot()
    clean_dir = DATA_CLEAN / snapshot_id
    report = json.loads((clean_dir / "cleaning_report.json").read_text(encoding="utf-8"))
    meta = json.loads((DATA_RAW / snapshot_id / "meta.json").read_text(encoding="utf-8"))
    with open(clean_dir / "listings_clean.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    with connect() as conn:
        cur = conn.cursor()
        try:
            ensure_schema(cur)
            migrate(cur)
            known_locations = merge_dimensions(cur)

            cur.execute("SELECT COUNT(*) FROM snapshot WHERE snapshot_id = :1", [snapshot_id])
            exists = cur.fetchone()[0] > 0
            if exists and reload:
                cur.execute("DELETE FROM fact_listing WHERE snapshot_id = :1", [snapshot_id])
                cur.execute("DELETE FROM snapshot WHERE snapshot_id = :1", [snapshot_id])
                print(f"--reload: snapshot {snapshot_id} silindi, yenidən yüklənir.")
                exists = False
            if exists:
                print(f"Snapshot {snapshot_id} artıq yüklənib — təkrar yüklənmir.")
                conn.commit()
            else:
                # Lüğətdə olmayan yeni məkanlar "Naməlum" kimi əlavə olunur (FK pozulmasın)
                new_locs = {int(r["location_id"]) for r in rows if r["location_id"]} - known_locations
                if new_locs:
                    cur.executemany(
                        "INSERT INTO dim_location VALUES (:1, :2, 'Naməlum', NULL)",
                        [(i, f"Məkan {i}") for i in sorted(new_locs)],
                    )
                    print(f"Yeni məkan ID-ləri əlavə olundu: {sorted(new_locs)}")

                outliers = sum(r["is_outlier"] == "Y" for r in rows)
                duplicates = sum(r.get("is_duplicate") == "Y" for r in rows)
                cur.execute(
                    "INSERT INTO snapshot (snapshot_id, captured_at, source_url, rows_raw, rows_clean, "
                    "rows_outlier, rows_duplicate) VALUES (:1, :2, :3, :4, :5, :6, :7)",
                    [snapshot_id, ts(meta["captured_at"]), meta["source"], report["raw_rows"], len(rows),
                     outliers, duplicates],
                )
                data = [(
                    r["snapshot_id"], int(r["listing_id"]), int(r["district_id"]),
                    int(r["location_id"]) if r["location_id"] else None, int(r["building_type_id"]),
                    int(r["rooms"]), r["rooms_group"], float(r["area_m2"]),
                    int(float(r["floor"])) if r["floor"] else None,
                    int(float(r["floors"])) if r["floors"] else None,
                    float(r["price_azn"]), float(r["price_per_m2"]), r["has_repair"], r["has_bill_of_sale"],
                    r["has_mortgage"], r["is_agency"], r["is_outlier"], r.get("is_duplicate", "N"),
                    ts(r["updated_at"]), r["url"],
                ) for r in rows]
                # Sütun adları açıq yazılır: miqrasiyadan sonra sütun sırası fərqli ola bilər
                sql = ("INSERT INTO fact_listing (snapshot_id, listing_id, district_id, location_id, building_type_id, "
                       "rooms, rooms_group, area_m2, floor, floors, price_azn, price_per_m2, has_repair, "
                       "has_bill_of_sale, has_mortgage, is_agency, is_outlier, is_duplicate, updated_at, url) "
                       "VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14, :15, :16, :17, :18, :19, :20)")
                for i in range(0, len(data), BATCH):
                    cur.executemany(sql, data[i:i + BATCH])
                conn.commit()
                print(f"Yükləndi: snapshot {snapshot_id}, {len(data)} elan "
                      f"({outliers} qeyri-adi qiymət, {duplicates} təkrar elan işarələndi).")

            n = run_sql_file(conn, ROOT / "sql" / "02_views.sql")
            print(f"View-lar yeniləndi ({n}).")
        except Exception:
            conn.rollback()
            raise

        cur.execute("SELECT COUNT(*), MIN(price_azn), MAX(price_azn) FROM v_listing_current")
        print("Yoxlama v_listing_current (say, min, max):", cur.fetchone())
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(main(args[0] if args else None, reload="--reload" in sys.argv))
