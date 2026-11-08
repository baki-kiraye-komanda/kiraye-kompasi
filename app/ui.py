"""
ui.py — saytın vizual hissəsi: «Xəzər səhəri» (açıq, isti) dizayn sistemi və animasiyalı HTML/SVG blokları.

Dizayn fikri: mövzu ev və maaşdır — insan mənzil axtarır. Ona görə açıq, isti, etibar yaradan üslub
(daşınmaz əmlak saytları kimi), Bakı mənzərəsi və Xəzər üzərində günəş doğuşu.
Rəng məntiqi dashboard-dakı kimidir: yaşıl — əlçatan, kəhrəba — orta, mərcan/qırmızı — baha.
Hər funksiya HTML mətni qaytarır; app.py onu show(...) ilə göstərir. Animasiyalar yalnız CSS ilədir.
"""
from __future__ import annotations

import html
import math

C = {
    "bg": "#FBF8F3", "card": "#FFFFFF", "ink": "#1B2433", "muted": "#5E6B7D", "dim": "#8F9AA8",
    "line": "#ECE5DA", "track": "#F1EBE2",
    "sea": "#0F7C8C", "sea2": "#0B5A66", "sky": "#4C9BE8", "green": "#1F9D66",
    "amber": "#E8970F", "coral": "#E8613F", "red": "#C9412F", "violet": "#6F63E8", "sand": "#F7E7D3",
}
C["teal"], C["rose"] = C["green"], C["red"]          # köhnə adlar (app.py-də istifadə olunur)
TONE = {"teal": C["green"], "amber": C["amber"], "coral": C["coral"], "muted": C["muted"]}


def az(n: float, dec: int = 0) -> str:
    """1234.5 -> '1 235' (Azərbaycan yazılışı: minliklər boşluqla)."""
    if n is None or n != n:
        return "—"
    s = f"{n:,.{dec}f}".replace(",", " ")
    return s.replace(".", ",") if dec else s


def pct(x: float) -> str:
    if x is None or x != x:
        return "—"
    if 0 < x < 0.005:  # 0.4% «0%» görünməsin — elan var, sadəcə azdır
        return "<1%"
    return f"{round(x * 100)}%"


def up(s: str) -> str:
    """Azərbaycan dilində böyük hərf: i -> İ."""
    return s.replace("i", "İ").upper()


def esc(s) -> str:
    return html.escape(str(s))


def share_color(s: float) -> str:
    if s >= 0.5:
        return C["green"]
    if s >= 0.2:
        return C["amber"]
    if s >= 0.05:
        return C["coral"]
    return C["red"]


def share_rgb(s: float) -> list[int]:
    h = share_color(s).lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


# --------------------------------------------------------------------------- CSS
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
:root{
  --bg:#FBF8F3; --card:#FFFFFF; --ink:#1B2433; --muted:#5E6B7D; --dim:#8F9AA8; --line:#ECE5DA; --track:#F1EBE2;
  --sea:#0F7C8C; --sea2:#0B5A66; --sky:#4C9BE8; --green:#1F9D66; --amber:#E8970F; --coral:#E8613F; --red:#C9412F; --violet:#6F63E8;
  --sun:linear-gradient(100deg,#E8613F 0%,#F2994A 55%,#F6B73C 100%);
  --seag:linear-gradient(100deg,#0B5A66 0%,#0F7C8C 50%,#16A3A8 100%);
  --shadow:0 1px 2px rgba(27,36,51,.04), 0 12px 32px -14px rgba(27,36,51,.18);
}
@property --num { syntax:'<integer>'; initial-value:0; inherits:false; }
@property --a { syntax:'<angle>'; initial-value:0deg; inherits:false; }

html, body, .stApp, [data-testid="stAppViewContainer"]{ background:var(--bg) !important; }
.stApp{ color:var(--ink); font-family:'Inter',system-ui,sans-serif; }
[data-testid="stAppViewContainer"]::before{
  content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
  background:
    radial-gradient(60% 40% at 10% 0%, rgba(246,183,60,.16), transparent 70%),
    radial-gradient(50% 40% at 95% 5%, rgba(76,155,232,.12), transparent 70%);
}
[data-testid="stHeader"]{ background:transparent !important; }
[data-testid="stToolbar"], #MainMenu, footer, [data-testid="stDecoration"]{ display:none !important; }
.block-container{ max-width:1240px !important; padding:.6rem 1.6rem 5rem !important; position:relative; z-index:1; }
h1,h2,h3,h4{ font-family:'Manrope',sans-serif !important; letter-spacing:-.02em; color:var(--ink) !important; }
p, label, .stMarkdown, li{ color:var(--ink); }
a{ color:var(--sea) !important; }
.cta, .cta *{ color:#FFFFFF !important; }

/* --- widgets --- */
[data-testid="stWidgetLabel"] p{ color:var(--muted) !important; font-weight:600 !important; font-size:.86rem !important; }
[data-baseweb="input"], [data-baseweb="select"] > div{ background:#FFFFFF !important; border:1px solid #E3DACD !important; border-radius:12px !important; }
[data-baseweb="input"] input{ color:var(--ink) !important; font-weight:700; font-size:1.05rem; }
[data-testid="stSlider"] [role="slider"]{ box-shadow:0 0 0 6px rgba(15,124,140,.15) !important; }
[data-testid="stSliderThumbValue"]{ color:var(--sea) !important; font-weight:800; }
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"]{
  border:0 !important; border-radius:999px !important; padding:.62rem 1.3rem !important; font-weight:700 !important;
  background:var(--seag) !important; color:#fff !important; box-shadow:0 10px 24px -10px rgba(15,124,140,.7);
  transition:transform .2s ease, box-shadow .2s ease; }
.stButton > button:hover{ transform:translateY(-2px); }
[data-testid="stBaseButton-pills"], [data-testid="stBaseButton-segmented_control"]{ background:#fff !important; border-color:#E3DACD !important; color:var(--ink) !important; }
[data-testid="stBaseButton-pills"], [data-testid="stBaseButton-pillsActive"]{ border-radius:999px !important; }
[data-testid="stBaseButton-pillsActive"], [data-testid="stBaseButton-segmented_controlActive"]{
  background:rgba(15,124,140,.10) !important; border-color:var(--sea) !important; color:var(--sea2) !important; font-weight:700 !important; }
[data-testid="stDataFrame"]{ border-radius:16px; overflow:hidden; border:1px solid var(--line); }
[data-testid="stChatMessage"]{ background:#FFFFFF; border:1px solid var(--line); border-radius:16px; }
[data-testid="stDeckGlJsonChart"]{ border-radius:18px; overflow:hidden; }

/* --- st.container(key=...) kartları --- */
.st-key-calc, .st-key-listings, .st-key-ai, .st-key-mapcard{
  background:var(--card); border:1px solid var(--line); border-radius:24px; padding:22px 22px 18px !important; box-shadow:var(--shadow); }
.st-key-mapcard{ padding:18px !important; }
.st-key-ai{ position:relative; }
.st-key-ai::before{ content:""; position:absolute; inset:-1px; border-radius:25px; padding:2px; pointer-events:none;
  background:conic-gradient(from var(--a), #0F7C8C, #4C9BE8, #F6B73C, #E8613F, #0F7C8C);
  -webkit-mask:linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite:xor; mask-composite:exclude;
  animation:spin 8s linear infinite; }
.st-key-ai h3{ font-size:1.12rem !important; margin:.9rem 0 .3rem !important; color:var(--sea2) !important; }
.st-key-ai li, .st-key-ai p{ font-size:.98rem; line-height:1.6; }
@keyframes spin{ to{ --a:360deg; } }

/* --- building blocks --- */
.kk *{ box-sizing:border-box; }
.kk{ font-family:'Inter',sans-serif; color:var(--ink); }
.disp{ font-family:'Manrope',sans-serif; font-weight:800; letter-spacing:-.03em; }
.sun{ background:var(--sun); -webkit-background-clip:text; background-clip:text; color:transparent; }
.muted{ color:var(--muted); } .dim{ color:var(--dim); }
.eyebrow{ font-size:.74rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); }
.card{ background:var(--card); border:1px solid var(--line); border-radius:22px; padding:22px; position:relative; overflow:hidden;
  box-shadow:var(--shadow); transition:transform .3s ease, box-shadow .3s ease; }
.card:hover{ transform:translateY(-3px); box-shadow:0 1px 2px rgba(27,36,51,.05), 0 20px 40px -16px rgba(27,36,51,.25); }
.pill{ display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:999px; font-size:.8rem; font-weight:600;
  border:1px solid var(--line); background:#FFFFFF; }
.dot{ width:8px; height:8px; border-radius:50%; display:inline-block; }
.live{ animation:pulse 1.8s ease-in-out infinite; }
@keyframes pulse{ 0%,100%{ opacity:1; transform:scale(1);} 50%{ opacity:.35; transform:scale(.7);} }
.rise{ opacity:0; animation:rise .9s cubic-bezier(.2,.8,.2,1) forwards; }
@keyframes rise{ from{ opacity:0; transform:translateY(16px);} to{ opacity:1; transform:none;} }
.cu{ animation:cu 1.8s cubic-bezier(.2,.8,.2,1) forwards; counter-reset:num var(--num); }
.cu::after{ content:counter(num); }
@keyframes cu{ from{ --num:0; } to{ --num:var(--to); } }
.bar{ height:100%; border-radius:999px; width:0; animation:grow 1.2s cubic-bezier(.2,.8,.2,1) forwards; }
@keyframes grow{ to{ width:var(--w); } }
.arc{ animation:arc 1.8s cubic-bezier(.2,.8,.2,1) forwards; }
@keyframes arc{ to{ stroke-dashoffset:var(--off); } }
.marquee{ overflow:hidden; mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent); }
.marquee .track{ display:inline-flex; gap:40px; white-space:nowrap; animation:scroll 50s linear infinite; padding:12px 0; }
@keyframes scroll{ to{ transform:translateX(-50%); } }
/* hero səhnəsi */
.sunball{ transform-box:fill-box; transform-origin:center; animation:sunrise 3.2s cubic-bezier(.2,.8,.2,1) both; }
@keyframes sunrise{ from{ transform:translateY(70px); opacity:.2;} to{ transform:none; opacity:1;} }
.wave{ animation:wave 9s linear infinite; }
.wave2{ animation:wave 14s linear infinite reverse; }
@keyframes wave{ to{ transform:translateX(-200px); } }
.cloud{ animation:cloud 60s linear infinite; }
@keyframes cloud{ from{ transform:translateX(-200px);} to{ transform:translateX(1400px);} }
.glint{ animation:glint 3s ease-in-out infinite; }
@keyframes glint{ 0%,100%{ opacity:.25;} 50%{ opacity:.8;} }
.nav a{ color:var(--muted) !important; text-decoration:none; font-weight:600; font-size:.9rem; padding:8px 12px; border-radius:999px; transition:all .2s; }
.nav a:hover{ color:var(--ink) !important; background:rgba(27,36,51,.05); }
.sec{ margin:60px 0 16px; }
.sec h2{ font-size:2.1rem; margin:6px 0 6px; line-height:1.12; }
.sec p{ color:var(--muted); max-width:760px; margin:0; font-size:1.02rem; }
@media (max-width: 760px){
  .hero-grid{ grid-template-columns:1fr !important; }
  .hero h1{ font-size:2.5rem !important; }
  .sec h2{ font-size:1.65rem; }
  .grid3, .grid4{ grid-template-columns:1fr !important; }
  .nav .links{ display:none !important; }
  .res-grid{ grid-template-columns:1fr !important; justify-items:center; }
  .res-grid > div:last-child{ width:100%; }
  .hb{ grid-template-columns:96px 1fr 58px !important; gap:8px !important; }
  .hb .disp{ font-size:.85rem !important; }
}
</style>
"""


# --------------------------------------------------------------------------- pieces
def cu(value: int, delay: float = 0.0) -> str:
    """Sıfırdan sayan tam ədəd (CSS counter)."""
    return f'<span class="cu" style="--to:{int(value)};animation-delay:{delay}s"></span>'


def reveal(text: str, delay: float = 0.0) -> str:
    return f'<span class="rise" style="display:inline-block;animation-delay:{delay}s">{esc(text)}</span>'


def ring(p: float, size: int = 220, stroke: int = 16, label: str = "", sub: str = "",
         mark: float | None = None, colors=("#E8613F", "#F6B73C"), uid: str = "r", delay: float = 0.2) -> str:
    """Animasiyalı halqa. p: 0..1."""
    r = (size - stroke) / 2 - 6
    c = 2 * math.pi * r
    off = c * (1 - min(max(p, 0), 1))
    cx = size / 2
    tick = ""
    if mark is not None:
        ang = -math.pi / 2 + 2 * math.pi * mark
        x1, y1 = cx + (r - stroke) * math.cos(ang), cx + (r - stroke) * math.sin(ang)
        x2, y2 = cx + (r + stroke) * math.cos(ang), cx + (r + stroke) * math.sin(ang)
        tick = f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{C["green"]}" stroke-width="3.5" stroke-linecap="round"/>'
    big = min(round(p * 100), 999)
    return f"""
<div style="position:relative;width:{size}px;height:{size}px;flex:none">
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="display:block;overflow:visible">
<defs><linearGradient id="g{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{colors[0]}"/><stop offset="1" stop-color="{colors[1]}"/></linearGradient></defs>
<circle cx="{cx}" cy="{cx}" r="{r:.1f}" fill="none" stroke="{C['track']}" stroke-width="{stroke}"/>
<circle cx="{cx}" cy="{cx}" r="{r:.1f}" fill="none" stroke="url(#g{uid})" stroke-width="{stroke}" stroke-linecap="round"
 stroke-dasharray="{c:.1f}" stroke-dashoffset="{c:.1f}" transform="rotate(-90 {cx} {cx})" class="arc" style="--off:{off:.1f};animation-delay:{delay}s"/>
{tick}
</svg>
<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;font-family:Manrope,sans-serif;padding:0 {stroke + 18}px">
<div style="font-size:{size * 0.22:.0f}px;font-weight:800;line-height:1;color:{C['ink']}">{cu(big, delay)}<span style="font-size:.55em">%</span></div>
<div style="font-size:13px;color:{C['muted']};margin-top:6px;line-height:1.2">{esc(label)}</div>
<div style="font-size:11px;color:{C['dim']};margin-top:3px;line-height:1.2">{esc(sub)}</div>
</div>
</div>"""


def hbar(label: str, value_txt: str, w: float, color: str, delay: float = 0.0, sub: str = "", marker: float | None = None,
         lw: int = 190, vw: int = 96) -> str:
    """Bir sətirlik üfüqi zolaq: etiket | zolaq | dəyər. w: 0..1."""
    mk = (f'<div style="position:absolute;left:{marker * 100:.1f}%;top:-6px;bottom:-6px;width:2px;border-radius:2px;background:{C["green"]}"></div>'
          if marker is not None else "")
    return f"""
<div class="hb" style="display:grid;grid-template-columns:{lw}px 1fr {vw}px;gap:12px;align-items:center;margin:9px 0">
<div style="font-weight:600;font-size:.92rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{esc(label)}<div class="dim" style="font-size:.7rem;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{esc(sub)}</div></div>
<div style="position:relative;height:12px;border-radius:999px;background:{C['track']}">
<div class="bar" style="--w:{max(min(w, 1), 0.004) * 100:.1f}%;animation-delay:{delay}s;background:linear-gradient(90deg,{color}AA,{color})"></div>{mk}
</div>
<div class="disp" style="text-align:right;font-size:1rem;color:{color}">{esc(value_txt)}</div>
</div>"""


COMPASS = """<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9.5" stroke="#fff" stroke-width="2"/>
<path d="M15.5 8.5l-2 5-5 2 2-5z" fill="#fff"/></svg>"""


# --------------------------------------------------------------------------- sections
def nav(n_listings: int, date: str) -> str:
    links = "".join(f'<a href="#{a}">{t}</a>' for a, t in
                    [("kalkulyator", "Kalkulyator"), ("rayonlar", "Rayonlar"), ("elanlar", "Elanlar"), ("ai", "AI məsləhətçi"), ("bazar", "Bazar")])
    return f"""
<div class="kk nav" style="display:flex;align-items:center;justify-content:space-between;gap:16px;padding:8px 4px 0">
<div style="display:flex;align-items:center;gap:12px">
<div style="width:42px;height:42px;border-radius:13px;background:var(--seag);display:grid;place-items:center;box-shadow:0 8px 20px -8px rgba(15,124,140,.8)">{COMPASS}</div>
<div><div class="disp" style="font-size:1.12rem">Kirayə Kompası</div><div class="dim" style="font-size:.75rem">Bakı · maaş və kirayə</div></div>
</div>
<div class="links" style="display:flex;gap:2px">{links}</div>
<div class="pill"><span class="dot live" style="background:{C['green']}"></span>{az(n_listings)} elan · {esc(date)}</div>
</div>"""


def skyline() -> str:
    """Xəzər üzərində günəş doğuşu və Bakı sahili (stilizə olunmuş siluet)."""
    far = "".join(f'<rect x="{x}" y="{240 - h}" width="{w}" height="{h}" rx="2"/>' for x, w, h in
                  [(20, 34, 60), (60, 26, 84), (92, 40, 52), (140, 22, 98), (168, 36, 70), (214, 28, 58), (250, 44, 90), (300, 24, 64),
                   (330, 38, 104), (376, 30, 72), (414, 46, 56), (470, 28, 88), (505, 36, 66), (560, 30, 94), (600, 42, 60), (650, 26, 80),
                   (684, 38, 110), (730, 30, 70), (770, 44, 58), (824, 26, 86), (860, 40, 64), (910, 30, 96), (948, 36, 62), (994, 28, 78),
                   (1030, 44, 100), (1082, 30, 68), (1120, 40, 84), (1166, 30, 60)])
    near = "".join(f'<rect x="{x}" y="{250 - h}" width="{w}" height="{h}" rx="3"/>' for x, w, h in
                   [(0, 60, 40), (70, 44, 64), (124, 70, 46), (205, 40, 72), (255, 66, 54), (330, 48, 38), (390, 58, 62),
                    (520, 64, 44), (595, 46, 58), (650, 70, 40), (735, 44, 66), (790, 62, 48), (1000, 56, 50), (1066, 48, 70), (1124, 76, 42)])
    wins = "".join(f'<rect x="{x + 8 + (i % 3) * 14}" y="{250 - h + 10 + (i // 3) * 14}" width="5" height="7" rx="1"/>'
                   for x, w, h in [(70, 44, 64), (205, 40, 72), (390, 58, 62), (595, 46, 58), (735, 44, 66), (1066, 48, 70)]
                   for i in range(6) if 10 + (i // 3) * 14 < h - 12)
    # üç «alov» qüllə (sağda, təpədə), Qız qalası (solda) və TV qülləsi — Bakının tanınan silueti
    towers = """
<path d="M884 250 C880 190 892 150 912 120 C920 160 918 205 916 250 Z"/>
<path d="M918 250 C914 180 928 128 952 96 C962 150 956 205 954 250 Z"/>
<path d="M956 250 C952 196 962 160 980 134 C988 172 986 210 984 250 Z"/>
<rect x="452" y="196" width="40" height="54" rx="18"/><rect x="448" y="192" width="48" height="8" rx="3"/>
<rect x="836" y="110" width="5" height="140"/><ellipse cx="838.5" cy="122" rx="9" ry="6"/>"""
    return f"""
<svg viewBox="0 0 1200 320" preserveAspectRatio="xMidYMax slice" width="100%" height="100%" style="position:absolute;inset:0;display:block">
<defs>
<radialGradient id="sg" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFE3A3"/><stop offset=".55" stop-color="#FFB862"/><stop offset="1" stop-color="#FF9A5A"/></radialGradient>
<radialGradient id="halo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFC27A" stop-opacity=".55"/><stop offset="1" stop-color="#FFC27A" stop-opacity="0"/></radialGradient>
<linearGradient id="sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8FCAD0"/><stop offset="1" stop-color="#4FA3AE"/></linearGradient>
</defs>
<g class="cloud" opacity=".8" style="animation-delay:-20s"><ellipse cx="120" cy="120" rx="60" ry="13" fill="#fff"/><ellipse cx="160" cy="112" rx="40" ry="11" fill="#fff"/></g>
<g class="cloud" opacity=".6" style="animation-duration:85s;animation-delay:-50s"><ellipse cx="420" cy="90" rx="70" ry="12" fill="#fff"/></g>
<g class="sunball"><circle cx="1010" cy="150" r="120" fill="url(#halo)"/><circle cx="1010" cy="150" r="56" fill="url(#sg)"/></g>
<g fill="#B5D1D5" opacity=".85">{far}</g>
<g fill="#6FA6AE">{near}{towers}</g>
<g fill="#FFE9C2" opacity=".55">{wins}</g>
<rect x="0" y="250" width="1200" height="70" fill="url(#sea)"/>
<g class="glint" fill="#FFE2B0"><rect x="965" y="258" width="90" height="3" rx="1.5"/><rect x="975" y="269" width="70" height="3" rx="1.5"/><rect x="983" y="280" width="54" height="3" rx="1.5"/><rect x="991" y="291" width="38" height="3" rx="1.5"/><rect x="998" y="302" width="24" height="3" rx="1.5"/></g>
<g class="wave" stroke="#fff" stroke-width="2" fill="none" opacity=".7">
<path d="M0 266 q25 -6 50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0"/></g>
<g class="wave2" stroke="#fff" stroke-width="1.5" fill="none" opacity=".45">
<path d="M0 290 q30 -5 60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0"/></g>
</svg>"""


def hero(f: dict) -> str:
    stats = [
        (az(f["median_2_city"]) + " AZN", "2 otaqlı mənzilin tipik kirayəsi", "Bakı şəhəri, median", C["coral"]),
        (az(f["need_salary_2"]) + " AZN", "normaya sığmaq üçün lazım olan maaş", f"Bakıda orta maaş {az(f['baku_salary'])} AZN", C["sea"]),
        (pct(f["agency_share"]), "elanları vasitəçilər verir", f"vasitəçi {az(f['agency'])} vs sahibi {az(f['owner'])} AZN", C["violet"]),
    ]
    chips = "".join(f"""
<div class="card rise" style="padding:16px 18px;animation-delay:{0.5 + i * 0.12:.2f}s">
<div class="disp" style="font-size:1.55rem;color:{col}">{esc(v)}</div>
<div style="font-size:.88rem;margin-top:4px;font-weight:600">{esc(t)}</div><div class="dim" style="font-size:.75rem;margin-top:2px">{esc(s)}</div>
</div>""" for i, (v, t, s, col) in enumerate(stats))
    return f"""
<div class="kk hero" style="margin-top:20px;position:relative;border-radius:30px;overflow:hidden;border:1px solid #F1E3D3;
 background:linear-gradient(180deg,#FFE4CC 0%,#FFF1E3 40%,#EEF6F6 78%,#E3F1F2 100%);box-shadow:var(--shadow)">
<div style="position:absolute;left:0;right:0;bottom:0;height:300px">{skyline()}</div>
<div class="hero-grid" style="position:relative;display:grid;grid-template-columns:1.25fr .85fr;gap:30px;align-items:center;padding:40px 44px 215px">
<div>
<div class="pill rise" style="background:rgba(255,255,255,.75);backdrop-filter:blur(6px)"><span class="dot" style="background:{C['coral']}"></span>bina.az-dakı bütün aylıq kirayə elanları əsasında</div>
<h1 class="disp rise" style="font-size:3.9rem;line-height:1.03;margin:16px 0 14px;animation-delay:.1s">Maaşın Bakıda <span class="sun">nəyə</span> çatır?</h1>
<p class="rise" style="font-size:1.1rem;max-width:560px;color:#3E4A5C;animation-delay:.25s">Maaşını yaz — hansı rayonda neçə real mənzilin sənə uyğun olduğunu,
kirayənin maaşının neçə faizini apardığını və necə ucuzlaşdırmaq olacağını gör. Süni intellekt nəticəni sadə dillə izah edir.</p>
<div class="rise" style="margin-top:20px;display:flex;gap:10px;flex-wrap:wrap;animation-delay:.35s">
<a class="cta" href="#kalkulyator" style="text-decoration:none"><span class="pill" style="background:var(--seag);border:0;padding:12px 22px;font-size:.95rem;box-shadow:0 10px 24px -10px rgba(15,124,140,.8)">Hesabla →</span></a>
<a href="#bazar" style="text-decoration:none"><span class="pill" style="color:{C['ink']};padding:12px 20px;font-size:.95rem;background:rgba(255,255,255,.8)">Bazarı gör</span></a>
</div>
</div>
<div class="card rise" style="display:flex;flex-direction:column;align-items:center;padding:22px 20px;background:rgba(255,255,255,.88);backdrop-filter:blur(10px);animation-delay:.2s">
<div class="eyebrow">Əsas problem</div>
{ring(f["burden_2_city"], 230, 17, "orta maaşın", "2 otaqlı median kirayə ÷ Bakı maaşı", mark=0.30, uid="hero", delay=0.5)}
<div style="display:flex;gap:16px;margin-top:4px;font-size:.8rem" class="muted">
<span><span class="dot" style="background:{C['green']}"></span> norma 30%</span>
<span>ölkə maaşı ilə: <b style="color:{C['ink']}">{pct(f['median_2_city'] / f['country_salary'])}</b></span>
</div>
</div>
</div>
</div>
<div class="kk grid3" style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:18px">{chips}</div>"""


def ticker(items: list[tuple[str, str, str]]) -> str:
    one = "".join(f'<span style="display:inline-flex;gap:10px;align-items:center"><span class="eyebrow" style="letter-spacing:.1em">{esc(k)}</span>'
                  f'<b class="disp" style="color:{col};font-size:1.02rem">{esc(v)}</b><span style="color:{C["dim"]}">•</span></span>'
                  for k, v, col in items)
    return f'<div class="kk marquee card" style="padding:0 18px;margin-top:22px;border-radius:999px"><div class="track">{one}{one}</div></div>'


def section(anchor: str, eyebrow: str, title: str, text: str = "") -> str:
    return (f'<div class="kk sec" id="{anchor}"><div class="eyebrow" style="color:{C["sea"]}">{esc(eyebrow)}</div>'
            f'<h2 class="disp">{title}</h2>{f"<p>{esc(text)}</p>" if text else ""}</div>')


def mini(k: str, v: str, col: str) -> str:
    return (f'<div style="border:1px solid var(--line);border-radius:14px;padding:12px 14px;background:#FCFAF7">'
            f'<div class="dim" style="font-size:.74rem">{esc(k)}</div><div class="disp" style="font-size:1.05rem;color:{col};margin-top:3px">{esc(v)}</div></div>')


def few_note(n: int) -> str:
    """Az elan olanda median etibarlı deyil — istifadəçini xəbərdar et."""
    if n >= 30:
        return ""
    return (f'<div style="margin-top:8px;font-size:.82rem;color:{C["amber"]};font-weight:600">'
            f'⚠ Bu filtrlərlə cəmi {az(n)} elan var — rəqəmlər az elana əsaslanır, ehtiyatla bax.</div>')


def result_card(r, f: dict) -> str:
    p = r.p
    v_txt, v_tone = r.verdict
    tone = TONE[v_tone]
    bw = min(r.burden, 1) if r.burden == r.burden else 0
    people = f" · {p.people} nəfər" if p.people > 1 else ""
    need = az(r.need_salary) + " AZN" if r.need_salary == r.need_salary else "—"
    ring_cols = (C["green"], "#52C49A") if v_tone == "teal" else (C["coral"], "#F6B73C") if v_tone == "coral" else (C["amber"], "#F6C760")
    return f"""
<div class="kk card" style="padding:24px">
<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;flex-wrap:wrap">
<div><div class="eyebrow">Sənin büdcən</div>
<div class="disp" style="font-size:2.2rem;margin-top:4px">{reveal(az(p.budget) + ' AZN')}<span class="muted" style="font-size:1rem;font-weight:600"> / ay{esc(people)}</span></div>
<div class="dim" style="font-size:.8rem">gəlirin {pct(p.share)}-i · ümumi gəlir {az(p.income)} AZN</div></div>
<div class="pill" style="color:{tone};border-color:{tone}55;background:{tone}12;font-weight:700"><span class="dot live" style="background:{tone}"></span>{esc(v_txt)}</div>
</div>
<div class="res-grid" style="display:grid;grid-template-columns:auto 1fr;gap:22px;align-items:center;margin-top:12px">
{ring(r.fit_share, 190, 15, "elan sənə uyğundur", f"{az(r.fit_n)} / {az(r.seg_n)}", uid="res", colors=ring_cols)}
<div>
<div class="disp" style="font-size:2.6rem;line-height:1">{reveal(az(r.fit_n), .2)}</div>
<div class="muted" style="margin-bottom:14px">uyğun mənzil · seçdiyin filtrlərlə</div>
<div class="eyebrow" style="margin-bottom:6px">Kirayə yükü (median ÷ gəlir)</div>
<div style="position:relative;height:14px;border-radius:999px;background:{C['track']}">
<div class="bar" style="--w:{bw * 100:.1f}%;animation-delay:.3s;background:linear-gradient(90deg,{C['green']},{C['amber']},{C['coral']},{C['red']});background-size:{100 / max(bw, .01):.0f}% 100%"></div>
<div style="position:absolute;left:30%;top:-6px;bottom:-6px;width:2px;border-radius:2px;background:{C['green']}"></div>
</div>
<div style="display:flex;justify-content:space-between;font-size:.78rem;margin-top:6px" class="dim"><span>0%</span><span style="color:{C['green']};font-weight:600">norma 30%</span><span>100%</span></div>
<div style="margin-top:10px;font-size:.95rem">Median kirayə <b>{az(r.median)} AZN</b> → gəlirin <b style="color:{tone}">{pct(r.burden)}</b>-i</div>
{few_note(r.seg_n)}
</div>
</div>
<div class="grid3" style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:18px">
{mini("Orta 50% aralığı", f"{az(r.p25)}–{az(r.p75)} AZN", C['violet'])}
{mini("Normaya sığmaq üçün maaş", need + (" (nəfərə)" if p.people > 1 else ""), C['sea'])}
{mini("Ən uyğun rayon", r.districts.iloc[0]["district_name"] if len(r.districts) else "—", C['green'])}
</div>
</div>"""


def map_header() -> str:
    legend = "".join(f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:12px"><span class="dot" style="background:{c}"></span>{t}</span>'
                     for t, c in [("50%+", C["green"]), ("20–50%", C["amber"]), ("5–20%", C["coral"]), ("5%-dən az", C["red"])])
    return (f'<div class="kk"><div class="eyebrow">Bakı xəritəsi</div>'
            f'<div class="dim" style="font-size:.78rem;margin:2px 0 4px">dairə = elan sayı · rəng = büdcənə uyğun elanların payı · faiz və rayon adı üçün dairənin üstünə gətir</div>'
            f'<div class="muted" style="font-size:.78rem;margin-bottom:8px">{legend}</div></div>')


def district_bars(dist, budget: float) -> str:
    rows = [hbar(r.district_name, pct(r.share), r.share, share_color(r.share), .1 + i * .07,
                 sub=f"median {az(r.median)} AZN · {az(r.fit)} / {az(r.n)} elan") for i, r in enumerate(dist.head(10).itertuples())]
    return f"""
<div class="kk card" style="padding:18px 20px;height:100%">
<div class="eyebrow">Büdcənə ({az(budget)} AZN) uyğun elanların payı</div>
<div class="dim" style="font-size:.78rem;margin:2px 0 8px">ən azı 20 elanı olan rayonlar · yuxarıda — ən əlçatan</div>
{''.join(rows)}
</div>"""


def savings(steps: list, budget: float, cheap: list[str]) -> str:
    if not steps:
        return ""
    mx = max(s for _, s in steps) * 1.08
    cols = [C["red"], C["coral"], C["amber"], C["sky"], C["green"]]
    rows = []
    for i, (name, val) in enumerate(steps):
        delta = f" · −{az(steps[i - 1][1] - val)}" if i else ""
        rows.append(hbar(name, az(val) + " AZN", val / mx, cols[min(i, 4)], .15 + i * .18,
                         sub=("başlanğıc" if i == 0 else f"addım {i}{delta} AZN"), marker=min(budget / mx, 1), lw=260))
    last = steps[-1][1]
    return f"""
<div class="kk card" style="padding:18px 20px">
<div class="eyebrow">Necə ucuzlaşdırmaq olar — addım-addım</div>
<div class="dim" style="font-size:.78rem;margin:2px 0 8px">yaşıl xətt — sənin büdcən ({az(budget)} AZN) · ucuz rayonlar: {esc(', '.join(cheap))}</div>
{''.join(rows)}
<div style="margin-top:12px;font-size:.95rem">Nəticə: <b style="color:{C['green']}">{az(last)} AZN</b> — <span class="muted">başlanğıcdan {pct(1 - last / steps[0][1])} ucuz</span></div>
</div>"""


def insight_cards(f: dict, sect) -> str:
    rooms = f["rooms"]
    rmax = max(rooms.values())
    rbars = "".join(
        f'<div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex:1">'
        f'<div class="disp" style="font-size:.85rem">{az(v)}</div>'
        f'<div style="height:110px;width:70%;display:flex;align-items:flex-end"><div style="width:100%;border-radius:10px 10px 4px 4px;'
        f'background:linear-gradient(180deg,#F6B73C,#E8613F);height:0;animation:hgrow 1.2s cubic-bezier(.2,.8,.2,1) {.1 + i * .12:.2f}s forwards;--h:{v / rmax * 100:.0f}%"></div></div>'
        f'<div class="dim" style="font-size:.75rem">{k} otaq</div></div>'
        for i, (k, v) in enumerate(rooms.items()))
    ok1 = int((sect["burden"] <= 0.30).sum())
    dots = "".join(f'<span title="{esc(r.sector_name)}: {pct(r.burden)}" style="width:16px;height:16px;border-radius:50%;display:inline-block;'
                   f'background:{C["green"] if r.burden <= .3 else C["track"]};border:1px solid {C["green"] if r.burden <= .3 else "#E3DACD"};'
                   f'animation:popdot .5s {.2 + i * .05:.2f}s both"></span>' for i, r in enumerate(sect.itertuples()))
    ag, ow, nw, od = f["agency"], f["owner"], f["new"], f["old"]
    return f"""
<style>@keyframes hgrow{{to{{height:var(--h)}}}} @keyframes popdot{{from{{transform:scale(0)}}to{{transform:scale(1)}}}}</style>
<div class="kk grid4" style="display:grid;grid-template-columns:1.3fr 1fr 1fr;gap:16px">
<div class="card"><div class="eyebrow">1 · Otaq sayı — əsas amil</div><div class="dim" style="font-size:.8rem;margin:2px 0 10px">median kirayə, bütün Bakı</div>
<div style="display:flex;gap:6px">{rbars}</div></div>
<div class="card"><div class="eyebrow">2 · Vasitəçi vs sahibi</div>
<div class="disp" style="font-size:2.3rem;margin-top:8px;color:{C['coral']}">+{pct(ag / ow - 1)}</div>
<div class="muted" style="font-size:.9rem">vasitəçi elanı {az(ag)} AZN, sahibinin elanı {az(ow)} AZN</div>
{hbar("Vasitəçi", az(ag), 1, C['coral'], .3, lw=72, vw=60)}{hbar("Sahibi", az(ow), ow / ag, C['green'], .45, lw=72, vw=60)}</div>
<div class="card"><div class="eyebrow">3 · Yeni vs köhnə tikili</div>
<div class="disp" style="font-size:2.3rem;margin-top:8px;color:{C['violet']}">−{pct(1 - od / nw)}</div>
<div class="muted" style="font-size:.9rem">köhnə tikili ucuzdur, amma fərq əsasən sahədən gəlir</div>
{hbar("Yeni", az(nw), 1, C['violet'], .3, lw=72, vw=60)}{hbar("Köhnə", az(od), od / nw, C['sky'], .45, lw=72, vw=60)}</div>
</div>
<div class="kk card" style="margin-top:16px;display:grid;grid-template-columns:1fr 1.4fr;gap:20px;align-items:center">
<div><div class="eyebrow">4 · Kimin maaşı çatır?</div>
<div class="disp" style="font-size:2.6rem;margin-top:6px;color:{C['coral']}">{ok1} / {len(sect)}</div>
<div class="muted">sahənin orta maaşı 1 otaqlı mənzili 30% normasında ödəyir</div>
<div class="dim" style="font-size:.76rem;margin-top:6px">DSK {f['salary_year']} · sahələr üzrə orta maaş (ölkə) · dairənin üstünə gətir</div></div>
<div style="display:flex;flex-wrap:wrap;gap:10px">{dots}</div>
</div>"""


def ai_header() -> str:
    return f"""
<div class="kk" style="display:flex;align-items:center;gap:14px;margin-bottom:6px">
<div style="width:46px;height:46px;border-radius:14px;display:grid;place-items:center;background:var(--seag);box-shadow:0 8px 20px -8px rgba(15,124,140,.8)">
<svg width="22" height="22" viewBox="0 0 24 24" fill="#fff"><path d="M12 2l2.2 6.3L20 10l-5.8 1.7L12 18l-2.2-6.3L4 10l5.8-1.7z"/></svg></div>
<div><div class="disp" style="font-size:1.3rem">AI məsləhətçi</div>
<div class="dim" style="font-size:.82rem">Gemini nəticəni yalnız bizim real rəqəmlərimizə əsaslanaraq sadə dillə izah edir</div></div>
</div>"""


def footer(f: dict, captured: str, raw: int) -> str:
    return f"""
<div class="kk" style="margin-top:70px;padding:26px 4px;border-top:1px solid var(--line);display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:24px;font-size:.85rem">
<div><div style="display:flex;align-items:center;gap:10px"><div style="width:30px;height:30px;border-radius:9px;background:var(--seag);display:grid;place-items:center">{COMPASS.replace('width="24" height="24"', 'width="18" height="18"')}</div>
<div class="disp" style="font-size:1.05rem">Kirayə Kompası</div></div>
<div class="muted" style="margin-top:8px">Data final layihəsi · Python → Oracle (SQL) → Power BI → bu sayt + Gemini. Rəqəmlər Power BI dashboard-u ilə eyni mənbədəndir.</div></div>
<div><div class="eyebrow">Mənbələr</div>
<div class="muted" style="margin-top:6px">bina.az — {az(raw)} xam elan, təmizləmədən sonra {az(f['n'])} unikal (toplama: {esc(captured[:16])})<br>
Dövlət Statistika Komitəsi — orta aylıq nominal əməkhaqqı, {f['salary_year']}</div></div>
<div><div class="eyebrow">Qeyd</div>
<div class="muted" style="margin-top:6px">Elan qiyməti — istənilən qiymətdir; maaş vergidən əvvəldir. Nəticə məlumat xarakteri daşıyır.</div></div>
</div>"""

def salary_compare(r, f: dict) -> str:
    """Sənin maaşın vs Bakı ortası vs normaya sığmaq üçün lazım olan maaş."""
    p = r.p
    need = r.need_salary if r.need_salary == r.need_salary else 0
    vals = [("Sənin maaşın", p.salary, C["sea"]), ("Bakıda orta maaş", f["baku_salary"], C["dim"]),
            ("Lazım olan (30%)", need, C["coral"])]
    mx = max(v for _, v, _ in vals) * 1.05 or 1
    rows = "".join(hbar(k, az(v) + " AZN", v / mx, col, .2 + i * .15, lw=130, vw=96) for i, (k, v, col) in enumerate(vals))
    gap = need - p.salary
    msg = (f"Normaya sığmaq üçün maaşın <b style='color:{C['coral']}'>{az(gap)} AZN</b> çox olmalıdır"
           if gap > 0 else f"Maaşın normaya sığır — <b style='color:{C['green']}'>{az(-gap)} AZN</b> ehtiyat qalır")
    return f"""
<div class="kk card" style="padding:18px 22px;margin-top:16px">
<div class="eyebrow">Maaşın haradadır?</div>
{rows}
<div style="font-size:.92rem;margin-top:8px">{msg} <span class="dim">(bir nəfər üçün, seçdiyin mənzil növünə görə)</span></div>
</div>"""
