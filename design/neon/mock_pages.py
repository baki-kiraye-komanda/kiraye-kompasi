"""
mock_pages.py — "Neon kompas" maketi: Ana səhifə və Bazar (real məlumatla).
Nəticə: design/neon/out/home.html, market.html (animasiyalı) + PNG.
Fon (panellər, kosmik fon) bir SVG/PNG-dir; vizuallar <img src="data:image/svg+xml"> kimi
yerləşir — Power BI-da Image vizualı ilə eyni prinsip.
"""
import math
import random
import sys
import urllib.parse
from pathlib import Path

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import components as K  # noqa: E402
from components import N, FONT  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = Path("/mnt/user-data/uploads/Final Project DATA AND GEN/exports")
OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)
W, H = 1920, 1080
X0, X1 = 144, 1896

L = pd.read_csv(SRC / "listings.csv")
D = pd.read_csv(SRC / "district.csv")
SAL_BAKU, SAL_COUNTRY = 1383.4, 1103.2


# ------------------------------------------------------------- fon
def stars(n=140, seed=7):
    rnd = random.Random(seed)
    out = ""
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.choice([0.6, 0.8, 1.0, 1.4])
        out += f"<circle cx='{x:.0f}' cy='{y:.0f}' r='{r}' fill='#FFFFFF' opacity='{rnd.uniform(0.15, 0.6):.2f}'/>"
    return out


def panel(x, y, w, h, accent=None, title=None, sub=None, r=22):
    acc = accent or N['cyan']
    s = (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='{r}' fill='url(#glass)' stroke='url(#edge)' stroke-width='1.3'/>"
         f"<rect x='{x + 24}' y='{y - 1}' width='90' height='3' rx='1.5' fill='{acc}' filter='url(#bgl)'/>")
    if title:
        s += K.label(x + 24, y + 36, title.upper(), N['muted'], 14, 700, 1.8)
    if sub:
        s += K.text(x + 24, y + 58, sub, 14, N['dim'], 400)
    return s


ICON = {
    "home": "M-14 2 L0 -12 L14 2 M-10 -1 V13 H10 V-1",
    "map": "M0 14 C0 14 -11 3 -11 -3 A11 11 0 0 1 11 -3 C11 3 0 14 0 14 Z M0 -7 A4 4 0 1 0 0.01 -7",
    "wallet": "M-14 -8 H12 V12 H-14 Z M-14 -8 L6 -14 V-8 M5 2 H14",
    "chart": "M-13 13 H14 M-9 13 V1 M-1 13 V-6 M7 13 V-12",
    "gear": "M0 -6 A6 6 0 1 0 0.01 -6 M0 -14 V-9 M0 9 V14 M-14 0 H-9 M9 0 H14",
}
NAV = [("home", "Ana səhifə"), ("map", "Bazar"), ("wallet", "Büdcəm"), ("chart", "Maaş"), ("gear", "Metod")]


def background(active, title, subtitle, panels):
    defs = (f"<radialGradient id='bg' cx='25%' cy='0%' r='120%'><stop offset='0' stop-color='{N['bg2']}'/>"
            f"<stop offset='0.5' stop-color='{N['bg1']}'/><stop offset='1' stop-color='{N['bg0']}'/></radialGradient>"
            f"<radialGradient id='nebM'><stop offset='0' stop-color='{N['magenta']}' stop-opacity='0.30'/><stop offset='1' stop-color='{N['magenta']}' stop-opacity='0'/></radialGradient>"
            f"<radialGradient id='nebC'><stop offset='0' stop-color='{N['cyan']}' stop-opacity='0.22'/><stop offset='1' stop-color='{N['cyan']}' stop-opacity='0'/></radialGradient>"
            f"<radialGradient id='nebV'><stop offset='0' stop-color='{N['violet']}' stop-opacity='0.28'/><stop offset='1' stop-color='{N['violet']}' stop-opacity='0'/></radialGradient>"
            f"<linearGradient id='glass' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#1A2366' stop-opacity='0.62'/>"
            f"<stop offset='1' stop-color='#0B1036' stop-opacity='0.70'/></linearGradient>"
            f"<linearGradient id='edge' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='{N['cyan']}' stop-opacity='0.45'/>"
            f"<stop offset='0.5' stop-color='#FFFFFF' stop-opacity='0.06'/><stop offset='1' stop-color='{N['magenta']}' stop-opacity='0.35'/></linearGradient>"
            f"<linearGradient id='tg' x1='0' x2='1'><stop offset='0' stop-color='#FFFFFF'/><stop offset='1' stop-color='{N['cyan']}'/></linearGradient>"
            f"<pattern id='grid' width='48' height='48' patternUnits='userSpaceOnUse'><path d='M48 0 H0 V48' fill='none' stroke='#FFFFFF' stroke-opacity='0.025'/></pattern>"
            + K.glow_filter("bgl", 3))
    s = (f"<rect width='{W}' height='{H}' fill='url(#bg)'/><rect width='{W}' height='{H}' fill='url(#grid)'/>"
         f"<ellipse cx='1700' cy='60' rx='560' ry='380' fill='url(#nebC)'/>"
         f"<ellipse cx='980' cy='1080' rx='700' ry='360' fill='url(#nebM)'/>"
         f"<ellipse cx='200' cy='420' rx='420' ry='420' fill='url(#nebV)'/>" + stars())
    # rail
    s += (f"<rect x='24' y='24' width='96' height='1032' rx='30' fill='url(#glass)' stroke='url(#edge)'/>"
          f"<circle cx='72' cy='82' r='24' fill='none' stroke='{N['cyan']}' stroke-width='2.5' filter='url(#bgl)'/>"
          f"<path d='M0 -15 L5 0 L0 15 L-5 0 Z' transform='translate(72,82) rotate(35)' fill='{N['magenta']}'/>")
    for i, (ic, lab) in enumerate(NAV):
        by = 150 + i * 112
        on = ic == active
        col = N['cyan'] if on else N['muted']
        if on:
            s += (f"<rect x='32' y='{by}' width='80' height='80' rx='20' fill='{N['cyan']}' fill-opacity='0.13' stroke='{N['cyan']}' stroke-opacity='0.6' filter='url(#bgl)'/>"
                  f"<rect x='22' y='{by + 18}' width='4' height='44' rx='2' fill='{N['cyan']}' filter='url(#bgl)'/>")
        s += (f"<path d='{ICON[ic]}' transform='translate(72,{by + 32})' fill='none' stroke='{col}' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'/>"
              + K.text(72, by + 68, lab, 12.5, col, 600, "middle"))
    # header
    s += (K.text(X0, 78, title, 42, "url(#tg)", 800) + K.text(X0, 110, subtitle, 18, N['muted'], 400)
          + f"<rect x='1560' y='40' width='336' height='48' rx='24' fill='#FFFFFF' fill-opacity='0.05' stroke='url(#edge)'/>"
          + f"<circle cx='1588' cy='64' r='6' fill='{N['teal']}' filter='url(#bgl)'/>"
          + K.label(1604, 70, "BAKI KİRAYƏ KOMPASI", N['text'], 15, 800, 1.6)
          + K.text(1896, 124, "bina.az · 17 428 unikal elan · 07.11.2026 · DSK 2025", 13, N['dim'], 400, "end"))
    s += panels
    return f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'><defs>{defs}</defs>{s}</svg>"


def place(svg_str, x, y, w, h):
    uri = "data:image/svg+xml;utf8," + urllib.parse.quote(svg_str)
    return f"<img style='position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px' src=\"{uri}\"/>"


def html(bg, imgs):
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>body{{margin:0;background:{N['bg0']}}}"
            f".s{{position:relative;width:{W}px;height:{H}px;transform-origin:0 0}}</style></head><body>"
            f"<div class='s' id='s'><img style='position:absolute;left:0;top:0' src=\"data:image/svg+xml;utf8,{urllib.parse.quote(bg)}\"/>"
            + "".join(imgs) + "</div><script>function f(){var k=Math.min(innerWidth/1920,innerHeight/1080);"
            "document.getElementById('s').style.transform='scale('+k+')';}onresize=f;f();</script></body></html>")


# ------------------------------------------------------------- data
city = L[L.is_baku_city == "Y"]
two = city[city.rooms_group == "2"]
med2 = two.price_azn.median()
burden = med2 / SAL_BAKU
mas = L[(L.is_baku_city == "N") & (L.rooms_group == "2")].price_azn.median()
dist = (L.groupby("district_name").agg(n=("price_azn", "size"), med=("price_azn", "median"),
                                       p25=("price_azn", lambda s: s.quantile(.25)),
                                       p75=("price_azn", lambda s: s.quantile(.75))).reset_index())
dist = dist.merge(D, on="district_name")
bins = np.histogram(L.price_azn.clip(upper=3000), bins=range(0, 3100, 100))[0].tolist()


def page_home():
    panels = (panel(X0, 194, 1010, 520, N['magenta'], "Əsas problem", "Kirayə ilə maaş arasındakı uçurum")
              + panel(1178, 194, 718, 160, N['cyan']) + panel(1178, 374, 718, 160, N['violet'])
              + panel(1178, 554, 718, 160, N['amber']))
    tiles = [("map", "Bazar xəritəsi", "Ən baha: Səbail", "1 250 AZN", N['cyan']),
             ("wallet", "Büdcəm nəyə çatır?", "700 AZN ilə elanların", "24%-i", N['amber']),
             ("chart", "Maaş və kirayə yükü", "20 sahədən 18-də yük", "50%+", N['coral']),
             ("gear", "Metodologiya", "22 262 xam elandan", "17 428 unikal", N['violet'])]
    tw = (X1 - X0 - 3 * 24) / 4
    for i, (ic, t, a, b, col) in enumerate(tiles):
        x = X0 + i * (tw + 24)
        panels += (f"<rect x='{x:.0f}' y='738' width='{tw:.0f}' height='318' rx='22' fill='url(#glass)' stroke='url(#edge)'/>"
                   f"<rect x='{x + 24:.0f}' y='737' width='90' height='3' rx='1.5' fill='{col}' filter='url(#bgl)'/>"
                   f"<circle cx='{x + 60:.0f}' cy='800' r='32' fill='{col}' fill-opacity='0.12' stroke='{col}' stroke-opacity='0.6' filter='url(#bgl)'/>"
                   f"<path d='{ICON[ic]}' transform='translate({x + 60:.0f},800)' fill='none' stroke='{col}' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'/>"
                   + K.text(x + 28, 878, t, 26, N['text'], 700) + K.text(x + 28, 918, a, 17, N['muted'])
                   + K.text(x + 28, 970, b, 40, col, 800) + K.text(x + 28, 1024, "Bax  →", 16, col, 700))
    bg = background("home", "Bakıda kirayə: maaş nəyə çatır?",
                    "bina.az-dakı bütün aylıq kirayə elanları əsasında real vəziyyət və şəxsi büdcə bələdçisi", panels)
    items = [(r.district_name.upper(), f"{r.med:,.0f} AZN".replace(",", " "),
              N['coral'] if r.med > 1000 else N['teal'], f"{'▲' if r.med > 1000 else '▼'} {abs(r.med / 1000 - 1):.0%} şəhər medianından")
             for r in dist.sort_values("med", ascending=False).itertuples() if r.n >= 30]
    items.insert(0, ("2 OTAQLI", f"{med2:,.0f} AZN".replace(",", " "), N['magenta'], f"= Bakıda maaşın {burden:.0%}-i"))
    items.insert(1, ("MASAZIR, 2 OTAQ", f"{mas:,.0f} AZN", N['teal'], f"= maaşın {mas / SAL_BAKU:.0%}-i · normaya uyğun"))
    items.insert(2, ("VASİTƏÇİ / MÜLKİYYƏTÇİ", "1 000 / 800 AZN", N['amber'], "+25%"))
    imgs = [place(K.ticker(1752, 46, items), X0, 132, 1752, 46)]
    # hero
    imgs.append(place(K.ring_gauge(400, burden, 0.30, alt=(mas / SAL_BAKU, "Masazır")), X0 + 40, 270, 400, 400))
    hero = (K.text(0, 40, "2 otaqlı mənzilin median kirayəsi", 20, N['muted'], 500)
            + K.count_up(0, 112, med2, 0, suffix=" AZN", size=72, color=N['text'], weight=800)
            + K.fade_in(K.text(0, 158, f"Bakıda orta aylıq maaş {SAL_BAKU:,.0f} AZN · kirayədən sonra qalır {SAL_BAKU - med2:,.0f} AZN".replace(",", " "), 17, N['muted']), 0.9)
            + K.fade_in(K.text(0, 214, "Kirayə yükü", 15, N['muted'], 700), 1.0))
    rows = [("Bakı şəhəri", burden, N['magenta']), ("Masazır", mas / SAL_BAKU, N['teal']), ("Ölkə ortası ilə", med2 / SAL_COUNTRY, N['violet'])]
    for i, (nm, v, col) in enumerate(rows):
        y = 240 + i * 52
        hero += (K.text(0, y + 16, nm, 16, N['text'], 600)
                 + f"<rect x='150' y='{y + 2}' width='330' height='18' rx='9' fill='#FFFFFF' fill-opacity='0.06'/>"
                 + f"<rect x='150' y='{y + 2}' width='0' height='18' rx='9' fill='{col}' filter='url(#hgl)'>"
                 f"<animate attributeName='width' to='{330 * min(v, 1):.0f}' dur='1s' begin='{1.0 + i * 0.25:.2f}s' fill='freeze'/></rect>"
                 + K.fade_in(K.text(492, y + 17, f"{v:.0%}", 18, col, 800), 1.6 + i * 0.25))
    nx = 150 + 330 * 0.30
    hero += (f"<line x1='{nx}' y1='226' x2='{nx}' y2='{240 + 3 * 52 - 20}' stroke='{N['teal']}' stroke-width='2' stroke-dasharray='4 4'/>"
             + K.text(nx, 222, "norma 30%", 12, N['teal'], 700, "middle"))
    imgs.append(place(K.svg(560, 420, hero, K.glow_filter("hgl", 4)), X0 + 470, 270, 560, 420))
    # KPI-lar
    bt = L.building_type.value_counts()
    k1 = K.kpi(718, 160, "Təhlil olunan unikal elan", len(L), sub="bina.az · təkrarlar çıxarılıb", accent=N['cyan'],
               mini=K.mini_split(380, 70, 300, [("Yeni tikili", bt["Yeni tikili"], N['cyan']), ("Köhnə", bt["Köhnə tikili"], N['magenta'])]))
    k2 = K.kpi(718, 160, "Median kirayə, AZN", L.price_azn.median(), sub="orta 50%: 750 – 1 400 AZN", accent=N['violet'],
               mini=K.mini_hist(380, 28, 310, 100, bins, marker_idx=10, color=N['violet'], color2=N['magenta'])
               + K.text(380, 146, "0", 11, N['dim']) + K.text(690, 146, "3 000+ AZN", 11, N['dim'], 400, "end"))
    k3 = K.kpi(718, 160, "Bakıda orta aylıq maaş, AZN", SAL_BAKU, sub="DSK, 2025 · nominal", accent=N['amber'],
               mini=K.mini_compare(380, 40, 310, [("Bakı", SAL_BAKU, N['amber']), ("Ölkə", SAL_COUNTRY, N['dim'])]))
    for i, k in enumerate([k1, k2, k3]):
        imgs.append(place(k, 1178, 194 + i * 180, 718, 160))
    return html(bg, imgs)


def page_market():
    kp = [(X0 + i * (1752 - 4 * 24) / 5 + i * 24, 150) for i in range(5)]
    kw = (1752 - 4 * 24) / 5
    panels = "".join(panel(round(x), y, round(kw), 150, c) for (x, y), c in
                     zip(kp, [N['cyan'], N['violet'], N['magenta'], N['amber'], N['teal']]))
    panels += panel(X0, 324, 860, 610, N['cyan'], "Rayonlar xəritəsi", "Dairə = elan sayı · rəng = median · üzərinə gəlin, sağ klik → elanlar")
    panels += panel(1028, 324, 868, 610, N['magenta'], "Qiymət aralığı rayonlar üzrə", "Zolaq: elanların orta 50%-i (P25–P75) · nöqtə: median")
    panels += panel(X0, 958, 1752, 98, N['violet'])
    panels += K.label(X0 + 70, 1013, "FİLTRLƏR", N['muted'], 14, 700, 1.8)
    for i, t in enumerate(["Otaq sayı", "Tikili növü", "Ərazi", "Elanı verən"]):
        x = X0 + 260 + i * 380
        panels += (K.text(x, 990, t, 12, N['dim'], 600)
                   + f"<rect x='{x}' y='1000' width='340' height='34' rx='10' fill='#FFFFFF' fill-opacity='0.05' stroke='url(#edge)'/>"
                   + K.text(x + 14, 1023, "Hamısı", 14, N['text'], 500)
                   + f"<path d='M{x + 314} 1013 l6 6 l6 -6' fill='none' stroke='{N['cyan']}' stroke-width='2'/>")
    bg = background("map", "Bazar xəritəsi", "Rayonlar üzrə median kirayə, qiymət aralığı və elan sayı", panels)
    ag = (L.is_agency == "Y").mean()
    kpis = [
        K.kpi(round(kw), 150, "Elan sayı", len(L), sub="unikal", accent=N['cyan']),
        K.kpi(round(kw), 150, "Median kirayə, AZN", L.price_azn.median(), sub="bütün mənzillər", accent=N['violet']),
        K.kpi(round(kw), 150, "Median 1 m², AZN", L.price_per_m2.median(), dec=1, sub="ayda", accent=N['magenta']),
        K.kpi(round(kw), 150, "Yeni / köhnə tikili", 1100, sub="köhnə tikili: 700 AZN", accent=N['amber']),
        K.kpi(round(kw), 150, "Vasitəçi payı", ag * 100, suffix="%", sub="vasitəçi +25% baha", accent=N['teal'],
              mini=K.mini_ring(round(kw) - 60, 80, 34, ag, N['teal'], "")),
    ]
    imgs = [place(k, round(x), y, round(kw), 150) for k, (x, y) in zip(kpis, kp)]
    pts = [(r.district_name, r.latitude, r.longitude, r.n, r.med) for r in dist.itertuples() if r.n >= 5]
    imgs.append(place(K.bubble_map(820, 520, pts), X0 + 20, 404, 820, 520))
    rows = [(r.district_name, r.p25, r.med, r.p75, r.n) for r in dist.sort_values("med", ascending=False).itertuples() if r.n >= 30]
    imgs.append(place(K.range_chart(830, 520, rows, L.price_azn.median()), 1046, 404, 830, 520))
    return html(bg, imgs)


def main():
    from playwright.sync_api import sync_playwright
    pages = {"home": page_home(), "market": page_market()}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        for k, h in pages.items():
            f = OUT / f"{k}.html"
            f.write_text(h, encoding="utf-8")
            pg.goto(f.as_uri())
            pg.wait_for_timeout(3500)
            pg.screenshot(path=str(OUT / f"{k}.png"))
            print("ok", k)
        b.close()


if __name__ == "__main__":
    main()
