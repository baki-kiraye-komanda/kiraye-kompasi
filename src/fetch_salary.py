"""
fetch_salary.py — Dövlət Statistika Komitəsindən (DSK) orta aylıq nominal əmək haqqı
cədvəlini yükləyir (kontekst məlumatı: "kirayə maaşın neçə faizidir?").

Mənbə: https://www.stat.gov.az/source/labour/  (Əmək bazarı bölməsi)
Fayl:  "Average monthly nominal wages and salaries by economic activity" (.xls)
Nəticə: data/ref/salary_raw_<dil>.xls  (xam fayl, sonra parse_salary ilə emal olunur)

Niyə rəsmi mənbə: müdafiədə "bu rəqəm haradandır?" sualına dəqiq cavab üçün.
"""
import sys

import requests

from config import DATA_REF

# Azərbaycan dilindəki versiyalar: adlar dashboard-da elə göstərilir
URLS = {
    "az": "https://www.stat.gov.az/source/labour/az/004_2-3.xls",        # iqtisadi fəaliyyət növləri üzrə
    "region_az": "https://www.stat.gov.az/source/labour/az/009_6.xls",   # iqtisadi rayonlar və şəhərlər üzrə (Bakı)
}


def main() -> int:
    DATA_REF.mkdir(parents=True, exist_ok=True)
    ok = 0
    for lang, url in URLS.items():
        try:
            r = requests.get(url, timeout=60, headers={"user-agent": "Mozilla/5.0"})
            if r.ok and len(r.content) > 1000:
                (DATA_REF / f"salary_raw_{lang}.xls").write_bytes(r.content)
                print(f"OK  {lang}: {len(r.content)} bayt <- {url}")
                ok += 1
            else:
                print(f"XETA {lang}: status {r.status_code}")
        except requests.RequestException as e:
            print(f"XETA {lang}: {e}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
