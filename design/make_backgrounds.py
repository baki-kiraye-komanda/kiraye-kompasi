"""
make_backgrounds.py — "Neon kompas" fon şəkilləri (1920x1080 PNG) — Python + SVG.

Fonda yalnız sabit elementlər var: kosmik fon, naviqasiya paneli, başlıqlar, kart çərçivələri,
izah mətnləri. Bütün rəqəmlər Power BI vizuallarındadır (SVG ölçüləri və standart vizuallar),
ona görə məlumat yenilənəndə fon köhnəlmir.
Nəticə: design/backgrounds/bg_<səhifə>.png
"""
import random
import sys
from pathlib import Path

from layout import C, H, NAV, PAGES, RAIL, W, X0, nav_rect

OUT = Path(__file__).resolve().parent / "backgrounds"
FONT = "Segoe UI, Inter, sans-serif"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=16, color=None, weight=400, anchor="start", spacing=0, opacity=1):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color or C["text"]}" text-anchor="{anchor}" letter-spacing="{spacing}" opacity="{opacity}">{esc(s)}</text>')


def az_upper(s):
    return s.replace("i", "İ").upper()


def panel(x, y, w, h, accent=None, title=None, sub=None, r=22):
    acc = accent or C["cyan"]
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#glass)" stroke="url(#edge)" stroke-width="1.3"/>'
         f'<rect x="{x + 24}" y="{y - 1}" width="90" height="3" rx="1.5" fill="{acc}" filter="url(#bgl)"/>')
    if title:
        s += text(x + 24, y + 36, az_upper(title), 14, C["muted"], 700, spacing=1.8)
    if sub:
        s += text(x + 24, y + 58, sub, 14, C["dim"])
    return s


ICONS = {
    "home": "M-14 2 L0 -12 L14 2 M-10 -1 V13 H10 V-1",
    "map": "M0 14 C0 14 -11 3 -11 -3 A11 11 0 0 1 11 -3 C11 3 0 14 0 14 Z M0 -7 A4 4 0 1 0 0.01 -7",
    "wallet": "M-14 -8 H12 V12 H-14 Z M-14 -8 L6 -14 V-8 M5 2 H14",
    "chart": "M-13 13 H14 M-9 13 V1 M-1 13 V-6 M7 13 V-12",
    "gear": "M0 -6 A6 6 0 1 0 0.01 -6 M0 -14 V-9 M0 9 V14 M-14 0 H-9 M9 0 H14 M-10 -10 L-6 -6 M6 6 L10 10 M10 -10 L6 -6 M-6 6 L-10 10",
    "spark": "M0 -14 L3 -3 L14 0 L3 3 L0 14 L-3 3 L-14 0 L-3 -3 Z",
    "db": "M-12 -9 A12 4 0 1 0 12 -9 A12 4 0 1 0 -12 -9 V9 A12 4 0 0 0 12 9 V-9 M-12 0 A12 4 0 0 0 12 0",
    "code": "M-6 -10 L-14 0 L-6 10 M6 -10 L14 0 L6 10",
    "filter": "M-13 -11 H13 L3 1 V12 L-3 9 V1 Z",
    "globe": "M0 -13 A13 13 0 1 0 0.01 -13 M-13 0 H13 M0 -13 C-7 -6 -7 6 0 13 C7 6 7 -6 0 -13",
}


def icon(cx, cy, name, color, scale=1.0, width=2.2):
    return (f'<path d="{ICONS[name]}" transform="translate({cx},{cy}) scale({scale})" fill="none" '
            f'stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')


def defs():
    return f"""<defs>
<radialGradient id="bg" cx="25%" cy="0%" r="120%"><stop offset="0" stop-color="{C['bg2']}"/><stop offset="0.5" stop-color="{C['bg1']}"/><stop offset="1" stop-color="{C['bg0']}"/></radialGradient>
<radialGradient id="nebM"><stop offset="0" stop-color="{C['magenta']}" stop-opacity="0.30"/><stop offset="1" stop-color="{C['magenta']}" stop-opacity="0"/></radialGradient>
<radialGradient id="nebC"><stop offset="0" stop-color="{C['cyan']}" stop-opacity="0.22"/><stop offset="1" stop-color="{C['cyan']}" stop-opacity="0"/></radialGradient>
<radialGradient id="nebV"><stop offset="0" stop-color="{C['violet']}" stop-opacity="0.28"/><stop offset="1" stop-color="{C['violet']}" stop-opacity="0"/></radialGradient>
<linearGradient id="glass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1A2366" stop-opacity="0.62"/><stop offset="1" stop-color="#0B1036" stop-opacity="0.72"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C['cyan']}" stop-opacity="0.45"/><stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.06"/><stop offset="1" stop-color="{C['magenta']}" stop-opacity="0.35"/></linearGradient>
<linearGradient id="tg" x1="0" x2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="{C['cyan']}"/></linearGradient>
<pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0 H0 V48" fill="none" stroke="#FFFFFF" stroke-opacity="0.025"/></pattern>
<filter id="bgl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>"""


def backdrop():
    rnd = random.Random(7)
    s = (f'<rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="url(#grid)"/>'
         f'<ellipse cx="1700" cy="60" rx="560" ry="380" fill="url(#nebC)"/>'
         f'<ellipse cx="980" cy="1080" rx="700" ry="360" fill="url(#nebM)"/>'
         f'<ellipse cx="200" cy="420" rx="420" ry="420" fill="url(#nebV)"/>')
    for _ in range(150):
        s += (f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(0, H):.0f}" r="{rnd.choice([0.6, 0.8, 1.0, 1.4])}" '
              f'fill="#FFFFFF" opacity="{rnd.uniform(0.15, 0.6):.2f}"/>')
    return s


def rail(active):
    x, y, w, h = RAIL
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="30" fill="url(#glass)" stroke="url(#edge)"/>'
         f'<circle cx="{x + w / 2}" cy="{y + 58}" r="24" fill="none" stroke="{C["cyan"]}" stroke-width="2.5" filter="url(#bgl)"/>'
         f'<path d="M0 -15 L5 0 L0 15 L-5 0 Z" transform="translate({x + w / 2},{y + 58}) rotate(35)" fill="{C["magenta"]}"/>')
    for i, (key, lab, ic) in enumerate(NAV):
        bx, by, bw, bh = nav_rect(i)
        on = key == active
        col = C["cyan"] if on else C["muted"]
        if on:
            s += (f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="20" fill="{C["cyan"]}" fill-opacity="0.13" '
                  f'stroke="{C["cyan"]}" stroke-opacity="0.6" filter="url(#bgl)"/>'
                  f'<rect x="{x - 2}" y="{by + 18}" width="4" height="{bh - 36}" rx="2" fill="{C["cyan"]}" filter="url(#bgl)"/>')
        s += icon(bx + bw / 2, by + 32, ic, col) + text(bx + bw / 2, by + 68, lab, 12.5, col, 600, "middle")
    s += text(x + w / 2, y + h - 30, "v2.0", 11, C["dim"], 400, "middle")
    return s


def header(page):
    p = PAGES[page]
    return (text(X0, 78, p["title"], 42, "url(#tg)", 800) + text(X0, 110, p["subtitle"], 18, C["muted"])
            + f'<rect x="1560" y="40" width="336" height="48" rx="24" fill="#FFFFFF" fill-opacity="0.05" stroke="url(#edge)"/>'
            + f'<circle cx="1588" cy="64" r="6" fill="{C["teal"]}" filter="url(#bgl)"/>'
            + text(1604, 70, "BAKI KİRAYƏ KOMPASI", 15, C["text"], 800, spacing=1.6))


# ---------------------------------------------------------------- səhifələr
def page_home():
    c = PAGES["home"]["cards"]
    s = panel(*c["hero"], C["magenta"], "Əsas problem", "Kirayə ilə maaş arasındakı uçurum — Bakı şəhəri, DSK maaşı")
    for i, col in enumerate([C["cyan"], C["violet"], C["amber"]]):
        s += panel(*c[f"kpi{i}"], col)
    tiles = [("map", C["cyan"]), ("wallet", C["amber"]), ("chart", C["coral"]), ("gear", C["violet"])]
    for i, (ic, col) in enumerate(tiles):
        x, y, w, h = c[f"tile{i}"]
        s += panel(x, y, w, h, col)
        s += (f'<circle cx="{x + 60}" cy="{y + 76}" r="30" fill="{col}" fill-opacity="0.12" stroke="{col}" stroke-opacity="0.6" filter="url(#bgl)"/>'
              + icon(x + 60, y + 76, ic, col))
    return s


def page_market():
    c = PAGES["market"]["cards"]
    s = "".join(panel(*c[f"kpi{i}"], col) for i, col in enumerate([C["cyan"], C["violet"], C["magenta"], C["amber"], C["teal"]]))
    s += panel(*c["map"], C["cyan"], "Rayonlar xəritəsi", "Dairə = elan sayı · rəng = median · klik: süzgəc · sağ klik: elanlar")
    s += panel(*c["range"], C["magenta"], "Qiymət aralığı rayonlar üzrə", "Zolaq: elanların orta 50%-i (P25–P75) · nöqtə: median · ən az 30 elan")
    s += panel(*c["drivers"], C["violet"])
    x, y, w, h = c["filters"]
    s += panel(x, y, w, h, C["violet"])
    s += icon(x + 44, y + h / 2, "filter", C["muted"], 0.9) + text(x + 72, y + h / 2 + 6, "FİLTRLƏR", 14, C["muted"], 700, spacing=1.6)
    return s


def page_budget():
    c = PAGES["budget"]["cards"]
    x, y, w, h = c["controls"]
    s = panel(x, y, w, h, C["amber"], "Sizin seçim", "Dəyişdirin — bütün səhifə yenilənir")
    for yy, t in [(262, "1. Kirayəyə ayıra biləcəyim məbləğ"), (460, "2. Kirayəni neçə nəfər bölür?"),
                  (612, "3. Otaq sayı"), (764, "4. Tikili növü")]:
        s += text(x + 24, yy, t, 16, C["text"], 600)
    s += f'<line x1="{x + 24}" y1="878" x2="{x + w - 24}" y2="878" stroke="#FFFFFF" stroke-opacity="0.1"/>'
    s += text(x + 24, 908, "Hazır ssenarilər (bookmark) — klik edin", 15, C["amber"], 700)
    scn = [("Standart", "700 AZN · 1 nəfər · hamısı"), ("Tələbə", "350 AZN · 2 nəfər · 2 otaq"),
           ("Gənc mütəxəssis", "700 AZN · 1 nəfər · 1 otaq"), ("Ailə", "1200 AZN · 3 otaq")]
    for i, (t, sub) in enumerate(scn):
        bx, by, bw, bh = c[f"scn{i}"]
        s += (f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="14" fill="{C["amber"]}" fill-opacity="0.08" '
              f'stroke="{C["amber"]}" stroke-opacity="0.45"/>' + text(bx + 14, by + 25, t, 15, C["text"], 700)
              + text(bx + 14, by + 45, sub, 12, C["muted"]))
    s += panel(*c["headline"], C["amber"])
    bx, by, bw, bh = c["bars"]
    s += panel(bx, by, bw, bh, C["teal"], "Büdcəyə uyğun elanların payı", "Rayon üzrə · sağ klik → Drill through → real elanlar")
    lx = bx + 24
    for col, t in [(C["teal"], "50%+"), (C["amber"], "20–50%"), (C["coral"], "20%-dən az")]:
        s += f'<circle cx="{lx + 6}" cy="{by + 80}" r="6" fill="{col}"/>' + text(lx + 18, by + 85, t, 14, C["muted"])
        lx += 120
    s += panel(*c["savings"], C["cyan"], "Necə ucuzlaşdırmaq olar?", "Median kirayə addım-addım: seçdiyiniz otaq sayı üzrə")
    return s


def page_salary():
    c = PAGES["salary"]["cards"]
    s = "".join(panel(*c[f"kpi{i}"], col) for i, col in enumerate([C["violet"], C["coral"], C["amber"]]))
    bx, by, bw, bh = c["bars"]
    s += panel(bx, by, bw, bh, C["coral"], "Kirayə yükü sahələr üzrə", "Sahə maaşları ölkə üzrədir (DSK) · sahəyə klik — yuxarıdakı rəqəmlər dəyişir")
    lx = bx + bw - 440
    for col, t in [(C["teal"], "≤30% normal"), (C["amber"], "30–50%"), (C["coral"], "50%+ ağır")]:
        s += f'<circle cx="{lx + 6}" cy="{by + 32}" r="6" fill="{col}"/>' + text(lx + 18, by + 37, t, 14, C["muted"])
        lx += 145
    x, y, w, h = c["side"]
    s += panel(x, y, w, h, C["violet"], "Seçimlər və əlçatanlıq")
    s += text(x + 24, 392, "Otaq sayı", 15, C["text"], 600) + text(x + 24, 500, "Kirayəni neçə nəfər bölür?", 15, C["text"], 600)
    s += f'<line x1="{x + 24}" y1="600" x2="{x + w - 24}" y2="600" stroke="#FFFFFF" stroke-opacity="0.1"/>'
    s += text(x + 24, 628, "30% NORMASI ÜÇÜN LAZIM OLAN MAAŞ", 13, C["amber"], 800, spacing=1.5)
    return s


def page_method():
    c = PAGES["method"]["cards"]
    x, y, w, h = c["pipeline"]
    s = panel(x, y, w, h, C["cyan"], "Məlumatın yolu", "Hər addım ayrıca skriptdir · run_pipeline.bat həftədə bir dəfə hamısını işlədir")
    nodes = [("globe", "bina.az", "GraphQL · 22 262 elan", C["blue"]),
             ("code", "Python", "toplama: scrape.py", C["cyan"]), ("filter", "Təmizləmə", "10 qayda: clean.py", C["amber"]),
             ("db", "Oracle", "ulduz sxemi + view", C["coral"]), ("chart", "Power BI", "eyni ixrac qatı (CSV)", C["violet"]),
             ("spark", "Sayt + Gemini", "sadə dildə izah", C["magenta"])]
    n = len(nodes)
    nw = 236
    gap = (w - 48 - n * nw) / (n - 1)
    for i, (ic, t, sub, col) in enumerate(nodes):
        nx, ny = x + 24 + i * (nw + gap), y + 92
        s += (f'<rect x="{nx:.0f}" y="{ny}" width="{nw}" height="150" rx="18" fill="{col}" fill-opacity="0.09" stroke="{col}" '
              f'stroke-opacity="0.55" filter="url(#bgl)"/>' + icon(nx + 40, ny + 42, ic, col)
              + text(nx + 20, ny + 98, t, 22, C["text"], 700) + text(nx + 20, ny + 126, sub, 14.5, C["muted"]))
        if i < n - 1:
            ax = nx + nw + 6
            s += (f'<path d="M{ax:.0f} {ny + 75} H{ax + gap - 14:.0f} M{ax + gap - 22:.0f} {ny + 67} L{ax + gap - 13:.0f} {ny + 75} '
                  f'L{ax + gap - 22:.0f} {ny + 83}" stroke="{C["cyan"]}" stroke-width="2" fill="none" stroke-linecap="round"/>')
    s += panel(*c["funnel"], C["magenta"], "Məlumat hunisi", "Hər mərhələdə neçə elan qalır və niyə")
    s += panel(*c["valid"], C["teal"], "Xarici yoxlama", "Nəticəmiz rəsmi və müstəqil mənbələrlə üst-üstə düşür")
    x, y, w, h = c["glossary"]
    s += panel(x, y, w, h, C["violet"], "Anlayışlar")
    gl = [("Median", "ortadakı qiymət: yarısı ucuz, yarısı baha — lüks elanlar təsir etmir"),
          ("P25–P75", "elanların orta 50%-inin aralığı"),
          ("Kirayə yükü", "adambaşına median kirayə ÷ Bakıda orta maaş (norma 30%)"),
          ("Təkrar elan", "eyni mənzil fərqli elanla — bir dəfə sayılır"),
          ("Snapshot", "bir toplama seansı; hər həftə yenisi əlavə olunur")]
    for k, (t, d) in enumerate(gl):
        yy = y + 78 + k * 42
        s += (f'<circle cx="{x + 30}" cy="{yy - 5}" r="4" fill="{C["violet"]}"/>' + text(x + 46, yy, t, 16, C["text"], 700)
              + text(x + 190, yy, d, 15, C["muted"]))
    return s


def page_listings():
    c = PAGES["listings"]["cards"]
    s = panel(*c["head"], C["cyan"])
    s += panel(*c["table"], C["magenta"], "Elanlar (ucuzdan bahaya)", "Sütun başlığına klik — sıralama · link ikonu — elan bina.az-da açılır")
    x, y, w, h = c["side"]
    s += panel(x, y, w, h, C["violet"], "Filtrlər")
    for key, t in [("side_rooms", "Otaq sayı"), ("side_type", "Tikili növü"), ("side_agent", "Elanı verən")]:
        bx, by, bw, bh = c[key]
        s += text(bx + 8, by - 14, t, 16, C["text"], 600)
    bx, by, bw, bh = c["back"]
    s += (f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="24" fill="{C["cyan"]}" fill-opacity="0.12" '
          f'stroke="{C["cyan"]}" stroke-opacity="0.6" filter="url(#bgl)"/>' + text(bx + bw / 2, by + 31, "←  Geri", 17, C["cyan"], 700, "middle"))
    return s


def page_tooltip():
    return f'<rect width="480" height="320" rx="20" fill="{C["bg0"]}"/>'


BUILDERS = {"home": page_home, "market": page_market, "budget": page_budget, "salary": page_salary,
            "method": page_method, "listings": page_listings}


def svg_page(key):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'{defs()}{backdrop()}{rail(key)}{header(key)}{BUILDERS[key]()}</svg>')


def main():
    from playwright.sync_api import sync_playwright

    OUT.mkdir(exist_ok=True)
    jobs = [(k, svg_page(k), W, H) for k in BUILDERS]
    jobs.append(("tooltip", f'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="320">{defs()}{page_tooltip()}</svg>', 480, 320))
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        for key, svg, w, h in jobs:
            (OUT / f"{key}.svg").write_text(svg, encoding="utf-8")
            pg.set_viewport_size({"width": w, "height": h})
            pg.set_content(f'<html><body style="margin:0;background:transparent">{svg}</body></html>')
            pg.screenshot(path=str(OUT / f"bg_{key}.png"), omit_background=True, clip={"x": 0, "y": 0, "width": w, "height": h})
            print("ok", key)
        b.close()


if __name__ == "__main__":
    sys.exit(main())
