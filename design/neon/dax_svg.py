"""
dax_svg.py — Power BI üçün animasiyalı SVG ölçülərini (DAX) yaradır -> tables/Vizual.tmdl

Prinsip (turizm layihəsindəki kimi): DAX ölçüsü SVG mətni qurur və
"data:image/svg+xml;utf8,..." qaytarır. Standart Image vizualı (sourceType = imageData)
bu şəkli göstərir. Filtr dəyişəndə ölçü yenidən hesablanır və animasiya təzədən oynayır.
Animasiya: SMIL — <set>, <animate>, <animateTransform>.

Hər ölçü analizin bir sualına cavab verir (təkrar qrafik yoxdur):
  Ana səhifə  — problem nə qədər böyükdür?  (ticker, hero, 3 KPI, plitələr)
  Bazar       — harada və niyə bahadır?     (5 KPI, rayon aralıqları, qiymət amilləri)
  Büdcəm      — mənə nə çatır, necə ucuzlaşdırım? (büdcə halqası, qənaət yolları)
  Maaş        — kimin maaşı çatır?          (maaş, yük halqası, lazım olan maaş)
  Metod       — rəqəmlərə niyə inanmaq olar? (huni, xarici yoxlama)
"""
import uuid
from pathlib import Path

C = {"bg0": "#04061A", "panel": "#0D1440", "text": "#F2F5FF", "muted": "#9AA6D6", "dim": "#5B6699",
     "cyan": "#22E5FF", "teal": "#2DF5C4", "magenta": "#FF3FD1", "violet": "#8B5CFF",
     "amber": "#FFC23F", "coral": "#FF5A7A", "blue": "#3D8BFF"}
OUT = Path(__file__).resolve().parents[2] / "powerbi" / "BakuKiraye.SemanticModel" / "definition" / "tables" / "Vizual.tmdl"

STYLE = ("text{font-family:Segoe UI,Inter,sans-serif}"
         f".l{{font-size:13px;font-weight:700;letter-spacing:1.6px;fill:{C['muted']}}}"
         f".m{{fill:{C['muted']}}}.d{{fill:{C['dim']}}}.t{{fill:{C['text']}}}")


def S(s):
    """Statik SVG mətni -> DAX sətri (ikiqat dırnaq qaçırılır)."""
    return '"' + s.replace('"', '""') + '"'


def NUM(expr, fmt="#,0"):
    return f'SUBSTITUTE(FORMAT({expr}, "{fmt}", "en-US"), ",", " ")'


def GL(fid="gl", std=4):
    return (f"<filter id='{fid}' x='-50%' y='-50%' width='200%' height='200%'><feGaussianBlur stdDeviation='{std}' result='b'/>"
            f"<feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge></filter>")


def GRAD(gid, c1, c2, vertical=False, o1=1, o2=1):
    xy = "x1='0' y1='1' x2='0' y2='0'" if vertical else "x1='0' y1='0' x2='1' y2='0'"
    return (f"<linearGradient id='{gid}' {xy}><stop offset='0' stop-color='{c1}' stop-opacity='{o1}'/>"
            f"<stop offset='1' stop-color='{c2}' stop-opacity='{o2}'/></linearGradient>")


def CU(var, x, y, size, color=None, anchor="start", fmt="#,0", prefix='""', suffix='""', dur=0.9, weight=700,
       begin=0.0):
    """Rəqəm 0-dan dəyərə qədər "qaçır" (12 kadr)."""
    color = color or C["text"]
    st = dur / 12
    return ('CONCATENATEX(GENERATESERIES(1, 12, 1), '
            f'"<text x=\'{x}\' y=\'{y}\' font-size=\'{size}\' font-weight=\'{weight}\' fill=\'{color}\' '
            f'text-anchor=\'{anchor}\' opacity=\'0\'>" & {prefix} & '
            f'SUBSTITUTE(FORMAT({var} * (1 - POWER(1 - [Value] / 12, 3)), "{fmt}", "en-US"), ",", " ") & {suffix} & '
            f'"<set attributeName=\'opacity\' to=\'1\' begin=\'" & FORMAT({begin} + ([Value] - 1) * {st:.4f}, "0.000", "en-US") & "s\' " & '
            f'IF([Value] = 12, "fill=\'freeze\'", "dur=\'{st:.4f}s\'") & "/></text>", "", [Value], ASC)')


def FADE(body_expr, begin=0.8, dur=0.4):
    return (S(f"<g opacity='0'><animate attributeName='opacity' from='0' to='1' begin='{begin}s' dur='{dur}s' fill='freeze'/>")
            + f" & {body_expr} & " + S("</g>"))


def TXT(x, y, expr, size=14, color=None, weight=400, anchor="start", cls=None):
    c = f"class='{cls}'" if cls else f"fill='{color or C['text']}'"
    return (S(f"<text x='{x}' y='{y}' font-size='{size}' font-weight='{weight}' {c} text-anchor='{anchor}'>")
            + f" & {expr} & " + S("</text>"))


def DTXT(x_expr, y, expr, size=14, color=None, weight=400, anchor="start"):
    """Mətn, x koordinatı DAX ifadəsidir."""
    return (S("<text x='") + f" & {x_expr} & " + S(f"' y='{y}' font-size='{size}' font-weight='{weight}' fill='{color or C['text']}' text-anchor='{anchor}'>")
            + f" & {expr} & " + S("</text>"))


def STXT(x, y, s, size=14, color=None, weight=400, anchor="start", cls=None, spacing=0):
    c = f"class='{cls}'" if cls else f"fill='{color or C['text']}'"
    sp = f" letter-spacing='{spacing}'" if spacing else ""
    return S(f"<text x='{x}' y='{y}' font-size='{size}' font-weight='{weight}' {c} text-anchor='{anchor}'{sp}>{s}</text>")


def LABEL(x, y, s):
    return S(f"<text x='{x}' y='{y}' class='l'>{s}</text>")


def BAR(x, y, w_expr, h, fill, begin=0.2, dur=0.8, rx=None, extra=""):
    """Üfüqi zolaq: eni animasiya ilə 0-dan w_expr-ə qədər böyüyür."""
    rx = h / 2 if rx is None else rx
    return (S(f"<rect x='{x}' y='{y}' width='0' height='{h}' rx='{rx}' fill='{fill}' {extra}><animate attributeName='width' to='")
            + f' & FORMAT({w_expr}, "0.0", "en-US") & '
            + S(f"' dur='{dur}s' begin='{begin}s' fill='freeze'/></rect>"))


def WRAP(w, h, defs, parts, vars_=""):
    body = "\n\t\t\t\t& ".join(parts)
    return (f"{vars_}\nVAR _svg =\n\t"
            + S(f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'><defs>{defs}</defs><style>{STYLE}</style>")
            + f"\n\t\t\t\t& {body}\n\t\t\t\t& " + S("</svg>")
            + '\nRETURN "data:image/svg+xml;utf8," & SUBSTITUTE(SUBSTITUTE(_svg, "%", "%25"), "#", "%23")')


CITY = 'Rayon[Ərazi] = "Bakı şəhəri"'
PRICE = "Elanlar[Kirayə (AZN/ay)]"
M = {}  # ad -> (izah, DAX)


def add(name, desc, dax):
    M[name] = (desc, dax)


# ======================================================================= ANA SƏHİFƏ
def m_ticker():
    w, h = 1752, 46
    x0 = 236
    vars_ = f"""VAR _sal = [Bakı orta maaşı]
VAR _m2 = CALCULATE([Median kirayə], Elanlar[Otaq] = "2", {CITY}, REMOVEFILTERS(Rayon[Rayon]))
VAR _mas = CALCULATE([Median kirayə], Elanlar[Otaq] = "2", Rayon[Ərazi] <> "Bakı şəhəri")
VAR _city = CALCULATE([Median kirayə], {CITY})
VAR _ag = CALCULATE([Median kirayə], Elanlar[Elanı verən] = "Vasitəçi", {CITY})
VAR _ow = CALCULATE([Median kirayə], Elanlar[Elanı verən] = "Mülkiyyətçi", {CITY})
VAR _nw = CALCULATE([Median kirayə], Elanlar[Tikili növü] = "Yeni tikili", {CITY})
VAR _od = CALCULATE([Median kirayə], Elanlar[Tikili növü] = "Köhnə tikili", {CITY})
VAR _d = FILTER(ADDCOLUMNS(VALUES(Rayon[Rayon]), "@m", [Median kirayə], "@n", [Elan sayı], "@q", [Median 1 m²]), [@n] >= 30)
VAR _items = UNION(
    ROW("o", 1, "k", "2 OTAQLI · BAKI", "v", {NUM('_m2')} & " AZN", "c", "{C['magenta']}", "e", "= orta maaşın " & FORMAT(DIVIDE(_m2, _sal), "0%") & "-i"),
    ROW("o", 2, "k", "NORMAYA SIĞMAQ ÜÇÜN MAAŞ", "v", {NUM('_m2 / 0.3')} & " AZN", "c", "{C['amber']}", "e", FORMAT(DIVIDE(_m2 / 0.3, _sal), "0.0") & " × Bakı ortası"),
    ROW("o", 3, "k", "MASAZIR · 2 OTAQ", "v", {NUM('_mas')} & " AZN", "c", "{C['teal']}", "e", "= maaşın " & FORMAT(DIVIDE(_mas, _sal), "0%") & "-i · normaya yaxın"),
    ROW("o", 4, "k", "VASİTƏÇİ / MÜLKİYYƏTÇİ", "v", {NUM('_ag')} & " / " & {NUM('_ow')} & " AZN", "c", "{C['coral']}", "e", "vasitəçi +" & FORMAT(DIVIDE(_ag, _ow) - 1, "0%")),
    ROW("o", 5, "k", "YENİ / KÖHNƏ TİKİLİ", "v", {NUM('_nw')} & " / " & {NUM('_od')} & " AZN", "c", "{C['violet']}", "e", "köhnə tikili −" & FORMAT(1 - DIVIDE(_od, _nw), "0%")),
    SELECTCOLUMNS(_d, "o", 10 + RANKX(_d, [@m] + [@q] / 1000, , DESC), "k", UPPER(SUBSTITUTE(Rayon[Rayon], "i", "İ")), "v", {NUM('[@m]')} & " AZN",
        "c", IF([@m] > _city, "{C['coral']}", "{C['teal']}"),
        "e", IF([@m] > _city, "▲ +", "▼ −") & FORMAT(ABS(DIVIDE([@m], _city) - 1), "0%") & " şəhər medianından")
)
VAR _plain = CONCATENATEX(_items, [k] & "  " & [v] & "  " & [e] & "            ✦            ", "")
VAR _L = ROUND(LEN(_plain) * 8.3, 0)
VAR _dur = FORMAT(_L / 75, "0.0", "en-US")
VAR _body = CONCATENATEX(_items,
    "<tspan fill='{C['muted']}' font-weight='600' font-size='13' letter-spacing='1.2'>" & [k] & "  </tspan><tspan fill='{C['text']}' font-weight='700'>" & [v] & "</tspan><tspan fill='" & [c] & "' font-weight='600'>  " & [e] & "</tspan><tspan fill='{C['violet']}'>            ✦            </tspan>",
    "", [o], ASC)"""
    defs = (f"<linearGradient id='fg' x1='0' x2='1'><stop offset='0' stop-color='black'/><stop offset='0.04' stop-color='white'/>"
            f"<stop offset='0.96' stop-color='white'/><stop offset='1' stop-color='black'/></linearGradient>"
            f"<mask id='tm'><rect x='{x0}' y='0' width='{w - x0}' height='{h}' fill='url(#fg)'/></mask>"
            + GRAD("tb", C["magenta"], C["cyan"], o1=0.5, o2=0.35) + GL("tg", 3))
    parts = [
        S(f"<rect x='1' y='1' width='{w - 2}' height='{h - 2}' rx='{h / 2}' fill='{C['panel']}' fill-opacity='0.8' stroke='url(#tb)' stroke-width='1.4'/>"
          f"<rect x='8' y='8' width='{x0 - 22}' height='{h - 16}' rx='{(h - 16) / 2}' fill='{C['magenta']}' fill-opacity='0.15' stroke='{C['magenta']}' stroke-opacity='0.6'/>"
          f"<circle cx='28' cy='{h / 2}' r='5' fill='{C['magenta']}' filter='url(#tg)'><animate attributeName='opacity' values='1;0.2;1' dur='1.4s' repeatCount='indefinite'/></circle>"
          f"<text x='42' y='{h / 2 + 5}' font-size='13' font-weight='800' letter-spacing='1.8' fill='{C['magenta']}'>CANLI BAZAR</text>"
          f"<g mask='url(#tm)'><g><animateTransform attributeName='transform' type='translate' from='{x0} 0' to='"),
        f'FORMAT({x0} - _L, "0", "en-US")',
        S("' dur='"), "_dur",
        S(f"s' repeatCount='indefinite'/><text x='0' y='{h / 2 + 6}' font-size='16' xml:space='preserve' textLength='"),
        "_L", S("' lengthAdjust='spacing'>"), "_body",
        S(f"</text><text x='"), "_L", S(f"' y='{h / 2 + 6}' font-size='16' xml:space='preserve' textLength='"),
        "_L", S("' lengthAdjust='spacing'>"), "_body", S("</text></g></g>"),
    ]
    add("VZ Ticker", "Ana səhifə: bəgüşən sətir (əsas faktlar + rayon medianları)", WRAP(w, h, defs, parts, vars_))


def m_hero():
    w, h = 978, 448
    size, c = 400, 200
    r, sw = 150, 30
    import math
    circ = 2 * math.pi * r
    vars_ = f"""VAR _sal = [Bakı orta maaşı]
VAR _cty = [Ölkə orta maaşı]
VAR _m2 = CALCULATE([Median kirayə], Elanlar[Otaq] = "2", {CITY})
VAR _mas = CALCULATE([Median kirayə], Elanlar[Otaq] = "2", Rayon[Ərazi] <> "Bakı şəhəri")
VAR _p = DIVIDE(_m2, _sal)
VAR _pm = DIVIDE(_mas, _sal)
VAR _pc = DIVIDE(_m2, _cty)
VAR _need = _m2 / 0.3
VAR _arc = {circ:.1f} * MIN(_p, 1)
VAR _a = -PI() / 2 + 2 * PI() * _pm
VAR _mx = {c} + {r} * COS(_a)
VAR _my = {c} + {r} * SIN(_a)"""
    ticks = "".join(
        f"<line x1='{c + (r + sw * 0.75) * math.cos(-math.pi / 2 + 2 * math.pi * i / 60):.1f}' y1='{c + (r + sw * 0.75) * math.sin(-math.pi / 2 + 2 * math.pi * i / 60):.1f}' "
        f"x2='{c + (r + sw * (1.05 if i % 5 else 1.3)) * math.cos(-math.pi / 2 + 2 * math.pi * i / 60):.1f}' y2='{c + (r + sw * (1.05 if i % 5 else 1.3)) * math.sin(-math.pi / 2 + 2 * math.pi * i / 60):.1f}' "
        f"stroke='{C['muted']}' stroke-opacity='{0.5 if i % 5 == 0 else 0.2}' stroke-width='1.2'/>" for i in range(60))
    na = -math.pi / 2 + 2 * math.pi * 0.30
    n1 = (c + (r - sw * 0.9) * math.cos(na), c + (r - sw * 0.9) * math.sin(na))
    n2 = (c + (r + sw * 0.9) * math.cos(na), c + (r + sw * 0.9) * math.sin(na))
    nl = (c + (r + sw * 1.15) * math.cos(na) + 6, c + (r + sw * 1.15) * math.sin(na))
    defs = (f"<linearGradient id='rg' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='{C['magenta']}'/>"
            f"<stop offset='0.55' stop-color='{C['violet']}'/><stop offset='1' stop-color='{C['cyan']}'/></linearGradient>"
            + GL("gl", 6) + GL("hg", 3))
    X = 450  # sağ blok
    parts = [
        S(f"<circle cx='{c}' cy='{c + 20}' r='{r}' fill='none' stroke='#FFFFFF' stroke-opacity='0.07' stroke-width='{sw}'/>"
          f"<g transform='translate(0,20)'>{ticks}</g>"
          f"<circle cx='{c}' cy='{c + 20}' r='{r}' fill='none' stroke='url(#rg)' stroke-width='{sw}' stroke-linecap='round' "
          f"stroke-dasharray='{circ:.1f}' stroke-dashoffset='{circ:.1f}' transform='rotate(-90 {c} {c + 20})' filter='url(#gl)'>"
          f"<animate attributeName='stroke-dashoffset' from='{circ:.1f}' to='"),
        f'FORMAT({circ:.1f} - _arc, "0.0", "en-US")',
        S(f"' dur='1.6s' begin='0.2s' fill='freeze' calcMode='spline' keyTimes='0;1' keySplines='0.2 0.8 0.2 1'/></circle>"
          f"<line x1='{n1[0]:.1f}' y1='{n1[1] + 20:.1f}' x2='{n2[0]:.1f}' y2='{n2[1] + 20:.1f}' stroke='{C['teal']}' stroke-width='4' stroke-linecap='round' filter='url(#hg)'/>"
          f"<text x='{nl[0]:.1f}' y='{nl[1] + 25:.1f}' font-size='13' font-weight='700' fill='{C['teal']}' text-anchor='start'>norma 30%</text>"
          f"<circle cy='0' r='11' fill='{C['teal']}' filter='url(#gl)' cx='"),
        f'FORMAT(_mx, "0.0", "en-US")', S("' transform='translate(0,"), f'FORMAT(_my + 20, "0.0", "en-US")',
        S(f")'><animate attributeName='r' values='8;14;8' dur='1.8s' repeatCount='indefinite'/></circle>"),
        CU("_p * 100", c, c + 40, 88, anchor="middle", suffix='"%"', dur=1.6, weight=800),
        STXT(c, c + 74, "orta maaşın", 18, C["muted"], 500, "middle"),
        # sağ blok
        STXT(X, 50, "2 otaqlı mənzilin median kirayəsi (Bakı şəhəri)", 19, C["muted"], 500),
        CU("_m2", X, 124, 76, suffix='" AZN"', weight=800),
        FADE(TXT(X, 166, '"Bakıda orta aylıq maaş " & ' + NUM("_sal") + ' & " AZN · kirayədən sonra qalır " & ' + NUM("_sal - _m2") + ' & " AZN"', 17, C["muted"]), 0.9),
        FADE(STXT(X, 212, "KİRAYƏ YÜKÜ (kirayə ÷ maaş)", 13, C["muted"], 700, spacing=1.5), 1.0),
    ]
    rows = [("Bakı şəhəri", "_p", C["magenta"]), ("Masazır (Abşeron)", "_pm", C["teal"]), ("Ölkə ortası ilə", "_pc", C["violet"])]
    for i, (nm, v, col) in enumerate(rows):
        y = 234 + i * 46
        parts += [STXT(X, y + 15, nm, 16, C["text"], 600),
                  S(f"<rect x='{X + 170}' y='{y + 2}' width='300' height='16' rx='8' fill='#FFFFFF' fill-opacity='0.07'/>"),
                  BAR(X + 170, y + 2, f"300 * MIN({v}, 1)", 16, col, 1.0 + i * 0.2, 1.0, extra="filter='url(#hg)'"),
                  FADE(TXT(X + 520, y + 16, f'FORMAT({v}, "0%")', 18, col, 800, "end"), 1.5 + i * 0.2)]
    nx = X + 170 + 300 * 0.3
    parts += [S(f"<line x1='{nx}' y1='226' x2='{nx}' y2='{234 + 3 * 46 - 10}' stroke='{C['teal']}' stroke-width='2' stroke-dasharray='4 4'/>"),
              S(f"<rect x='{X}' y='388' width='520' height='54' rx='14' fill='{C['amber']}' fill-opacity='0.10' stroke='{C['amber']}' stroke-opacity='0.5'/>"),
              FADE(TXT(X + 18, 412, '"30% normasına sığmaq üçün lazım olan maaş: " & ' + NUM("_need") + ' & " AZN"', 16, C["amber"], 700), 1.8),
              FADE(TXT(X + 18, 433, '"Bakıda orta maaşdan " & FORMAT(DIVIDE(_need, _sal), "0.0") & " dəfə çox"', 14, C["text"], 400), 2.0)]
    add("VZ Hero", "Ana səhifə: əsas problem — kirayə yükü halqası və müqayisə", WRAP(w, h, defs, parts, vars_))


def kpi_head(title, accent, value_var, sub_expr, fmt="#,0", suffix='""', w=718):
    return [S(f"<rect x='24' y='0' width='120' height='3' rx='1.5' fill='{accent}' filter='url(#kg)'/>"),
            LABEL(24, 36, title),
            CU(value_var, 24, 94, 48, fmt=fmt, suffix=suffix, weight=800),
            FADE(TXT(24, 126, sub_expr, 15, accent, 600), 0.9)]


def m_home_kpis():
    w, h = 718, 160
    defs = GL("kg", 3)
    # 1. elan sayı + yeni/köhnə payı
    vars1 = """VAR _n = CALCULATE([Elan sayı], REMOVEFILTERS())
VAR _new = DIVIDE(CALCULATE([Elan sayı], REMOVEFILTERS(), Elanlar[Tikili növü] = "Yeni tikili"), _n)"""
    parts = kpi_head("TƏHLİL OLUNAN UNİKAL ELAN", C["cyan"], "_n", '"bina.az · təkrarlar çıxarılıb"')
    parts += [S(f"<rect x='390' y='62' width='300' height='12' rx='6' fill='#FFFFFF' fill-opacity='0.06'/>"),
              BAR(390, 62, "300 * _new - 3", 12, C["cyan"], 0.3),
              S(f"<rect y='62' width='0' height='12' rx='6' fill='{C['magenta']}' x='"), 'FORMAT(390 + 300 * _new, "0", "en-US")',
              S("'><animate attributeName='width' to='"), 'FORMAT(300 * (1 - _new), "0", "en-US")',
              S("' dur='0.8s' begin='0.6s' fill='freeze'/></rect>"),
              FADE(TXT(390, 100, '"Yeni tikili " & FORMAT(_new, "0%")', 13, C["cyan"], 600), 0.9),
              FADE(TXT(690, 100, '"Köhnə " & FORMAT(1 - _new, "0%")', 13, C["magenta"], 600, "end"), 1.1)]
    add("VZ KPI Elan", "Ana səhifə KPI: unikal elan sayı + tikili növü payı", WRAP(w, h, defs, parts, vars1))
    # 2. median + histogram
    vars2 = f"""VAR _m = CALCULATE([Median kirayə], REMOVEFILTERS())
VAR _p25 = CALCULATE([P25 kirayə], REMOVEFILTERS())
VAR _p75 = CALCULATE([P75 kirayə], REMOVEFILTERS())
VAR _b = ADDCOLUMNS(GENERATESERIES(0, 2900, 100), "@c",
    VAR _lo = [Value] RETURN CALCULATE(COUNTROWS(Elanlar), REMOVEFILTERS(), {PRICE} >= _lo, {PRICE} < IF(_lo = 2900, 1000000, _lo + 100)))
VAR _mx = MAXX(_b, [@c])
VAR _bars = CONCATENATEX(_b,
    VAR _hh = 96 * DIVIDE([@c], _mx) VAR _x = 390 + [Value] / 100 * 10.3 VAR _on = _m >= [Value] && _m < [Value] + 100
    RETURN "<rect x='" & FORMAT(_x, "0.0", "en-US") & "' y='124' width='8.3' height='0' rx='1.5' fill='" & IF(_on, "url(#h2)", "url(#h1)") & "'>"
        & "<animate attributeName='height' to='" & FORMAT(_hh, "0.0", "en-US") & "' dur='0.7s' begin='" & FORMAT(0.1 + [Value] / 100 * 0.025, "0.00", "en-US") & "s' fill='freeze'/>"
        & "<animate attributeName='y' to='" & FORMAT(124 - _hh, "0.0", "en-US") & "' dur='0.7s' begin='" & FORMAT(0.1 + [Value] / 100 * 0.025, "0.00", "en-US") & "s' fill='freeze'/></rect>",
    "", [Value], ASC)"""
    defs2 = defs + GRAD("h1", C["violet"], C["violet"], True, 0.15, 1) + GRAD("h2", C["magenta"], C["magenta"], True, 0.3, 1)
    parts = kpi_head("MEDİAN KİRAYƏ, AZN", C["violet"], "_m", '"orta 50%: " & ' + NUM("_p25") + ' & " – " & ' + NUM("_p75") + ' & " AZN"')
    parts += ["_bars", STXT(390, 146, "0", 11, C["dim"]), STXT(690, 146, "3 000+ AZN", 11, C["dim"], 400, "end")]
    add("VZ KPI Median", "Ana səhifə KPI: median kirayə + qiymət paylanması (histogram)", WRAP(w, h, defs2, parts, vars2))
    # 3. maaş Bakı vs ölkə
    vars3 = """VAR _s = [Bakı orta maaşı]
VAR _c = [Ölkə orta maaşı]
VAR _y = [Maaş ili]"""
    parts = kpi_head("BAKIDA ORTA AYLIQ MAAŞ, AZN", C["amber"], "_s", '"DSK, " & _y & " · nominal, vergidən əvvəl"')
    for i, (nm, v, col) in enumerate([("Bakı", "_s", C["amber"]), ("Ölkə", "_c", C["dim"])]):
        y = 46 + i * 40
        parts += [STXT(390, y + 13, nm, 14, C["muted"], 600),
                  S(f"<rect x='450' y='{y + 2}' width='170' height='14' rx='7' fill='#FFFFFF' fill-opacity='0.06'/>"),
                  BAR(450, y + 2, f"170 * DIVIDE({v}, _s)", 14, col, 0.3 + i * 0.2),
                  FADE(TXT(690, y + 15, NUM(v), 15, C["text"], 700, "end"), 0.9 + i * 0.2)]
    add("VZ KPI Maaş", "Ana səhifə KPI: Bakıda orta maaş vs ölkə", WRAP(w, h, defs, parts, vars3))


def m_tiles():
    w, h = 1752, 318
    tw = (w - 3 * 24) / 4
    vars_ = f"""VAR _d = FILTER(ADDCOLUMNS(VALUES(Rayon[Rayon]), "@m", [Median kirayə], "@n", [Elan sayı], "@q", [Median 1 m²]), [@n] >= 30)
VAR _top = TOPN(1, _d, [@m], DESC, [@q], DESC)
VAR _topN = MAXX(_top, Rayon[Rayon])
VAR _topM = MAXX(_top, [@m])
VAR _fit = CALCULATE(DIVIDE(COUNTROWS(FILTER(Elanlar, {PRICE} <= 700)), COUNTROWS(Elanlar)), Elanlar[Otaq] = "2", {CITY})
VAR _yr = CALCULATE(MAX('Maaş'[İl]), ALL('Maaş'))
VAR _sec = FILTER(ADDCOLUMNS(FILTER(ALL('Maaş'[Sahə]), 'Maaş'[Sahə] <> "İqtisadiyyat üzrə - cəmi"), "@s",
    CALCULATE(MAX('Maaş'[Orta maaş (AZN)]), 'Maaş'[İl] = _yr)), NOT ISBLANK([@s]))
VAR _need1 = CALCULATE([Median kirayə], Elanlar[Otaq] = "1", {CITY}) / 0.3
VAR _ok = COUNTROWS(FILTER(_sec, [@s] >= _need1))
VAR _ns = COUNTROWS(_sec)
VAR _raw = [Xam elan sayı]
VAR _an = [Analiz elan sayı]"""
    tiles = [("BAZAR XƏRİTƏSİ", "Harada nə qədərdir?", '"Ən baha: " & _topN', NUM("_topM") + ' & " AZN"', C["cyan"]),
             ("BÜDCƏM NƏYƏ ÇATIR?", "Məbləğinizə uyğun rayonlar", '"700 AZN ilə 2 otaqlı elanların"', 'FORMAT(_fit, "0%") & "-i"', C["amber"]),
             ("MAAŞ VƏ KİRAYƏ YÜKÜ", "Kimin maaşı kirayəyə çatır?", '"1 otaqlını 30% ilə ödəyən sahə"', '_ok & " / " & _ns', C["coral"]),
             ("METODOLOGİYA", "Rəqəmlərə niyə inanmaq olar?", NUM("_raw") + ' & " xam elandan"', NUM("_an") + ' & " unikal"', C["violet"])]
    parts = []
    for i, (t, q, a, b, col) in enumerate(tiles):
        x = round(i * (tw + 24))
        parts += [STXT(x + 104, 74, t, 14, col, 800, spacing=1.6), STXT(x + 104, 98, q, 15, C["muted"]),
                  FADE(TXT(x + 28, 170, a, 17, C["muted"]), 0.4 + i * 0.15),
                  FADE(TXT(x + 28, 228, b, 40, col, 800), 0.6 + i * 0.15),
                  S(f"<text x='{x + 28}' y='286' font-size='16' font-weight='700' fill='{col}'>Bax  →"
                    f"<animate attributeName='opacity' values='1;0.35;1' dur='2.4s' begin='{i * 0.4}s' repeatCount='indefinite'/></text>")]
    add("VZ Plitələr", "Ana səhifə: 4 plitə — hər səhifənin əsas rəqəmi", WRAP(w, h, "", parts, vars_))


# ======================================================================= BAZAR
def small_kpi(name, desc, title, accent, vars_, value, sub, fmt="#,0", suffix='""', extra=None, w=331, h=136):
    parts = [S(f"<rect x='22' y='0' width='100' height='3' rx='1.5' fill='{accent}' filter='url(#kg)'/>"),
             LABEL(22, 34, title), CU(value, 22, 86, 42, fmt=fmt, suffix=suffix, weight=800),
             FADE(TXT(22, 116, sub, 14, accent, 600), 0.9)]
    if extra:
        parts += extra
    add(name, desc, WRAP(w, h, GL("kg", 3), parts, vars_))


def m_market_kpis():
    small_kpi("VZ MK Elan", "Bazar KPI: elan sayı (filtrə görə)", "ELAN SAYI", C["cyan"],
              "VAR _n = [Elan sayı]\nVAR _all = CALCULATE([Elan sayı], REMOVEFILTERS())",
              "_n", 'FORMAT(DIVIDE(_n, _all), "0%") & " bütün elanlardan"')
    small_kpi("VZ MK Median", "Bazar KPI: median kirayə", "MEDİAN KİRAYƏ, AZN", C["violet"],
              "VAR _m = [Median kirayə]\nVAR _p25 = [P25 kirayə]\nVAR _p75 = [P75 kirayə]",
              "_m", '"orta 50%: " & ' + NUM("_p25") + ' & "–" & ' + NUM("_p75"))
    small_kpi("VZ MK M2", "Bazar KPI: 1 m² medianı", "MEDİAN 1 M², AZN / AY", C["magenta"],
              "VAR _v = [Median 1 m²]\nVAR _a = [Median sahə]", "_v", '"median sahə " & FORMAT(_a, "0") & " m²"', fmt="0.0")
    vars_t = """VAR _nw = CALCULATE([Median kirayə], Elanlar[Tikili növü] = "Yeni tikili")
VAR _od = CALCULATE([Median kirayə], Elanlar[Tikili növü] = "Köhnə tikili")"""
    small_kpi("VZ MK Tikili", "Bazar KPI: yeni vs köhnə tikili medianı", "YENİ / KÖHNƏ TİKİLİ", C["amber"], vars_t,
              "_nw", 'IF(ISBLANK(_od), "", "köhnə tikili " & ' + NUM("_od") + ' & " AZN (−" & FORMAT(1 - DIVIDE(_od, _nw), "0%") & ")")')
    import math
    circ = 2 * math.pi * 30
    vars_a = """VAR _p = [Vasitəçi payı]
VAR _ag = CALCULATE([Median kirayə], Elanlar[Elanı verən] = "Vasitəçi")
VAR _ow = CALCULATE([Median kirayə], Elanlar[Elanı verən] = "Mülkiyyətçi")"""
    ring = [S(f"<circle cx='284' cy='72' r='30' fill='none' stroke='#FFFFFF' stroke-opacity='0.08' stroke-width='9'/>"
              f"<circle cx='284' cy='72' r='30' fill='none' stroke='{C['teal']}' stroke-width='9' stroke-linecap='round' "
              f"stroke-dasharray='{circ:.1f}' stroke-dashoffset='{circ:.1f}' transform='rotate(-90 284 72)' filter='url(#kg)'>"
              f"<animate attributeName='stroke-dashoffset' to='"), f'FORMAT({circ:.1f} * (1 - _p), "0.0", "en-US")',
            S("' dur='1.2s' begin='0.2s' fill='freeze'/></circle>")]
    small_kpi("VZ MK Vasitəçi", "Bazar KPI: vasitəçi payı və qiymət fərqi", "VASİTƏÇİ PAYI", C["teal"], vars_a,
              "_p * 100", 'IF(ISBLANK(_ow), "", "vasitəçi +" & FORMAT(DIVIDE(_ag, _ow) - 1, "0%") & " baha")', suffix='"%"', extra=ring)


def m_range():
    w, h = 836, 412
    x0, x1, hi = 140, 770, 2400
    vars_ = f"""VAR _city = [Median kirayə]
VAR _d = FILTER(ADDCOLUMNS(VALUES(Rayon[Rayon]), "@n", [Elan sayı], "@m", [Median kirayə], "@p25", [P25 kirayə], "@p75", [P75 kirayə], "@q", [Median 1 m²]), [@n] >= 30)
VAR _k = COUNTROWS(_d)
VAR _rh = DIVIDE(340, MAX(_k, 1))
VAR _r = ADDCOLUMNS(_d, "@i", RANKX(_d, [@m] + [@q] / 1000, , DESC))
VAR _sx = 1
VAR _rows = CONCATENATEX(_r,
    VAR _y = 20 + ([@i] - 1) * _rh + _rh / 2
    VAR _a = {x0} + MIN([@p25], {hi}) / {hi} * {x1 - x0}
    VAR _b = {x0} + MIN([@p75], {hi}) / {hi} * {x1 - x0}
    VAR _c = {x0} + MIN([@m], {hi}) / {hi} * {x1 - x0}
    VAR _col = SWITCH(TRUE(), [@m] >= 1100, "{C['coral']}", [@m] >= 900, "{C['amber']}", [@m] >= 600, "{C['blue']}", "{C['teal']}")
    VAR _bg = FORMAT(0.1 + ([@i] - 1) * 0.06, "0.00", "en-US")
    RETURN "<text x='{x0 - 14}' y='" & FORMAT(_y + 5, "0.0", "en-US") & "' font-size='14' font-weight='600' fill='{C['text']}' text-anchor='end'>" & Rayon[Rayon] & "</text>"
        & "<rect x='" & FORMAT(_a, "0.0", "en-US") & "' y='" & FORMAT(_y - 6, "0.0", "en-US") & "' width='0' height='12' rx='6' fill='url(#rb)'><animate attributeName='width' to='" & FORMAT(MAX(_b - _a, 4), "0.0", "en-US") & "' dur='0.8s' begin='" & _bg & "s' fill='freeze'/></rect>"
        & "<g opacity='0'><animate attributeName='opacity' to='1' dur='0.3s' begin='" & FORMAT(0.7 + ([@i] - 1) * 0.06, "0.00", "en-US") & "s' fill='freeze'/>"
        & "<circle cx='" & FORMAT(_c, "0.0", "en-US") & "' cy='" & FORMAT(_y, "0.0", "en-US") & "' r='7' fill='" & _col & "' stroke='{C['bg0']}' stroke-width='2' filter='url(#dg)'/>"
        & "<text x='" & FORMAT(_b + 12, "0.0", "en-US") & "' y='" & FORMAT(_y + 5, "0.0", "en-US") & "' font-size='13' font-weight='700' fill='" & _col & "'>" & {NUM('[@m]')} & "</text></g>",
    "", [@i], ASC)
VAR _cx = {x0} + MIN(_city, {hi}) / {hi} * {x1 - x0}"""
    grid = "".join(f"<line x1='{x0 + v / hi * (x1 - x0):.1f}' y1='10' x2='{x0 + v / hi * (x1 - x0):.1f}' y2='370' stroke='#FFFFFF' stroke-opacity='0.06'/>"
                   f"<text x='{x0 + v / hi * (x1 - x0):.1f}' y='392' font-size='12' class='d' text-anchor='middle'>{v:,}</text>".replace(",", " ")
                   for v in range(0, hi + 1, 400))
    defs = GRAD("rb", C["violet"], C["magenta"], o1=0.5, o2=0.9) + GL("dg", 4)
    parts = [S(grid), "_rows",
             S(f"<line y1='6' y2='370' stroke='{C['cyan']}' stroke-dasharray='4 4' stroke-opacity='0.8' x1='"), 'FORMAT(_cx, "0.0", "en-US")',
             S("' x2='"), 'FORMAT(_cx, "0.0", "en-US")', S("'/>"),
             DTXT('FORMAT(_cx + 6, "0", "en-US")', 14, '"seçimin medianı " & ' + NUM("_city"), 12, C["cyan"], 600)]
    add("VZ Rayon aralığı", "Bazar: rayonlar üzrə P25–P75 aralığı və median (ən az 30 elan)", WRAP(w, h, defs, parts, vars_))


def m_drivers():
    w, h = 1720, 134
    vars_ = f"""VAR _r = ADDCOLUMNS(FILTER(VALUES(Elanlar[Otaq]), CALCULATE([Elan sayı]) >= 30), "@m", [Median kirayə], "@a", [Median sahə])
VAR _rmx = MAXX(_r, [@m])
VAR _ladder = CONCATENATEX(_r,
    VAR _i = SWITCH(Elanlar[Otaq], "1", 0, "2", 1, "3", 2, "4", 3, 4)
    VAR _x = 40 + _i * 96
    VAR _hh = 74 * DIVIDE([@m], _rmx)
    RETURN "<rect x='" & _x & "' y='110' width='56' height='0' rx='6' fill='url(#lg)'><animate attributeName='height' to='" & FORMAT(_hh, "0.0", "en-US") & "' dur='0.8s' begin='" & FORMAT(0.1 + _i * 0.12, "0.00", "en-US") & "s' fill='freeze'/><animate attributeName='y' to='" & FORMAT(110 - _hh, "0.0", "en-US") & "' dur='0.8s' begin='" & FORMAT(0.1 + _i * 0.12, "0.00", "en-US") & "s' fill='freeze'/></rect>"
        & "<g opacity='0'><animate attributeName='opacity' to='1' dur='0.3s' begin='" & FORMAT(0.8 + _i * 0.12, "0.00", "en-US") & "s' fill='freeze'/><text x='" & (_x + 28) & "' y='" & FORMAT(104 - _hh, "0.0", "en-US") & "' font-size='13' font-weight='700' fill='{C['text']}' text-anchor='middle'>" & {NUM('[@m]')} & "</text></g>"
        & "<text x='" & (_x + 28) & "' y='128' font-size='12' class='m' text-anchor='middle'>" & Elanlar[Otaq] & " otaq · " & FORMAT([@a], "0") & " m²</text>",
    "", Elanlar[Otaq], ASC)
VAR _nw = CALCULATE([Median kirayə], Elanlar[Tikili növü] = "Yeni tikili")
VAR _od = CALCULATE([Median kirayə], Elanlar[Tikili növü] = "Köhnə tikili")
VAR _nwm = CALCULATE([Median 1 m²], Elanlar[Tikili növü] = "Yeni tikili")
VAR _odm = CALCULATE([Median 1 m²], Elanlar[Tikili növü] = "Köhnə tikili")
VAR _nwa = CALCULATE([Median sahə], Elanlar[Tikili növü] = "Yeni tikili")
VAR _oda = CALCULATE([Median sahə], Elanlar[Tikili növü] = "Köhnə tikili")
VAR _ag = CALCULATE([Median kirayə], Elanlar[Elanı verən] = "Vasitəçi")
VAR _ow = CALCULATE([Median kirayə], Elanlar[Elanı verən] = "Mülkiyyətçi")
VAR _mx2 = MAX(MAX(_nw, _od), MAX(_ag, _ow))"""
    parts = [LABEL(40, 18, "1. OTAQ SAYI — ƏSAS AMİL"), "_ladder",
             LABEL(600, 18, "2. TİKİLİ NÖVÜ"), LABEL(1170, 18, "3. ELANI VERƏN")]
    grp = [(600, [("Yeni tikili", "_nw", C["violet"]), ("Köhnə tikili", "_od", C["amber"])],
            '"1 m²: " & FORMAT(_nwm, "0.0") & " vs " & FORMAT(_odm, "0.0") & " AZN · sahə " & FORMAT(_nwa, "0") & " vs " & FORMAT(_oda, "0") & " m² → fərq əsasən ölçüdədir"'),
           (1170, [("Vasitəçi", "_ag", C["coral"]), ("Mülkiyyətçi", "_ow", C["teal"])],
            'IF(ISBLANK(_ow), "", "Mülkiyyətçi elanı " & FORMAT(1 - DIVIDE(_ow, _ag), "0%") & " ucuzdur → birbaşa sahibdən axtarın")')]
    for gx, rows, note in grp:
        for i, (nm, v, col) in enumerate(rows):
            y = 36 + i * 34
            parts += [STXT(gx, y + 14, nm, 14, C["text"], 600),
                      S(f"<rect x='{gx + 110}' y='{y + 3}' width='250' height='14' rx='7' fill='#FFFFFF' fill-opacity='0.06'/>"),
                      BAR(gx + 110, y + 3, f"250 * DIVIDE({v}, _mx2)", 14, col, 0.3 + i * 0.2),
                      FADE(TXT(gx + 480, y + 16, NUM(v) + ' & " AZN"', 15, C["text"], 700, "end"), 0.9 + i * 0.2)]
        parts.append(FADE(TXT(gx, 122, note, 13, C["muted"]), 1.2))
    defs = GRAD("lg", C["magenta"], C["cyan"], True, 0.35, 1) + GL("kg", 3)
    add("VZ Amillər", "Bazar: qiyməti nə müəyyən edir — otaq, tikili növü, elanı verən", WRAP(w, h, defs, parts, vars_))


# ======================================================================= BÜDCƏM
def m_budget():
    import math
    w, h = 1276, 230
    r = 82
    circ = 2 * math.pi * r
    vars_ = """VAR _p = [Büdcəyə uyğun pay]
VAR _n = [Büdcəyə uyğun elan]
VAR _b = [Seçilmiş büdcə]
VAR _ppl = [Seçilmiş nəfər]
VAR _pm = [Adambaşına median]
VAR _gap = [Büdcə fərqi]
VAR _best = [Ən əlçatan rayon]
VAR _sal = [Bakı orta maaşı]"""
    defs = (f"<linearGradient id='bg1' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='{C['amber']}'/><stop offset='1' stop-color='{C['magenta']}'/></linearGradient>"
            + GL("gl", 5))
    parts = [S(f"<circle cx='110' cy='115' r='{r}' fill='none' stroke='#FFFFFF' stroke-opacity='0.07' stroke-width='22'/>"
               f"<circle cx='110' cy='115' r='{r}' fill='none' stroke='url(#bg1)' stroke-width='22' stroke-linecap='round' "
               f"stroke-dasharray='{circ:.1f}' stroke-dashoffset='{circ:.1f}' transform='rotate(-90 110 115)' filter='url(#gl)'>"
               f"<animate attributeName='stroke-dashoffset' to='"), f'FORMAT({circ:.1f} * (1 - MIN(_p, 1)), "0.0", "en-US")',
             S("' dur='1.4s' begin='0.2s' fill='freeze' calcMode='spline' keyTimes='0;1' keySplines='0.2 0.8 0.2 1'/></circle>"),
             CU("_p * 100", 110, 128, 44, anchor="middle", suffix='"%"', dur=1.4, weight=800),
             STXT(110, 152, "elanlar", 14, C["muted"], 500, "middle"),
             TXT(250, 62, '"Ayda " & ' + NUM("_b") + ' & " AZN" & IF(_ppl = 2, " · 2 nəfər (mənzil ≤ " & ' + NUM("_b * 2") + ' & " AZN)", "") & " ilə"', 22, C["muted"], 500),
             CU("_n", 250, 128, 60, suffix='" uyğun mənzil"', weight=800),
             FADE(TXT(250, 170, '"Adambaşına median kirayə " & ' + NUM("_pm") + ' & " AZN · büdcə fərqi " & IF(_gap >= 0, "+", "−") & ' + NUM("ABS(_gap)") + ' & " AZN"', 17, C["muted"]), 0.9),
             FADE(TXT(250, 202, '"Büdcə Bakıda orta maaşın " & FORMAT(DIVIDE(_b, _sal), "0%") & "-i" & IF(DIVIDE(_b, _sal) > 0.3, " — 30% normasından çox", " — normaya uyğun")', 15,
                      C["amber"], 600), 1.1),
             S(f"<rect x='980' y='40' width='276' height='150' rx='18' fill='{C['teal']}' fill-opacity='0.08' stroke='{C['teal']}' stroke-opacity='0.5'/>"),
             STXT(1004, 76, "ƏN ƏLÇATAN RAYON", 13, C["teal"], 800, spacing=1.6),
             FADE(TXT(1004, 128, "_best", 34, C["text"], 800), 0.8),
             STXT(1004, 166, "ən az 30 elan olan rayonlar", 13, C["muted"])]
    add("VZ Büdcə", "Büdcəm: uyğun elan payı halqası və nəticə", WRAP(w, h, defs, parts, vars_))


def m_savings():
    w, h = 612, 560
    vars_ = f"""VAR _room = SELECTEDVALUE(Elanlar[Otaq], "2")
VAR _b = [Seçilmiş büdcə]
VAR _base = CALCULATE([Median kirayə], REMOVEFILTERS(Elanlar), REMOVEFILTERS(Rayon), Elanlar[Otaq] = _room, {CITY})
VAR _dist = TOPN(4, FILTER(ADDCOLUMNS(CALCULATETABLE(VALUES(Rayon[Rayon]), {CITY}), "@m",
        CALCULATE([Median kirayə], REMOVEFILTERS(Elanlar[Tikili növü]), Elanlar[Otaq] = _room), "@n",
        CALCULATE([Elan sayı], REMOVEFILTERS(Elanlar[Tikili növü]), Elanlar[Otaq] = _room)), [@n] >= 30), [@m], ASC)
VAR _cheap = TREATAS(SELECTCOLUMNS(_dist, "r", Rayon[Rayon]), Rayon[Rayon])
VAR _s1 = CALCULATE([Median kirayə], REMOVEFILTERS(Elanlar), REMOVEFILTERS(Rayon), Elanlar[Otaq] = _room, _cheap)
VAR _s2 = CALCULATE([Median kirayə], REMOVEFILTERS(Elanlar), REMOVEFILTERS(Rayon), Elanlar[Otaq] = _room, _cheap, Elanlar[Tikili növü] = "Köhnə tikili")
VAR _s3 = CALCULATE([Median kirayə], REMOVEFILTERS(Elanlar), REMOVEFILTERS(Rayon), Elanlar[Otaq] = _room, _cheap, Elanlar[Tikili növü] = "Köhnə tikili", Elanlar[Elanı verən] = "Mülkiyyətçi")
VAR _s4 = _s3 / 2
VAR _names = CONCATENATEX(_dist, Rayon[Rayon], ", ", [@m], ASC)
VAR _mx = _base * 1.25
VAR _steps = {{
    (1, "Başlanğıc: " & _room & " otaqlı, Bakı", _base, _base, "{C['magenta']}"),
    (2, "Ucuz rayonlara baxın", _base, _s1, "{C['cyan']}"),
    (3, "+ köhnə tikili", _s1, _s2, "{C['violet']}"),
    (4, "+ mülkiyyətçi elanı (vasitəçisiz)", _s2, _s3, "{C['blue']}"),
    (5, "2 nəfər bölüşsün", _s3, _s4, "{C['teal']}")
}}
VAR _rows = CONCATENATEX(_steps,
    VAR _y = 30 + ([Value1] - 1) * 86
    VAR _from = [Value3]
    VAR _to = [Value4]
    VAR _x1 = 20 + 560 * DIVIDE(_to, _mx)
    VAR _x2 = 20 + 560 * DIVIDE(_from, _mx)
    VAR _bg = FORMAT(0.2 + ([Value1] - 1) * 0.35, "0.00", "en-US")
    RETURN "<text x='20' y='" & _y & "' font-size='15' font-weight='600' fill='{C['text']}'>" & [Value2] & "</text>"
        & IF([Value1] > 1, "<rect x='" & FORMAT(_x1, "0.0", "en-US") & "' y='" & (_y + 12) & "' width='" & FORMAT(_x2 - _x1, "0.0", "en-US") & "' height='26' rx='6' fill='#FFFFFF' fill-opacity='0.05' stroke='" & [Value5] & "' stroke-opacity='0.35' stroke-dasharray='3 3'/>", "")
        & "<rect x='20' y='" & (_y + 12) & "' width='0' height='26' rx='6' fill='" & [Value5] & "' fill-opacity='0.85' filter='url(#sg)'><animate attributeName='width' to='" & FORMAT(_x1 - 20, "0.0", "en-US") & "' dur='0.7s' begin='" & _bg & "s' fill='freeze'/></rect>"
        & "<g opacity='0'><animate attributeName='opacity' to='1' dur='0.3s' begin='" & FORMAT(0.6 + ([Value1] - 1) * 0.35, "0.00", "en-US") & "s' fill='freeze'/>"
        & "<text x='" & FORMAT(_x1 + 10, "0.0", "en-US") & "' y='" & (_y + 31) & "' font-size='16' font-weight='800' fill='{C['text']}'>" & {NUM('_to')} & " AZN"
        & IF([Value1] > 1, "<tspan font-size='13' font-weight='600' fill='" & [Value5] & "'>  −" & {NUM('_from - _to')} & "</tspan>", "") & "</text></g>",
    "", [Value1], ASC)
VAR _bx = 20 + 560 * DIVIDE(_b, _mx)"""
    parts = ["_rows",
             S(f"<line y1='12' y2='460' stroke='{C['amber']}' stroke-width='2' stroke-dasharray='5 4' x1='"), 'FORMAT(_bx, "0.0", "en-US")',
             S("' x2='"), 'FORMAT(_bx, "0.0", "en-US")', S("'/>"),
             DTXT('FORMAT(MIN(_bx, 470), "0", "en-US")', 478, '"sizin büdcə: " & ' + NUM("_b") + ' & " AZN"', 13, C["amber"], 700),
             FADE(TXT(20, 510, '"Ucuz rayonlar: " & _names', 13, C["muted"]), 2.0),
             FADE(TXT(20, 536, '"Nəticə: " & ' + NUM("_s4") + ' & " AZN adambaşına = Bakıda orta maaşın " & FORMAT(DIVIDE(_s4, [Bakı orta maaşı]), "0%") & "-i"', 15, C["teal"], 700), 2.2)]
    add("VZ Qənaət", "Büdcəm: qənaət yolları — median kirayəni addım-addım necə azaltmaq olar",
        WRAP(w, h, GL("sg", 3), parts, vars_))


# ======================================================================= MAAŞ
def m_salary():
    import math
    vars1 = """VAR _s = [Orta maaş]
VAR _sec = IF(ISFILTERED('Maaş'[Sahə]), SELECTEDVALUE('Maaş'[Sahə], "seçilmiş sahələr") & " (ölkə üzrə)", "Bakı şəhəri üzrə orta")"""
    parts = kpi_head("ORTA AYLIQ MAAŞ, AZN", C["violet"], "_s", "_sec", w=568)
    add("VZ SL Maaş", "Maaş: seçilmiş sahənin (və ya Bakının) orta maaşı", WRAP(568, 150, GL("kg", 3), parts, vars1))
    r = 46
    circ = 2 * math.pi * r
    vars2 = """VAR _y = [Kirayə yükü]
VAR _pm = [Adambaşına median]
VAR _col = SWITCH(TRUE(), ISBLANK(_y), "#5B6699", _y <= 0.3, "#2DF5C4", _y <= 0.5, "#FFC23F", "#FF5A7A")"""
    parts = [S(f"<rect x='24' y='0' width='120' height='3' rx='1.5' fill='{C['coral']}' filter='url(#kg)'/>"), LABEL(24, 36, "KİRAYƏ YÜKÜ"),
             CU("_y * 100", 24, 94, 48, suffix='"%"', weight=800),
             FADE(TXT(24, 126, '"median kirayə " & ' + NUM("_pm") + ' & " AZN ÷ maaş"', 15, C["coral"], 600), 0.9),
             S(f"<circle cx='480' cy='76' r='{r}' fill='none' stroke='#FFFFFF' stroke-opacity='0.08' stroke-width='12'/>"
               f"<circle cx='480' cy='76' r='{r}' fill='none' stroke-width='12' stroke-linecap='round' stroke-dasharray='{circ:.1f}' "
               f"stroke-dashoffset='{circ:.1f}' transform='rotate(-90 480 76)' filter='url(#kg)' stroke='"), "_col",
             S("'><animate attributeName='stroke-dashoffset' to='"), f'FORMAT({circ:.1f} * (1 - MIN(_y, 1)), "0.0", "en-US")',
             S("' dur='1.2s' begin='0.2s' fill='freeze'/></circle>"),
             S(f"<line x1='{480 + (r - 10) * math.cos(-math.pi / 2 + 2 * math.pi * 0.3):.1f}' y1='{76 + (r - 10) * math.sin(-math.pi / 2 + 2 * math.pi * 0.3):.1f}' "
               f"x2='{480 + (r + 10) * math.cos(-math.pi / 2 + 2 * math.pi * 0.3):.1f}' y2='{76 + (r + 10) * math.sin(-math.pi / 2 + 2 * math.pi * 0.3):.1f}' "
               f"stroke='{C['teal']}' stroke-width='3'/>")]
    add("VZ SL Yük", "Maaş: kirayə yükü halqası (30% norma işarəsi ilə)", WRAP(568, 150, GL("kg", 3), parts, vars2))
    vars3 = """VAR _pm = [Adambaşına median]
VAR _need = _pm / 0.3
VAR _s = [Orta maaş]"""
    parts = kpi_head("30% ÜÇÜN LAZIM OLAN MAAŞ", C["amber"], "_need", 'IF(_s >= _need, "maaş kifayət edir ✓", "maaşdan " & FORMAT(DIVIDE(_need, _s), "0.0") & " dəfə çox")', w=568)
    add("VZ SL Lazım", "Maaş: kirayə 30%-dən çox olmasın deyə lazım olan maaş", WRAP(568, 150, GL("kg", 3), parts, vars3))


def m_afford():
    w, h = 516, 400
    vars_ = f"""VAR _ppl = [Seçilmiş nəfər]
VAR _yr = CALCULATE(MAX('Maaş'[İl]), ALL('Maaş'))
VAR _sec = FILTER(ADDCOLUMNS(FILTER(ALL('Maaş'[Sahə]), 'Maaş'[Sahə] <> "İqtisadiyyat üzrə - cəmi"), "@s",
    CALCULATE(MAX('Maaş'[Orta maaş (AZN)]), REMOVEFILTERS('Maaş'), 'Maaş'[Sahə] = EARLIER('Maaş'[Sahə]), 'Maaş'[İl] = _yr)), NOT ISBLANK([@s]))
VAR _ns = COUNTROWS(_sec)
VAR _r = {{ ("1", 0), ("2", 1), ("3", 2), ("4", 3) }}
VAR _rows = CONCATENATEX(_r,
    VAR _room = [Value1]
    VAR _m = CALCULATE([Median kirayə], REMOVEFILTERS(Elanlar), Elanlar[Otaq] = _room, {CITY}) / _ppl
    VAR _need = _m / 0.3
    VAR _ok = COUNTROWS(FILTER(_sec, [@s] >= _need))
    VAR _y = 40 + [Value2] * 84
    VAR _dots = CONCATENATEX(GENERATESERIES(1, _ns, 1),
        "<circle cx='" & (14 + [Value] * 22) & "' cy='" & (_y + 44) & "' r='7' fill='" & IF([Value] <= _ok, "{C['teal']}", "#FFFFFF") & "' fill-opacity='" & IF([Value] <= _ok, "1", "0.10") & "' opacity='0'><set attributeName='opacity' to='1' begin='" & FORMAT(0.2 + [Value] * 0.03 + [Value2] * 0.25, "0.00", "en-US") & "s' fill='freeze'/></circle>", "", [Value], ASC)
    RETURN "<text x='20' y='" & _y & "' font-size='16' font-weight='700' fill='{C['text']}'>" & [Value1] & " otaq</text>"
        & "<text x='496' y='" & _y & "' font-size='15' font-weight='700' fill='{C['amber']}' text-anchor='end'>" & {NUM('_need')} & " AZN lazımdır</text>"
        & _dots
        & "<text x='496' y='" & (_y + 49) & "' font-size='14' font-weight='800' fill='" & IF(_ok > 0, "{C['teal']}", "{C['coral']}") & "' text-anchor='end'>" & _ok & " / " & _ns & "</text>",
    "", [Value2], ASC)"""
    parts = [STXT(20, 14, "Dairə = 1 sahə · yaşıl: orta maaşı kifayət edir", 13, C["muted"]), "_rows",
             FADE(TXT(20, 392, 'IF(_ppl = 2, "2 nəfər bölüşəndə hesablanıb", "Kirayəni 2 nəfər bölsə? Yuxarıda «2» seçin")', 13, C["dim"]), 1.5)]
    add("VZ Əlçatanlıq", "Maaş: hansı otaq sayını neçə sahənin orta maaşı 30% normasında ödəyir", WRAP(w, h, "", parts, vars_))


# ======================================================================= METOD
def m_funnel():
    w, h = 828, 520
    vars_ = """VAR _raw = [Xam elan sayı]
VAR _cl = [Təmiz elan sayı]
VAR _out = [Qeyri-adi qiymət sayı]
VAR _dup = [Təkrar elan sayı]
VAR _an = [Analiz elan sayı]"""
    steps = [("Saytdan toplanan", "_raw", "bina.az · 13 rayon × 2 tikili növü", C["cyan"]),
             ("Təmizləmədən sonra", "_cl", "R1–R7: səhv qiymət, sahə, mərtəbə", C["blue"]),
             ("Qeyri-adi qiymət və otaq kirayəsi çıxanda", "_cl - _out", '"−" & ' + NUM("_out") + ' & " (R8: 1 m² qiyməti 1–99% xaricində · R10: otaq kirayəsi)"', C["violet"]),
             ("Təkrar elanlar çıxanda", "_an", '"−" & ' + NUM("_cl - _out - _an") + ' & " (R9: eyni mənzil, fərqli elan · cəmi " & ' + NUM("_dup") + ' & ", bir qismi artıq çıxmışdı)"', C["magenta"])]
    parts = []
    for i, (nm, v, sub, col) in enumerate(steps):
        y = 30 + i * 120
        sub_expr = sub if sub.startswith('"−"') else f'"{sub}"'
        parts += [STXT(20, y, nm.replace("i", "İ").upper(), 13, C["muted"], 700, spacing=1.5),
                  S(f"<rect x='20' y='{y + 14}' width='600' height='42' rx='10' fill='#FFFFFF' fill-opacity='0.05'/>"),
                  BAR(20, y + 14, f"600 * DIVIDE({v}, _raw)", 42, col, 0.2 + i * 0.35, 0.8, rx=10, extra="filter='url(#fg2)' fill-opacity='0.85'"),
                  CU(v, 800, y + 46, 30, anchor="end", weight=800, begin=0.2 + i * 0.35, dur=0.7),
                  FADE(TXT(20, y + 82, sub_expr, 14, col, 600), 0.6 + i * 0.35)]
    add("VZ Huni", "Metod: məlumat hunisi — xamdan unikal elanlara", WRAP(w, h, GL("fg2", 3), parts, vars_))


def m_validation():
    w, h = 836, 216
    vars_ = """VAR _m = CALCULATE([Median kirayə], REMOVEFILTERS(), Rayon[Ərazi] = "Bakı şəhəri")
VAR _m2 = CALCULATE([Median 1 m²], REMOVEFILTERS(), Rayon[Ərazi] = "Bakı şəhəri")"""
    rows = [("Mərkəzi Bank · median kirayə (14.04.2026)", "1002", "_m", "#,0", " AZN"),
            ("JAM-News · 1 m² / ay (30.08.2026)", "11", "_m2", "0.0", " AZN")]
    parts = []
    for i, (nm, ext, ours, fmt, unit) in enumerate(rows):
        y = 22 + i * 96
        parts += [STXT(20, y, nm, 15, C["muted"], 600),
                  STXT(20, y + 42, "onlar", 13, C["dim"]), STXT(80, y + 44, f"{int(ext):,}".replace(",", " ") + unit, 26, C["text"], 800),
                  STXT(340, y + 42, "biz", 13, C["dim"]), CU(ours, 380, y + 44, 26, C["cyan"], fmt=fmt, suffix=f'"{unit}"', weight=800),
                  FADE(TXT(816, y + 42, f'"fərq " & FORMAT(ABS(DIVIDE({ours}, {ext}) - 1), "0%") & " ✓"', 18, C["teal"], 800, "end"), 1.0 + i * 0.3)]
    add("VZ Yoxlama", "Metod: xarici yoxlama — Mərkəzi Bank və JAM-News ilə müqayisə", WRAP(w, h, "", parts, vars_))


# ======================================================================= TOOLTIP, ELANLAR
def m_tooltip():
    w, h = 480, 320
    vars_ = """VAR _r = [Seçilmiş rayon]
VAR _m = [Median kirayə]
VAR _n = [Elan sayı]
VAR _p25 = [P25 kirayə]
VAR _p75 = [P75 kirayə]
VAR _m2 = [Median 1 m²]
VAR _ag = [Vasitəçi payı]
VAR _fit = [Büdcəyə uyğun pay]
VAR _sal = [Bakı orta maaşı]"""
    parts = [S(f"<rect x='1' y='1' width='478' height='318' rx='20' fill='{C['panel']}' stroke='{C['cyan']}' stroke-opacity='0.6'/>"
               f"<rect x='24' y='0' width='90' height='3' fill='{C['magenta']}'/>"),
             TXT(24, 46, "_r", 26, C["cyan"], 800),
             CU("_m", 24, 108, 44, suffix='" AZN"', weight=800, dur=0.6),
             STXT(24, 130, "median kirayə", 13, C["muted"]),
             TXT(456, 108, 'FORMAT(DIVIDE(_m, _sal), "0%")', 32, C["magenta"], 800, "end"),
             STXT(456, 130, "Bakı maaşının", 13, C["muted"], 400, "end")]
    cells = [("ELAN", NUM("_n")), ("ORTA 50%", NUM("_p25") + ' & "–" & ' + NUM("_p75")), ("1 M²", 'FORMAT(_m2, "0.0") & " AZN"'),
             ("VASİTƏÇİ", 'FORMAT(_ag, "0%")'), ("BÜDCƏYƏ UYĞUN", 'FORMAT(_fit, "0%")')]
    for i, (lab, ex) in enumerate(cells):
        x = 24 + (i % 3) * 150
        y = 174 + (i // 3) * 70
        parts += [STXT(x, y, lab, 11, C["muted"], 700, spacing=1.4), FADE(TXT(x, y + 28, ex, 20, C["amber"] if i == 4 else C["text"], 700), 0.3 + i * 0.08)]
    add("VZ Tooltip", "Tooltip səhifəsi: rayonun mini kartı", WRAP(w, h, "", parts, vars_))


def m_list_head():
    w, h = 1752, 140
    vars_ = """VAR _r = [Seçilmiş rayon]
VAR _n = [Elan sayı]
VAR _m = [Median kirayə]
VAR _p25 = [P25 kirayə]
VAR _p75 = [P75 kirayə]
VAR _m2 = [Median 1 m²]
VAR _sal = [Bakı orta maaşı]"""
    parts = [S(f"<rect x='24' y='0' width='120' height='3' fill='{C['cyan']}'/>"), LABEL(24, 34, "RAYON"),
             TXT(24, 92, "_r", 44, C["cyan"], 800),
             FADE(TXT(24, 124, '"median kirayə Bakı maaşının " & FORMAT(DIVIDE(_m, _sal), "0%") & "-i"', 15, C["magenta"], 600), 0.8)]
    for i, (lab, v, fmt, suf) in enumerate([("ELAN SAYI", "_n", "#,0", '""'), ("MEDİAN KİRAYƏ", "_m", "#,0", '" AZN"'),
                                            ("MEDİAN 1 M²", "_m2", "0.0", '" AZN"')]):
        x = 480 + i * 300
        parts += [LABEL(x, 34, lab), CU(v, x, 92, 44, fmt=fmt, suffix=suf, weight=800, begin=i * 0.15)]
    parts += [LABEL(1380, 34, "ORTA 50% (P25–P75)"),
              FADE(TXT(1380, 92, NUM("_p25") + ' & " – " & ' + NUM("_p75") + ' & " AZN"', 34, C["text"], 800), 0.5)]
    add("VZ Elanlar başlıq", "Elanlar (drill-through): rayonun başlığı və əsas rəqəmləri", WRAP(w, h, "", parts, vars_))


def build():
    for f in [m_ticker, m_hero, m_home_kpis, m_tiles, m_market_kpis, m_range, m_drivers, m_budget, m_savings,
              m_salary, m_afford, m_funnel, m_validation, m_tooltip, m_list_head]:
        f()
    lines = ["/// Animasiyalı SVG vizual qatı (dax_svg.py ilə yaradılır, əl ilə dəyişməyin)",
             "table Vizual", f"\tlineageTag: 5b0c6a52-7c3e-4a59-9a3d-0d7d2b1c9e01", ""]
    for name, (desc, dax) in M.items():
        lines.append(f"\t/// {desc}")
        lines.append(f"\tmeasure '{name}' =")
        for ln in dax.strip("\n").split("\n"):
            lines.append("\t\t\t" + ln)
        lines.append("\t\tdataCategory: ImageUrl")
        lines.append("\t\tdisplayFolder: SVG")
        lines.append(f"\t\tlineageTag: {uuid.uuid5(uuid.NAMESPACE_URL, 'vz/' + name)}")
        lines.append("")
    lines += ["\tcolumn _", "\t\tisHidden", "\t\tlineageTag: 5b0c6a52-7c3e-4a59-9a3d-0d7d2b1c9e02", "\t\tisNameInferred",
              "\t\tsourceColumn: [_]", "", "\tpartition Vizual = calculated", "\t\tmode: import", '\t\tsource = ROW("_", BLANK())', ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(M)} ölçü -> {OUT}")


if __name__ == "__main__":
    build()
