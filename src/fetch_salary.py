"""
fetch_salary.py — Dövlət Statistika Komitəsindən (DSK) orta aylıq nominal əmək haqqı
cədvəlini yükləyir (kontekst məlumatı: "kirayə maaşın neçə faizidir?").

Mənbə: https://www.stat.gov.az/source/labour/  (Əmək bazarı bölməsi)
Fayl:  "Average monthly nominal wages and salaries by economic activity" (.xls)
Nəticə: data/ref/salary_raw_<dil>.xls  (xam fayl; sonra load_salary.py oxuyub Oracle-a yazır)

Niyə rəsmi mənbə: müdafiədə "bu rəqəm haradandır?" sualına dəqiq cavab üçün.
"""
import sys
import time

import requests

from config import DATA_REF

# Azərbaycan dilindəki versiyalar: adlar dashboard-da elə göstərilir
URLS = {
    "az": "https://www.stat.gov.az/source/labour/az/004_2-3.xls",        # iqtisadi fəaliyyət növləri üzrə
    "region_az": "https://www.stat.gov.az/source/labour/az/009_6.xls",   # iqtisadi rayonlar və şəhərlər üzrə (Bakı)
}
TRIES = 3        # stat.gov.az bəzən ilk bağlantını kəsir — bir neçə dəfə cəhd edirik
PAUSE_SEC = 5    # cəhdlər arası fasilə


def download(url: str) -> bytes | None:
    """Faylı yükləyir; alınmasa None. 1000 baytdan kiçik cavab fayl deyil (xəta səhifəsidir)."""
    for attempt in range(1, TRIES + 1):
        try:
            r = requests.get(url, timeout=60, headers={"user-agent": "Mozilla/5.0"})
            if r.ok and len(r.content) > 1000:
                return r.content
            print(f"     cəhd {attempt}: status {r.status_code}")
        except requests.RequestException as e:
            print(f"     cəhd {attempt}: {type(e).__name__}")
        if attempt < TRIES:
            time.sleep(PAUSE_SEC)
    return None


def main() -> int:
    DATA_REF.mkdir(parents=True, exist_ok=True)
    usable = 0  # istifadə oluna bilən fayl sayı (yeni yüklənən və ya əvvəldən saxlanılan)
    for lang, url in URLS.items():
        path = DATA_REF / f"salary_raw_{lang}.xls"
        content = download(url)
        if content:
            path.write_bytes(content)
            print(f"OK  {lang}: {len(content)} bayt <- {url}")
            usable += 1
        elif path.exists():
            # Sayt cavab vermədi: əvvəl yüklənmiş fayl qalır. Maaş statistikası ildə bir dəfə yenilənir,
            # ona görə köhnə fayl adətən eyni rəqəmləri saxlayır.
            print(f"XƏBƏRDARLIQ {lang}: sayt cavab vermədi — əvvəl saxlanmış fayl istifadə olunur ({path.name})")
            usable += 1
        else:
            print(f"XETA {lang}: yüklənmədi və saxlanmış fayl da yoxdur")
    return 0 if usable == len(URLS) else 1


if __name__ == "__main__":
    sys.exit(main())
