"""
export_data.py — Oracle view-larından ixrac qatı (export layer) yaradır (Addım 3).

Nəticə: exports/*.csv  (Power BI və sayt EYNİ fayllardan oxuyur)
  listings.csv       — son snapshotun təmiz elanları (v_listing_current)
  district.csv       — rayonlar (koordinatlarla)
  district_stats.csv — rayon x otaq üzrə median, P25, P75 (v_district_stats)
  price_trend.csv    — snapshotlar üzrə median dinamikası (v_price_trend)
  salary.csv         — DSK: sahələr üzrə orta aylıq əməkhaqqı (ölkə üzrə)
  salary_region.csv  — DSK: rayon və şəhərlər üzrə orta aylıq əməkhaqqı (Bakı şəhəri daxil)
  snapshot.csv       — məlumatın tarixi və həcmi

Niyə ixrac qatı:
  * Power BI və sayt eyni rəqəmləri göstərir (bir mənbə — bir həqiqət).
  * Hesabat Oracle Client quraşdırılmamış kompüterdə də açılır.
  * Sayt internetdə işləyir, amma verilənlər bazası internetə açılmır (təhlükəsizlik).
"""
import csv
import sys

from config import ROOT
from db import connect

EXPORTS = ROOT / "exports"
APP_DATA = ROOT / "app" / "data"

QUERIES = {
    "listings": """SELECT listing_id, district_id, district_name, is_baku_city, location_name, location_type,
                          building_type, rooms, rooms_group, area_m2, floor, floors, price_azn, price_per_m2,
                          has_repair, has_bill_of_sale, is_agency, url
                   FROM v_listing_current ORDER BY listing_id""",
    "district": """SELECT district_id, district_name, is_baku_city, latitude, longitude
                   FROM dim_district ORDER BY district_name""",
    "district_stats": "SELECT * FROM v_district_stats ORDER BY district_name, rooms_group",
    "price_trend": "SELECT * FROM v_price_trend ORDER BY captured_at, district_name, rooms_group",
    "salary": """SELECT year, sector_name, avg_salary_azn, source_url
                 FROM salary_sector ORDER BY year, avg_salary_azn DESC""",
    "salary_region": """SELECT year, region_name, avg_salary_azn, source_url
                        FROM salary_region ORDER BY year, region_name""",
    "snapshot": """SELECT snapshot_id, captured_at, rows_raw, rows_clean, rows_outlier, rows_duplicate
                   FROM v_latest_snapshot""",
}


def write_csv(path, header, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([h.lower() for h in header])
        for r in rows:
            w.writerow(["" if v is None else (v.isoformat(sep=" ") if hasattr(v, "isoformat") else v) for v in r])


def main() -> int:
    with connect() as conn:
        cur = conn.cursor()
        for name, sql in QUERIES.items():
            cur.execute(sql)
            header = [d[0] for d in cur.description]
            rows = cur.fetchall()
            for folder in (EXPORTS, APP_DATA):  # sayt üçün də eyni nüsxə
                write_csv(folder / f"{name}.csv", header, rows)
            print(f"{name:15} {len(rows):6} sətir")
    return 0


if __name__ == "__main__":
    sys.exit(main())
