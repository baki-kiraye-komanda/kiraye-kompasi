"""
components.py — "Neon kompas" dizaynının animasiyalı SVG komponentləri (maket üçün).

Hər funksiya bir SVG sətri qaytarır. Power BI-da eyni SVG DAX ölçüsü ilə qurulacaq
və standart "Image" vizualında göstəriləcək (sourceType = imageData) — əlavə vizual lazım deyil.
Animasiya: SMIL (<animate>, <set>, <animateTransform>) — Power BI-ın Image vizualında işləyir.
"""
import math

FONT = "'Segoe UI', Inter, sans-serif"
N = {  # neon palitra
    "bg0": "#04061A", "bg1": "#0A0F33", "bg2": "#131A4D", "panel": "#0D1440",
    "text": "#F2F5FF", "muted": "#9AA6D6", "dim": "#5B6699",
    "cyan": "#22E5FF", "teal": "#2DF5C4", "magenta": "#FF3FD1", "violet": "#8B5CFF",
    "amber": "#FFC23F", "coral": "#FF5A7A", "blue": "#3D8BFF",
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt(v, dec=0):
    s = f"{v:,.{dec}f}".replace(",", " ")
    return s


def svg(w, h, body, defs=""):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>"
            f"<defs>{defs}</defs>{body}</svg>")


def glow_filter(fid="gl", std=6):
    return (f"<filter id='{fid}' x='-50%' y='-50%' width='200%' height='200%'>"
            f"<feGaussianBlur stdDeviation='{std}' result='b'/>"
            f"<feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge></filter>")


def count_up(x, y, value, dec=0, prefix="", suffix="", size=40, color=None, anchor="start", frames=14, dur=0.9,
             weight=700):
    """Rəqəm 0-dan dəyərə qədər "qaçır" (kadr-kadr; DAX-da GENERATESERIES + CONCATENATEX ilə eyni)."""
    out = ""
    step = dur / frames
    for i in range(1, frames + 1):
        v = value * (1 - (1 - i / frames) ** 3)  # ease-out
        last = i == frames
        out += (f"<text x='{x}' y='{y}' font-family=\"{FONT}\" font-size='{size}' font-weight='{weight}' "
                f"fill='{color or N['text']}' text-anchor='{anchor}' opacity='0'>{prefix}{fmt(v, dec)}{suffix}"
                f"<set attributeName='opacity' to='1' begin='{(i - 1) * step:.2f}s' "
                + ("fill='freeze'" if last else f"dur='{step:.2f}s'") + "/></text>")
    return out


def label(x, y, s, color=None, size=13, weight=600, spacing=1.6, anchor="start"):
    return (f"<text x='{x}' y='{y}' font-family=\"{FONT}\" font-size='{size}' font-weight='{weight}' "
            f"letter-spacing='{spacing}' fill='{color or N['muted']}' text-anchor='{anchor}'>{esc(s)}</text>")


def text(x, y, s, size=16, color=None, weight=400, anchor="start", opacity=1):
    return (f"<text x='{x}' y='{y}' font-family=\"{FONT}\" font-size='{size}' font-weight='{weight}' "
            f"fill='{color or N['text']}' text-anchor='{anchor}' opacity='{opacity}'>{esc(s)}</text>")


def fade_in(body, begin=0.6, dur=0.5):
    return (f"<g opacity='0'><animate attributeName='opacity' from='0' to='1' begin='{begin}s' dur='{dur}s' "
            f"fill='freeze'/>{body}</g>")


# ---------------------------------------------------------------- ticker
def ticker(w, h, items, title="CANLI BAZAR"):
    """Bəgüşən sətir: items = [(açar, dəyər, rəng, əlavə)]."""
    body_parts = []
    plain = 0
    for k, v, col, extra in items:
        body_parts.append(f"<tspan fill='{N['muted']}' font-weight='600' letter-spacing='1.2' font-size='13'>{esc(k)}  </tspan>"
                          f"<tspan fill='{N['text']}' font-weight='700'>{esc(v)}</tspan>"
                          f"<tspan fill='{col}' font-weight='600'>  {esc(extra)}</tspan>"
                          f"<tspan fill='{N['violet']}'>          ✦          </tspan>")
        plain += len(k) + len(v) + len(extra) + 26
    L = round(plain * 8.1)
    dur = L / 70
    body = "".join(body_parts)
    x0 = 230
    defs = (f"<linearGradient id='fg' x1='0' x2='1'><stop offset='0' stop-color='black'/><stop offset='0.04' stop-color='white'/>"
            f"<stop offset='0.96' stop-color='white'/><stop offset='1' stop-color='black'/></linearGradient>"
            f"<mask id='tm'><rect x='{x0}' y='0' width='{w - x0}' height='{h}' fill='url(#fg)'/></mask>"
            f"<linearGradient id='tb' x1='0' x2='1'><stop offset='0' stop-color='{N['magenta']}' stop-opacity='0.22'/>"
            f"<stop offset='1' stop-color='{N['cyan']}' stop-opacity='0.10'/></linearGradient>" + glow_filter("tgl", 3))
    s = (f"<rect x='1' y='1' width='{w - 2}' height='{h - 2}' rx='{h / 2}' fill='{N['panel']}' fill-opacity='0.75' "
         f"stroke='url(#tb)' stroke-width='1.5'/>"
         f"<rect x='8' y='8' width='{x0 - 24}' height='{h - 16}' rx='{(h - 16) / 2}' fill='{N['magenta']}' fill-opacity='0.14' "
         f"stroke='{N['magenta']}' stroke-opacity='0.55'/>"
         f"<circle cx='28' cy='{h / 2}' r='5' fill='{N['magenta']}' filter='url(#tgl)'>"
         f"<animate attributeName='opacity' values='1;0.2;1' dur='1.4s' repeatCount='indefinite'/></circle>"
         + label(42, h / 2 + 5, title, N['magenta'], 13, 700, 1.8) +
         f"<g mask='url(#tm)'><g><animateTransform attributeName='transform' type='translate' from='{x0} 0' "
         f"to='{x0 - L} 0' dur='{dur:.1f}s' repeatCount='indefinite'/>"
         f"<text x='0' y='{h / 2 + 6}' font-family=\"{FONT}\" font-size='16' xml:space='preserve' textLength='{L}' "
         f"lengthAdjust='spacing'>{body}</text>"
         f"<text x='{L}' y='{h / 2 + 6}' font-family=\"{FONT}\" font-size='16' xml:space='preserve' textLength='{L}' "
         f"lengthAdjust='spacing'>{body}</text></g></g>")
    return svg(w, h, s, defs)


# ---------------------------------------------------------------- hero ring
def ring_gauge(size, pct, norm=0.30, alt=None):
    """Neon halqa: faiz animasiya ilə dolur; 30% norma işarəsi; alt = (faiz, ad) müqayisə nöqtəsi."""
    c = size / 2
    r = size * 0.40
    sw = size * 0.075
    circ = 2 * math.pi * r
    arc = circ * pct

    def pt(p, rr):
        a = -math.pi / 2 + 2 * math.pi * p
        return c + rr * math.cos(a), c + rr * math.sin(a)

    nx1, ny1 = pt(norm, r - sw * 0.9)
    nx2, ny2 = pt(norm, r + sw * 0.9)
    lx, ly = pt(norm, r - sw * 1.5)
    defs = (f"<linearGradient id='rg' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='{N['magenta']}'/>"
            f"<stop offset='0.55' stop-color='{N['violet']}'/><stop offset='1' stop-color='{N['cyan']}'/></linearGradient>"
            + glow_filter("rgl", size * 0.02))
    s = (f"<circle cx='{c}' cy='{c}' r='{r}' fill='none' stroke='#FFFFFF' stroke-opacity='0.07' stroke-width='{sw}'/>"
         # ölçü cizgiləri
         + "".join(f"<line x1='{pt(i / 60, r + sw * 0.75)[0]:.1f}' y1='{pt(i / 60, r + sw * 0.75)[1]:.1f}' "
                   f"x2='{pt(i / 60, r + sw * (1.05 if i % 5 else 1.25))[0]:.1f}' y2='{pt(i / 60, r + sw * (1.05 if i % 5 else 1.25))[1]:.1f}' "
                   f"stroke='{N['muted']}' stroke-opacity='{0.5 if i % 5 == 0 else 0.22}' stroke-width='1.2'/>" for i in range(60))
         + f"<circle cx='{c}' cy='{c}' r='{r}' fill='none' stroke='url(#rg)' stroke-width='{sw}' stroke-linecap='round' "
           f"stroke-dasharray='{circ:.1f}' stroke-dashoffset='{circ:.1f}' transform='rotate(-90 {c} {c})' filter='url(#rgl)'>"
           f"<animate attributeName='stroke-dashoffset' from='{circ:.1f}' to='{circ - arc:.1f}' dur='1.6s' begin='0.2s' "
           f"fill='freeze' calcMode='spline' keySplines='0.2 0.8 0.2 1' keyTimes='0;1'/></circle>"
         # 30% norma
         + f"<line x1='{nx1:.1f}' y1='{ny1:.1f}' x2='{nx2:.1f}' y2='{ny2:.1f}' stroke='{N['teal']}' stroke-width='4' stroke-linecap='round' filter='url(#rgl)'/>"
         + text(lx, ly + 5, "norma 30%", 14, N['teal'], 700, "end")
         + count_up(c, c + size * 0.07, pct * 100, 0, suffix="%", size=size * 0.22, color=N['text'], anchor="middle", dur=1.6)
         + text(c, c + size * 0.16, "maaşın", 18, N['muted'], 500, "middle"))
    if alt:
        ap, an = alt
        ax, ay = pt(ap, r)
        s += (f"<circle cx='{ax:.1f}' cy='{ay:.1f}' r='{sw * 0.42:.1f}' fill='{N['cyan']}' filter='url(#rgl)'>"
              f"<animate attributeName='r' values='{sw * 0.32:.1f};{sw * 0.55:.1f};{sw * 0.32:.1f}' dur='1.8s' repeatCount='indefinite'/></circle>")
    return svg(size, size, s, defs)


# ---------------------------------------------------------------- KPI kartı
def kpi(w, h, title, value, dec=0, prefix="", suffix="", sub="", accent=None, mini=""):
    accent = accent or N['cyan']
    defs = (f"<linearGradient id='kb' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='{accent}' stop-opacity='0.9'/>"
            f"<stop offset='1' stop-color='{accent}' stop-opacity='0'/></linearGradient>" + glow_filter("kgl", 4))
    s = (f"<rect x='24' y='0' width='140' height='3' rx='1.5' fill='url(#kb)' filter='url(#kgl)'/>"
         + label(24, 36, title.upper())
         + count_up(24, 92, value, dec, prefix, suffix, 46, N['text'])
         + fade_in(text(24, 124, sub, 15, accent, 600), 0.9)
         + mini)
    return svg(w, h, s, defs)


def mini_hist(x, y, w, h, bins, marker_idx=None, color=None, color2=None):
    """Mini histogram: sütunlar aşağıdan böyüyür (animasiya)."""
    color = color or N['cyan']
    color2 = color2 or N['magenta']
    mx = max(bins)
    bw = w / len(bins)
    out = (f"<defs><linearGradient id='hg' x1='0' y1='1' x2='0' y2='0'><stop offset='0' stop-color='{color}' stop-opacity='0.15'/>"
           f"<stop offset='1' stop-color='{color}'/></linearGradient>"
           f"<linearGradient id='hg2' x1='0' y1='1' x2='0' y2='0'><stop offset='0' stop-color='{color2}' stop-opacity='0.2'/>"
           f"<stop offset='1' stop-color='{color2}'/></linearGradient></defs>")
    for i, b in enumerate(bins):
        bh = h * b / mx
        fill = "url(#hg2)" if marker_idx is not None and i == marker_idx else "url(#hg)"
        out += (f"<rect x='{x + i * bw + 1:.1f}' y='{y + h:.1f}' width='{bw - 2:.1f}' height='0' rx='1.5' fill='{fill}'>"
                f"<animate attributeName='height' to='{bh:.1f}' dur='0.7s' begin='{0.1 + i * 0.025:.2f}s' fill='freeze'/>"
                f"<animate attributeName='y' to='{y + h - bh:.1f}' dur='0.7s' begin='{0.1 + i * 0.025:.2f}s' fill='freeze'/></rect>")
    return out


def mini_split(x, y, w, parts):
    """Bir sətirlik bölünmüş zolaq: parts = [(ad, dəyər, rəng)]."""
    tot = sum(p[1] for p in parts)
    out, cx = "", x
    for i, (name, v, col) in enumerate(parts):
        pw = w * v / tot
        out += (f"<rect x='{cx:.1f}' y='{y}' width='0' height='10' rx='5' fill='{col}'>"
                f"<animate attributeName='width' to='{max(pw - 4, 2):.1f}' dur='0.8s' begin='{0.2 + i * 0.2:.1f}s' fill='freeze'/></rect>")
        out += fade_in(text(cx, y + 32, f"{name} {v / tot:.0%}", 13, col, 600), 0.8 + i * 0.2)
        cx += pw
    return out


def mini_compare(x, y, w, rows):
    """Üfüqi müqayisə zolaqları: rows = [(ad, dəyər, rəng)]."""
    mx = max(r[1] for r in rows)
    out = ""
    for i, (name, v, col) in enumerate(rows):
        yy = y + i * 34
        out += text(x, yy + 12, name, 13, N['muted'], 500)
        out += (f"<rect x='{x + 92}' y='{yy + 2}' width='{w - 160}' height='12' rx='6' fill='#FFFFFF' fill-opacity='0.06'/>"
                f"<rect x='{x + 92}' y='{yy + 2}' width='0' height='12' rx='6' fill='{col}'>"
                f"<animate attributeName='width' to='{(w - 160) * v / mx:.1f}' dur='0.9s' begin='{0.3 + i * 0.2:.1f}s' fill='freeze'/></rect>")
        out += fade_in(text(x + w, yy + 13, fmt(v), 14, N['text'], 700, "end"), 0.9 + i * 0.2)
    return out


def mini_ring(cx, cy, r, pct, color, label_text):
    circ = 2 * math.pi * r
    return (f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='#FFFFFF' stroke-opacity='0.08' stroke-width='9'/>"
            f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='{color}' stroke-width='9' stroke-linecap='round' "
            f"stroke-dasharray='{circ:.1f}' stroke-dashoffset='{circ:.1f}' transform='rotate(-90 {cx} {cy})' filter='url(#kgl)'>"
            f"<animate attributeName='stroke-dashoffset' to='{circ * (1 - pct):.1f}' dur='1.2s' begin='0.2s' fill='freeze'/></circle>"
            + text(cx, cy + 6, label_text, 16, N['text'], 700, "middle"))


# ---------------------------------------------------------------- rayon aralığı (P25–P75 + median)
def range_chart(w, h, rows, city_median):
    """rows = [(rayon, p25, median, p75, n)]; median nöqtəsi parlayır, aralıq zolaq kimi."""
    lo, hi = 0, 2200
    x0, x1 = 150, w - 70
    sx = lambda v: x0 + (min(v, hi) - lo) / (hi - lo) * (x1 - x0)
    rh = (h - 60) / len(rows)
    defs = (f"<linearGradient id='rgb' x1='0' x2='1'><stop offset='0' stop-color='{N['violet']}' stop-opacity='0.5'/>"
            f"<stop offset='1' stop-color='{N['magenta']}' stop-opacity='0.85'/></linearGradient>" + glow_filter("dgl", 4))
    s = ""
    for v in range(0, 2201, 500):
        s += (f"<line x1='{sx(v):.1f}' y1='10' x2='{sx(v):.1f}' y2='{h - 40}' stroke='#FFFFFF' stroke-opacity='0.06'/>"
              + text(sx(v), h - 18, f"{v:,}".replace(",", " "), 12, N['dim'], 500, "middle"))
    cxm = sx(city_median)
    s += (f"<line x1='{cxm:.1f}' y1='6' x2='{cxm:.1f}' y2='{h - 40}' stroke='{N['cyan']}' stroke-dasharray='4 4' stroke-opacity='0.7'/>"
          + text(cxm + 6, 18, f"şəhər medianı {city_median:,.0f}".replace(",", " "), 12, N['cyan'], 600))
    for i, (name, p25, med, p75, n) in enumerate(rows):
        y = 24 + i * rh + rh / 2
        col = N['coral'] if med >= 1100 else N['amber'] if med >= 900 else N['blue'] if med >= 600 else N['teal']
        s += text(x0 - 14, y + 5, name, 14, N['text'], 600, "end")
        s += (f"<rect x='{sx(p25):.1f}' y='{y - 6:.1f}' width='0' height='12' rx='6' fill='url(#rgb)'>"
              f"<animate attributeName='width' to='{sx(p75) - sx(p25):.1f}' dur='0.8s' begin='{0.1 + i * 0.06:.2f}s' fill='freeze'/></rect>")
        s += fade_in(f"<circle cx='{sx(med):.1f}' cy='{y:.1f}' r='7' fill='{col}' stroke='{N['bg0']}' stroke-width='2' filter='url(#dgl)'/>"
                     + text(sx(p75) + 12, y + 5, f"{med:,.0f}".replace(",", " "), 13, col, 700), 0.7 + i * 0.06, 0.3)
    return svg(w, h, s, defs)


# ---------------------------------------------------------------- xəritə (maket: Power BI-da standart scatter)
def bubble_map(w, h, pts):
    """pts = [(ad, lat, lon, n, median)]; parlayan, nəbz vuran dairələr."""
    lats = [p[1] for p in pts]
    lons = [p[2] for p in pts]
    la0, la1 = min(lats) - 0.02, max(lats) + 0.03
    lo0, lo1 = min(lons) - 0.04, max(lons) + 0.05
    X = lambda lon: 40 + (lon - lo0) / (lo1 - lo0) * (w - 80)
    Y = lambda lat: 30 + (la1 - lat) / (la1 - la0) * (h - 60)
    mx = max(p[3] for p in pts)
    defs = glow_filter("mgl", 8) + "".join(
        f"<radialGradient id='b{i}'><stop offset='0' stop-color='{c}' stop-opacity='0.95'/><stop offset='0.7' stop-color='{c}' stop-opacity='0.35'/>"
        f"<stop offset='1' stop-color='{c}' stop-opacity='0'/></radialGradient>"
        for i, c in enumerate([N['teal'], N['blue'], N['amber'], N['coral']]))
    s = ""
    # Xəzər sahil xətti (dekorativ)
    s += (f"<path d='M{w * 0.05} {h * 0.92} C {w * 0.3} {h * 0.98}, {w * 0.55} {h * 0.75}, {w * 0.95} {h * 0.88}' fill='none' "
          f"stroke='{N['cyan']}' stroke-opacity='0.18' stroke-width='2' stroke-dasharray='2 6'/>")
    for i, (name, lat, lon, n, med) in enumerate(sorted(pts, key=lambda p: -p[3])):
        x, y = X(lon), Y(lat)
        r = 8 + 46 * math.sqrt(n / mx)
        gi = 3 if med >= 1100 else 2 if med >= 900 else 1 if med >= 600 else 0
        col = [N['teal'], N['blue'], N['amber'], N['coral']][gi]
        s += (f"<circle cx='{x:.1f}' cy='{y:.1f}' r='0' fill='url(#b{gi})'>"
              f"<animate attributeName='r' to='{r:.1f}' dur='0.8s' begin='{0.1 + i * 0.07:.2f}s' fill='freeze'/></circle>"
              f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r:.1f}' fill='none' stroke='{col}' stroke-opacity='0.6'>"
              f"<animate attributeName='r' values='{r:.1f};{r * 1.5:.1f}' dur='2.4s' begin='{i * 0.3:.1f}s' repeatCount='indefinite'/>"
              f"<animate attributeName='stroke-opacity' values='0.6;0' dur='2.4s' begin='{i * 0.3:.1f}s' repeatCount='indefinite'/></circle>"
              f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3' fill='#FFFFFF' filter='url(#mgl)'/>")
        s += fade_in(text(x, y - r - 8, name, 14, N['text'], 700, "middle")
                     + text(x, y + 5 + r + 14, f"{med:,.0f} AZN".replace(",", " "), 12, col, 700, "middle"), 0.8 + i * 0.05)
    return svg(w, h, s, defs)


def donut(size, parts, center_top, center_bottom):
    """parts = [(ad, dəyər, rəng)] — animasiyalı donut."""
    c = size / 2
    r = size * 0.36
    sw = size * 0.11
    circ = 2 * math.pi * r
    tot = sum(p[1] for p in parts)
    s, acc = "", 0
    for i, (name, v, col) in enumerate(parts):
        seg = circ * v / tot
        s += (f"<circle cx='{c}' cy='{c}' r='{r}' fill='none' stroke='{col}' stroke-width='{sw}' "
              f"stroke-dasharray='0 {circ:.1f}' stroke-dashoffset='{-acc:.1f}' transform='rotate(-90 {c} {c})' filter='url(#dg)'>"
              f"<animate attributeName='stroke-dasharray' to='{max(seg - 4, 1):.1f} {circ:.1f}' dur='0.9s' begin='{0.2 + i * 0.4:.1f}s' fill='freeze'/></circle>")
        acc += seg
    s += count_up(c, c + 4, center_top, 0, suffix="%", size=size * 0.17, anchor="middle")
    s += text(c, c + size * 0.12, center_bottom, 13, N['muted'], 500, "middle")
    return svg(size, size, s, glow_filter("dg", 3))
