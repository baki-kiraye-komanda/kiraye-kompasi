"""
clean.py — Xam elanları təmizləyir (Addım 2, Data transformation).

Giriş:  data/raw/<snapshot_id>/listings_raw.csv
Çıxış:  data/clean/<snapshot_id>/listings_clean.csv
        data/clean/<snapshot_id>/cleaning_report.json  (hər qaydanın neçə sətir təsir etdiyi)

Qaydalar (hər birinin səbəbi yanında yazılıb):
  R1 Təkrar elan (eyni listing_id)              -> silinir   (bir mənzil iki dəfə sayılmasın)
  R2 Günlük kirayə                              -> silinir   (layihə aylıq kirayə haqqındadır)
  R3 Valyuta USD                                -> AZN-ə çevrilir (1 USD = 1.70 AZN); digər valyuta silinir
  R4 Qiymət yoxdur / 100 AZN-dən az / 30 000-dən çox -> silinir (səhv daxil edilmiş və ya satış qiyməti)
  R5 Otaq sayı yoxdur                           -> silinir
  R6 Sahə yoxdur, 10 m²-dən az və ya 1000-dən çox -> silinir (fiziki mümkün olmayan dəyər)
  R7 Mərtəbə > binanın mərtəbə sayı              -> mərtəbə boş qoyulur (sətir saxlanılır)
     Binanın mərtəbə sayı 60-dan çox (məs. "1300") -> boş qoyulur: Bakıda belə yaşayış binası yoxdur
  R8 Qeyri-adi qiymət (1 m² qiyməti öz otaq qrupunun 1%-99% intervalından kənar)
                                                -> SİLİNMİR, is_outlier = Y işarələnir.
     Niyə silmirik: bu elanlar real ola bilər (lüks və ya çox ucuz). Statistikada
     (median, P25-P75) nəzərə alınmır, amma bazada qalır və yoxlanıla bilər.
  R9 Ehtimal olunan təkrar elan: eyni rayon, məkan, tikili növü, otaq, sahə, mərtəbə,
     mərtəbə sayı və qiymət -> SİLİNMİR, is_duplicate = Y işarələnir (ən son yenilənən qalır).
     Niyə: eyni mənzili bir neçə vasitəçi ayrı-ayrı elan kimi yerləşdirir (ID fərqli olur).
     Saylar ("neçə mənzil") təkrarsız hesablanmalıdır.
  R10 Ehtimal olunan OTAQ kirayəsi (bütün mənzil yox): Bakı şəhərində 2 otaqlı ≤ 250,
     3 otaqlı ≤ 350, 4+ otaqlı ≤ 400 AZN -> SİLİNMİR, is_outlier = Y işarələnir.
     Niyə: belə elanlarda adətən "otaq yoldaşı axtarılır" yazılır və qiymət 1 nəfər
     üçündür. 08.11.2026-da ən ucuz 210 elan bina.az-da əl ilə yoxlandı: bu həddən
     aşağı elanların ~89%-i otaq/yataq kirayəsi idi. Abşeron (Masazır) bu qaydaya
     düşmür: orada ucuz elanlar real mənzildir (yoxlamada 0 otaq kirayəsi).
"""
import json
import sys

import pandas as pd

from config import DATA_CLEAN, DATA_RAW, DISTRICTS, USD_TO_AZN

MIN_PRICE, MAX_PRICE = 100, 30000
MIN_AREA, MAX_AREA = 10, 1000
MAX_FLOORS = 60
# R10: Bakı şəhərində bu qiymətdən ucuz (və ya bərabər) çoxotaqlı elan çox güman ki, otaq kirayəsidir
ROOM_SHARE_MAX = {2: 250, 3: 350, 4: 400}  # 4 və daha çox otaq üçün 400
BAKU_CITY_IDS = {k for k, (_, city) in DISTRICTS.items() if city == "Y"}


def latest_snapshot() -> str:
    # meta.json yalnız toplama bitəndə yazılır; INCOMPLETE — elanların 95%-dən azı toplanıb.
    # Belə snapshot-lar təmizlənmir: köhnə, tam məlumat istifadə olunur.
    snaps = sorted(p.name for p in DATA_RAW.iterdir()
                   if (p / "listings_raw.csv").exists() and (p / "meta.json").exists()
                   and not (p / "INCOMPLETE").exists())
    if not snaps:
        raise SystemExit("data/raw-da snapshot tapılmadı. Əvvəl scrape.py işlədin.")
    return snaps[-1]


def to_bool(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().isin(["true", "1", "y"])


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    report: dict[str, int] = {"raw_rows": len(df)}

    before = len(df)
    df = df.drop_duplicates(subset="listing_id")
    report["R1_duplicates_removed"] = before - len(df)

    daily = to_bool(df["is_paid_daily"])
    report["R2_daily_removed"] = int(daily.sum())
    df = df[~daily].copy()

    df["price"] = pd.to_numeric(df["price"], errors="coerce").astype("float64")
    is_usd = df["currency"].eq("USD")
    report["R3_usd_converted"] = int(is_usd.sum())
    df.loc[is_usd, "price"] = df.loc[is_usd, "price"] * USD_TO_AZN
    other_cur = ~df["currency"].isin(["AZN", "USD"])
    report["R3_other_currency_removed"] = int(other_cur.sum())
    df = df[~other_cur].copy()
    df = df.rename(columns={"price": "price_azn"})

    bad_price = df["price_azn"].isna() | (df["price_azn"] < MIN_PRICE) | (df["price_azn"] > MAX_PRICE)
    report["R4_bad_price_removed"] = int(bad_price.sum())
    df = df[~bad_price].copy()

    df["rooms"] = pd.to_numeric(df["rooms"], errors="coerce")
    no_rooms = df["rooms"].isna() | (df["rooms"] <= 0)
    report["R5_no_rooms_removed"] = int(no_rooms.sum())
    df = df[~no_rooms].copy()
    df["rooms"] = df["rooms"].astype(int)
    df["rooms_group"] = df["rooms"].clip(upper=5).astype(str).replace({"5": "5+"})

    df["area_m2"] = pd.to_numeric(df["area_m2"], errors="coerce").astype("float64")
    bad_area = df["area_m2"].isna() | (df["area_m2"] < MIN_AREA) | (df["area_m2"] > MAX_AREA)
    report["R6_bad_area_removed"] = int(bad_area.sum())
    df = df[~bad_area].copy()

    df["floor"] = pd.to_numeric(df["floor"], errors="coerce").astype("Int64")
    df["floors"] = pd.to_numeric(df["floors"], errors="coerce").astype("Int64")
    bad_floors = df["floors"].notna() & ((df["floors"] < 1) | (df["floors"] > MAX_FLOORS))
    report["R7_bad_floors_fixed"] = int(bad_floors.sum())
    df.loc[bad_floors, "floors"] = pd.NA
    bad_floor = df["floor"].notna() & df["floors"].notna() & (df["floor"] > df["floors"])
    report["R7_floor_fixed"] = int(bad_floor.sum())
    df.loc[bad_floor, "floor"] = pd.NA

    df["price_azn"] = df["price_azn"].round(2)
    df["price_per_m2"] = (df["price_azn"] / df["area_m2"]).round(2)
    lo = df.groupby("rooms_group")["price_per_m2"].transform(lambda s: s.quantile(0.01))
    hi = df.groupby("rooms_group")["price_per_m2"].transform(lambda s: s.quantile(0.99))
    df["is_outlier"] = ((df["price_per_m2"] < lo) | (df["price_per_m2"] > hi)).map({True: "Y", False: "N"})
    report["R8_outliers_flagged"] = int((df["is_outlier"] == "Y").sum())

    # R10: otaq kirayəsi (qiymət 1 nəfər üçündür, bütün mənzil üçün yox)
    limit = df["rooms"].clip(upper=4).map(ROOM_SHARE_MAX)  # 1 otaqlı -> NaN (qayda tətbiq olunmur)
    room_share = (df["district_id"].astype(str).isin(BAKU_CITY_IDS)
                  & limit.notna() & (df["price_azn"] <= limit))
    report["R10_room_share_flagged"] = int((room_share & (df["is_outlier"] == "N")).sum())
    df.loc[room_share, "is_outlier"] = "Y"

    # R9: eyni mənzilin təkrar elanları (ən son yenilənən elan "əsas" sayılır)
    dup_key = ["district_id", "location_id", "building_type_id", "rooms", "area_m2", "floor", "floors", "price_azn"]
    # eyni vaxtda yenilənən elanlarda böyük ID (daha yeni elan) qalır: nəticə hər dəfə eyni olsun
    df = df.sort_values(["updated_at", "listing_id"], ascending=False, kind="mergesort")
    df["is_duplicate"] = df.duplicated(subset=dup_key, keep="first").map({True: "Y", False: "N"})
    df = df.sort_values("listing_id")
    report["R9_duplicates_flagged"] = int((df["is_duplicate"] == "Y").sum())

    for col in ["has_repair", "has_bill_of_sale", "has_mortgage", "is_agency"]:
        df[col] = to_bool(df[col]).map({True: "Y", False: "N"})

    report["clean_rows"] = len(df)
    report["analysis_rows"] = int(((df["is_outlier"] == "N") & (df["is_duplicate"] == "N")).sum())
    cols = ["snapshot_id", "captured_at", "listing_id", "district_id", "building_type_id",
            "location_id", "rooms", "rooms_group", "area_m2", "floor", "floors", "price_azn",
            "price_per_m2", "has_repair", "has_bill_of_sale", "has_mortgage", "is_agency",
            "is_outlier", "is_duplicate", "updated_at", "url"]
    return df[cols], report


def main(snapshot_id: str | None = None) -> int:
    snapshot_id = snapshot_id or latest_snapshot()
    raw = pd.read_csv(DATA_RAW / snapshot_id / "listings_raw.csv", dtype=str, encoding="utf-8-sig")
    df, report = clean(raw)
    out = DATA_CLEAN / snapshot_id
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "listings_clean.csv", index=False, encoding="utf-8-sig")
    report["snapshot_id"] = snapshot_id
    (out / "cleaning_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for k, v in report.items():
        print(f"{k:30} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
