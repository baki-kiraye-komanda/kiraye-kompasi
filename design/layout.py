"""
layout.py — "Neon kompas" dizayn sistemi: rənglər, səhifələr və hər kartın koordinatları.

Bir mənbə: fon şəkilləri (make_backgrounds.py), Power BI vizuallarının yeri (make_report.py)
və SVG ölçülərinin ölçüsü (neon/dax_svg.py) bu koordinatlara uyğundur.
Kətan: 1920 x 1080 px.
"""

W, H = 1920, 1080

C = {
    "bg0": "#04061A", "bg1": "#0A0F33", "bg2": "#131A4D", "panel": "#0D1440",
    "text": "#F2F5FF", "muted": "#9AA6D6", "dim": "#5B6699",
    "cyan": "#22E5FF", "teal": "#2DF5C4", "magenta": "#FF3FD1", "violet": "#8B5CFF",
    "amber": "#FFC23F", "coral": "#FF5A7A", "blue": "#3D8BFF",
}

RAIL = (24, 24, 96, 1032)
X0, X1 = 144, 1896
GAP = 24

NAV = [  # (açar, etiket, ikon)
    ("home", "Ana səhifə", "home"),
    ("market", "Bazar", "map"),
    ("budget", "Büdcəm", "wallet"),
    ("salary", "Maaş", "chart"),
    ("method", "Metod", "gear"),
]
NAV_Y0, NAV_STEP, NAV_SIZE = 150, 112, 80


def nav_rect(i):
    return (32, NAV_Y0 + i * NAV_STEP, NAV_SIZE, NAV_SIZE)


def row(y, h, n, x0=X0, x1=X1, gap=GAP):
    w = (x1 - x0 - gap * (n - 1)) / n
    return [(round(x0 + i * (w + gap)), y, round(w), h) for i in range(n)]


PAGES = {
    "home": {
        "title": "Bakıda kirayə: maaş nəyə çatır?",
        "subtitle": "bina.az-dakı bütün aylıq kirayə elanları əsasında problem, səbəblər və şəxsi həll yolu",
        "cards": {
            "ticker": (X0, 136, 1752, 46),
            "hero": (X0, 198, 1010, 516),
            "hero_img": (X0 + 16, 260, 978, 448),
            **{f"kpi{i}": (1178, 198 + i * 178, 718, 160) for i in range(3)},
            **{f"tile{i}": r for i, r in enumerate(row(738, 318, 4))},
            "tiles_img": (X0, 738, 1752, 318),
        },
    },
    "market": {
        "title": "Bazar: harada və niyə bahadır?",
        "subtitle": "Rayonlar, qiymət aralıqları və qiyməti müəyyən edən amillər · filtrlər bütün səhifəni dəyişir",
        "cards": {
            **{f"kpi{i}": r for i, r in enumerate(row(150, 136, 5))},
            "map": (X0, 306, 860, 488),
            "range": (1028, 306, 868, 488),
            "range_img": (1044, 370, 836, 412),
            "drivers": (X0, 814, 1752, 150),
            "drivers_img": (X0 + 16, 824, 1720, 134),
            "filters": (X0, 984, 1752, 72),
        },
    },
    "budget": {
        "title": "Büdcəm nəyə çatır?",
        "subtitle": "Kirayəyə ayıra biləcəyiniz məbləği seçin — hansı rayonlarda neçə elan uyğundur və necə ucuzlaşdırmaq olar",
        "cards": {
            "controls": (X0, 150, 420, 906),
            "ctl_budget": (X0 + 16, 276, 388, 160),
            "ctl_people": (X0 + 16, 476, 388, 80),
            "ctl_rooms": (X0 + 16, 628, 388, 80),
            "ctl_type": (X0 + 16, 780, 388, 80),
            **{f"scn{i}": (X0 + 16 + (i % 2) * 202, 924 + (i // 2) * 68, 186, 58) for i in range(4)},
            "headline": (588, 150, 1308, 250),
            "headline_img": (604, 160, 1276, 230),
            "bars": (588, 424, 660, 632),
            "savings": (1272, 424, 624, 632),
            "savings_img": (1278, 488, 612, 560),
        },
    },
    "salary": {
        "title": "Kimin maaşı kirayəyə çatır?",
        "subtitle": "Median kirayə müxtəlif sahələrdə orta maaşın neçə faizini aparır · sahəyə klik edin",
        "cards": {
            **{f"kpi{i}": r for i, r in enumerate(row(150, 150, 3))},
            "bars": (X0, 324, 1180, 732),
            "side": (1348, 324, 548, 732),
            "side_rooms": (1364, 404, 516, 70),
            "side_people": (1364, 512, 516, 70),
            "afford_img": (1364, 640, 516, 400),
        },
    },
    "method": {
        "title": "Metodologiya: rəqəmlərə niyə inanmaq olar?",
        "subtitle": "Məlumat haradan gəlir, necə təmizlənir və nəticə rəsmi mənbələrlə necə yoxlanılıb",
        "cards": {
            "pipeline": (X0, 150, 1752, 280),
            "funnel": (X0, 454, 860, 602),
            "funnel_img": (X0 + 16, 520, 828, 520),
            "valid": (1028, 454, 868, 290),
            "valid_img": (1044, 524, 836, 216),
            "glossary": (1028, 768, 868, 288),
        },
    },
    "listings": {  # drill-through səhifəsi (rayona sağ klik → Drill through → Elanlar)
        "title": "Rayon üzrə real elanlar",
        "subtitle": "Rayona sağ klik → Drill through → «Elanlar» · link ikonu elanı bina.az-da açır",
        "cards": {
            "head": (X0, 150, 1752, 140),
            "table": (X0, 314, 1340, 742),
            "side": (1508, 314, 388, 742),
            "side_rooms": (1524, 420, 356, 80),
            "side_type": (1524, 560, 356, 80),
            "side_agent": (1524, 700, 356, 80),
            "back": (1424, 44, 120, 48),
        },
    },
}
