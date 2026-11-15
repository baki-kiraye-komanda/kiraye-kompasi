"""
keep_awake.py — Streamlit Community Cloud pulsuz saytı bir neçə gün ziyarət olunmayanda «yuxuya» gedir.
GitHub Actions bu skripti hər 4 saatdan bir işlədir: saytı əsl brauzerdə açır, yuxudadırsa
«Yes, get this app back up!» düyməsini basır və sayt açılana qədər gözləyir.
"""
import sys

from playwright.sync_api import sync_playwright

URL = "https://kiraye-kompasi.streamlit.app/"
WAKE = "Yes, get this app back up"
READY = "Kirayə Kompası"          # sayt açılanda səhifə başlığında görünür


def main() -> int:
    with sync_playwright() as p:
        page = p.chromium.launch().new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(10_000)
        btn = page.get_by_role("button", name=WAKE)
        if btn.count():
            print("Sayt yuxuda idi — oyadılır...")
            btn.first.click()
        try:  # sayt tam açılana qədər (yuxudan sonra 1-3 dəqiqə)
            page.wait_for_function(f"document.title.includes({READY!r})", timeout=240_000)
        except Exception:
            print("XƏTA: sayt 4 dəqiqədə açılmadı. Başlıq:", page.title())
            return 1
        print("OK: sayt oyaqdır —", page.title())
    return 0


if __name__ == "__main__":
    sys.exit(main())
