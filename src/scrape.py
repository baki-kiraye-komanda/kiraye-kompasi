"""
scrape.py — bina.az-dan Bakıda aylıq kirayə mənzil elanlarını toplayır (Addım 1).

Necə işləyir:
  bina.az saytı elanları öz GraphQL xidmətindən (https://bina.az/graphql) alır.
  Biz də eyni xidmətə, saytın özünün istifadə etdiyi sahələrlə sorğu göndəririk.
  Hər rayon x tikili növü (yeni/köhnə) üçün səhifə-səhifə (25 elan) gedirik.

Niyə belə:
  * HTML-i parse etmək əvəzinə strukturlaşdırılmış JSON alırıq: daha dəqiq və sabit.
  * Rayonu sorğunun filtrindən bilirik (elanın öz yerində bəzən yalnız metro yazılır).
  * Yeni/köhnə tikili də filtrdən gəlir, ona görə hər elan dəqiq etiketlənir.
  * Saniyədə 1 sorğu: sayta yük verməmək üçün.
  * Telefon, ad və şəkil KİMİ ŞƏXSİ MƏLUMATLAR TOPLANMIR.

Nəticə:
  data/raw/<snapshot_id>/listings_raw.csv  — xam elanlar
  data/raw/<snapshot_id>/meta.json         — vaxt, hər qrup üzrə sayt sayı və toplanan say
  logs/scrape_<snapshot_id>.log
"""
import csv
import json
import logging
import sys
import time

import requests

from config import BUILDING_TYPES, DATA_RAW, DISTRICTS, LOGS, new_snapshot_id

URL = "https://bina.az/graphql"
PAGE_SIZE = 25          # bina.az bir sorğuda maksimum 25 elan qaytarır
PAUSE_SEC = 1.0         # sorğular arası fasilə
MAX_RETRIES = 4
MIN_COMPLETENESS = 0.95  # saytdakı elanların ən azı 95%-i toplanmalıdır

HEADERS = {
    "content-type": "application/json",
    # bina.az-ın GraphQL serveri bu başlığı tələb edir (CSRF qorunması)
    "apollo-require-preflight": "true",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
}

QUERY = """
query Rent($first: Int, $cursor: String, $filter: ItemFilter, $sort: ItemConnectionSort!) {
  itemsConnection(first: $first, after: $cursor, filter: $filter, sort: $sort) {
    totalCount
    pageInfo { hasNextPage endCursor }
    edges { node {
      id rooms floor floors isPaidDaily hasRepair hasBillOfSale hasMortgage isBusiness
      updatedAt path
      area { value units }
      price { total currency }
      location { id name }
    } }
  }
}
"""

COLUMNS = [
    "snapshot_id", "captured_at", "listing_id", "district_id", "district_name",
    "building_type_id", "building_type", "rooms", "area_m2", "area_units", "floor", "floors",
    "price", "currency", "is_paid_daily", "has_repair", "has_bill_of_sale", "has_mortgage",
    "is_agency", "location_id", "location_name", "updated_at", "url",
]


def fetch_page(session: requests.Session, filt: dict, cursor: str | None) -> dict:
    """Bir səhifəni gətirir. Müvəqqəti xətalarda (şəbəkə, 429, 5xx) gözləyib təkrarlayır."""
    body = {
        "operationName": "Rent",
        "query": QUERY,
        "variables": {"first": PAGE_SIZE, "cursor": cursor, "filter": filt, "sort": "BUMPED_AT_DESC"},
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.post(URL, json=body, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if "errors" in data:
                    raise RuntimeError(f"GraphQL xətası: {data['errors']}")
                return data["data"]["itemsConnection"]
            logging.warning("HTTP %s (cəhd %s)", r.status_code, attempt)
        except (requests.RequestException, ValueError) as e:
            logging.warning("Şəbəkə xətası (cəhd %s): %s", attempt, e)
        time.sleep(PAUSE_SEC * 2 ** attempt)  # 2, 4, 8, 16 san.
    raise RuntimeError("Səhifə alınmadı, sorğu dayandırıldı.")


def to_row(node: dict, snapshot_id: str, captured_at: str, did: str, bid: str) -> dict:
    area = node.get("area") or {}
    price = node.get("price") or {}
    loc = node.get("location") or {}
    return {
        "snapshot_id": snapshot_id,
        "captured_at": captured_at,
        "listing_id": node["id"],
        "district_id": did,
        "district_name": DISTRICTS[did][0],
        "building_type_id": bid,
        "building_type": BUILDING_TYPES[bid],
        "rooms": node.get("rooms"),
        "area_m2": area.get("value"),
        "area_units": area.get("units"),
        "floor": node.get("floor"),
        "floors": node.get("floors"),
        "price": price.get("total"),
        "currency": price.get("currency"),
        "is_paid_daily": node.get("isPaidDaily"),
        "has_repair": node.get("hasRepair"),
        "has_bill_of_sale": node.get("hasBillOfSale"),
        "has_mortgage": node.get("hasMortgage"),
        "is_agency": node.get("isBusiness"),
        "location_id": loc.get("id"),
        "location_name": loc.get("name"),
        "updated_at": node.get("updatedAt"),
        "url": "https://bina.az" + (node.get("path") or ""),
    }


def main() -> int:
    snapshot_id, captured_at = new_snapshot_id()
    out_dir = DATA_RAW / snapshot_id
    out_dir.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOGS / f"scrape_{snapshot_id}.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.info("Snapshot %s başladı", snapshot_id)

    session = requests.Session()
    meta = {"snapshot_id": snapshot_id, "captured_at": captured_at, "source": URL, "groups": []}
    seen: set[str] = set()
    rows_written = 0

    with open(out_dir / "listings_raw.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for did, (dname, _) in DISTRICTS.items():
            for bid, bname in BUILDING_TYPES.items():
                filt = {"cityId": "1", "categoryId": bid, "leased": True,
                        "paidDaily": False, "locationIds": [did]}
                cursor, site_total, got = None, None, 0
                while True:
                    conn = fetch_page(session, filt, cursor)
                    site_total = conn["totalCount"]
                    for edge in conn["edges"]:
                        node = edge["node"]
                        if node["id"] in seen:  # elan siyahıda yer dəyişərsə təkrar düşə bilər
                            continue
                        seen.add(node["id"])
                        writer.writerow(to_row(node, snapshot_id, captured_at, did, bid))
                        got += 1
                    time.sleep(PAUSE_SEC)
                    if not conn["pageInfo"]["hasNextPage"]:
                        break
                    cursor = conn["pageInfo"]["endCursor"]
                rows_written += got
                meta["groups"].append({"district": dname, "building_type": bname,
                                       "site_total": site_total, "collected": got})
                logging.info("%-10s %-13s saytda=%5s toplandı=%5s", dname, bname, site_total, got)

    meta["rows"] = rows_written
    site_sum = sum(g["site_total"] or 0 for g in meta["groups"])
    meta["completeness"] = round(rows_written / site_sum, 4) if site_sum else 0
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    logging.info("Bitdi: %s elan (saytda %s, tamlıq %.1f%%) -> %s",
                 rows_written, site_sum, meta["completeness"] * 100, out_dir)
    # Qoruma: elanların 95%-dən azı toplanıbsa (sayt cavab vermədi və s.), yarımçıq məlumat
    # Oracle-a və sayta getməsin — köhnə, tam məlumat qalsın (run_pipeline.bat burada dayanır).
    if meta["completeness"] < MIN_COMPLETENESS:
        logging.error("Tamlıq %.1f%% < %.0f%% — snapshot istifadə olunmayacaq",
                      meta["completeness"] * 100, MIN_COMPLETENESS * 100)
        (out_dir / "INCOMPLETE").write_text("yarımçıq toplama", encoding="utf-8")
        return 2
    print(f"SNAPSHOT_ID={snapshot_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
