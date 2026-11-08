"""
load_salary.py — DSK cədvəllərindən orta aylıq nominal əməkhaqqını oxuyur və Oracle-a yazır.

İki cədvəl (hər ikisi https://www.stat.gov.az/source/labour/ bölməsindən):
  1. Vərəq "4.2" (004_2-3.xls)  -> SALARY_SECTOR  : iqtisadi fəaliyyət növləri üzrə (ÖLKƏ ortalaması)
  2. Vərəq "9.6" (009_6.xls)    -> SALARY_REGION  : iqtisadi rayonlar və şəhərlər üzrə (BAKI şəhəri daxil)

Qayda (hər iki vərəq üçün eyni): başlıq sətri — içində ən azı 3 il (1990-2100) olan ilk sətirdir;
ad sütunu 3-cü sütundur (indeks 2); rəqəmi olmayan sətirlər ("o cümlədən:") atılır.
Son 5 il saxlanılır. MERGE: təkrar işlədəndə dublikat yaranmır, rəqəm dəyişibsə yenilənir.

Niyə Bakı rəqəmi vacibdir: kirayə Bakıdadır, ona görə əsas göstərici "Bakıda orta maaş"dır
(2025: 1383.4 AZN). Ölkə ortalaması (1103.2) Bakı üçün yükü şişirdərdi.
Qeyd: bu, ORTA (median deyil) və vergidən əvvəlki (nominal) məbləğdir.
"""
import sys
import warnings

import pandas as pd

from config import DATA_REF
from db import connect

# DSK faylı köhnə .xls formatındadır (xlrd ilə oxunur); pandas-ın "xlrd köhnəlir" xəbərdarlığı nəticəyə təsir etmir
warnings.filterwarnings("ignore", message="The xlrd engine")

KEEP_YEARS = 5
LABEL_COL = 2
TABLES = [  # (fayl, vərəq, Oracle cədvəli, ad sütunu, mənbə)
    ("salary_raw_az.xls", "4.2", "salary_sector", "sector_name",
     "https://www.stat.gov.az/source/labour/az/004_2-3.xls"),
    ("salary_raw_region_az.xls", "9.6", "salary_region", "region_name",
     "https://www.stat.gov.az/source/labour/az/009_6.xls"),
]


def as_year(v):
    y = pd.to_numeric(v, errors="coerce")  # il xanası 2025 və ya 2024.0 kimi gələ bilər
    return int(y) if pd.notna(y) and 1990 <= y <= 2100 and float(y).is_integer() else None


def parse(path, sheet: str) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet, header=None)
    header_idx = next(i for i in raw.index
                      if sum(as_year(v) is not None for v in raw.loc[i]) >= 3)
    years = {c: as_year(v) for c, v in raw.loc[header_idx].items()
             if c != LABEL_COL and as_year(v) is not None}
    rows = []
    for i in range(header_idx + 1, len(raw)):
        name = raw.at[i, LABEL_COL]
        if pd.isna(name) or not str(name).strip():
            continue
        name = " ".join(str(name).split())  # artıq boşluqlar silinir
        for c, year in years.items():
            val = pd.to_numeric(raw.at[i, c], errors="coerce")
            if pd.notna(val) and val > 0:
                rows.append({"year": year, "name": name, "avg_salary_azn": round(float(val), 2)})
    df = pd.DataFrame(rows).drop_duplicates(["year", "name"])
    return df[df["year"] > df["year"].max() - KEEP_YEARS]


def main() -> int:
    with connect() as conn:
        cur = conn.cursor()
        for fname, sheet, table, col, url in TABLES:
            path = DATA_REF / fname
            if not path.exists():
                print(f"XETA: {path} yoxdur — əvvəlcə fetch_salary.py işlədin")
                return 1
            df = parse(path, sheet)
            print(f"{table}: {len(df)} sətir, illər {df.year.min()}-{df.year.max()}, {df.name.nunique()} ad")
            cur.executemany(
                f"""MERGE INTO {table} t
                    USING (SELECT :1 yr, :2 nm, :3 sal, :4 src FROM dual) s
                    ON (t.year = s.yr AND t.{col} = s.nm)
                    WHEN MATCHED THEN UPDATE SET t.avg_salary_azn = s.sal, t.source_url = s.src
                    WHEN NOT MATCHED THEN INSERT (year, {col}, avg_salary_azn, source_url)
                         VALUES (s.yr, s.nm, s.sal, s.src)""",
                [(int(r.year), r.name, r.avg_salary_azn, url) for r in df.itertuples()],
            )
        conn.commit()
        cur.execute("SELECT region_name, avg_salary_azn FROM salary_region "
                    "WHERE year = (SELECT MAX(year) FROM salary_region) "
                    "AND (region_name LIKE 'Bak%' OR region_name LIKE 'Azərbaycan%') ORDER BY 2 DESC")
        for name, sal in cur.fetchall():
            print(f"  {sal:>8} AZN  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
