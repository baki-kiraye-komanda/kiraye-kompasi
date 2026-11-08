"""
app.py — «Kirayə Kompası» saytı (Streamlit).

İşə salmaq (lokal):   run_site.bat   və ya   streamlit run app/app.py
Məlumat:              app/data/*.csv (Oracle → export_data.py)
AI:                   Gemini (ai.py); açar olmasa sayt AI-sız işləyir.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai    # noqa: E402
import core  # noqa: E402
import ui    # noqa: E402
import importlib  # noqa: E402

for _m in (core, ui, ai):  # kod dəyişəndə serveri yenidən başlatmadan yeni versiya götürülsün
    importlib.reload(_m)

st.set_page_config(page_title="Kirayə Kompası — Bakıda maaş nəyə çatır?", page_icon="🧭",
                   layout="wide", initial_sidebar_state="collapsed")


def show(html: str) -> None:
    """HTML/SVG blokunu göstərir. st.html SVG-ni silir, ona görə st.markdown istifadə olunur;
    boş sətir və girintilər markdown-un HTML-i «kod» kimi oxumaması üçün silinir."""
    body = "".join(x.strip() + "\n" for x in html.splitlines() if x.strip())
    st.markdown(body if body.startswith("<style") else f'<div lang="az">{body}</div>', unsafe_allow_html=True)


show(ui.CSS)


@st.cache_resource(show_spinner=False, max_entries=2)
def load_data(version: str):
    """Məlumat bir dəfə yüklənir; həftəlik yeniləmədə snapshot.csv dəyişir → keş avtomatik yenilənir."""
    return core.load()


def data_version() -> str:
    try:
        return (core.DATA / "snapshot.csv").read_text(encoding="utf-8")
    except OSError:
        return ""


data = load_data(data_version())
facts = core.market_facts(data)
SECTOR_NONE = "— Özüm yazacam —"
FEEDBACK_FORM = "https://forms.gle/gBcHsGWFEkGnqoBA8"  # Google Form: tools/google_form.gs ilə yaradılıb
SECTORS = {f"{r.sector_name} · {ui.az(r.avg_salary_azn)} AZN": float(r.avg_salary_azn) for r in data.sectors.itertuples()}

# ------------------------------------------------------------------ yuxarı hissə
date = data.captured_at[8:10] + "." + data.captured_at[5:7] + "." + data.captured_at[:4]
show(ui.nav(facts["n"], date))
show(ui.hero(facts))

med = data.listings.groupby("district_name").agg(size=("price_azn", "size"), median=("price_azn", "median"), m2=("price_per_m2", "median"))
med = med[med["size"] >= 20].sort_values(["median", "m2"], ascending=False)  # bərabər median: 1 m² qiyməti həll edir (Power BI-dakı kimi)
items = [("2 otaqlı · Bakı", ui.az(facts["median_2_city"]) + " AZN", ui.C["amber"]),
         ("Lazım olan maaş", ui.az(facts["need_salary_2"]) + " AZN", ui.C["coral"]),
         ("Masazır · 2 otaq", ui.az(facts["masazir_2"]) + " AZN", ui.C["teal"]) if facts["masazir_2"] else None,
         ("Vasitəçi / sahibi", f"{ui.az(facts['agency'])} / {ui.az(facts['owner'])} AZN", ui.C["violet"])]
items = [i for i in items if i] + [(ui.up(k), ui.az(v) + " AZN", ui.C["coral"] if v > facts["median"] else ui.C["teal"])
                                   for k, v in med["median"].items()]
show(ui.ticker(items))

# ------------------------------------------------------------------ 1 · kalkulyator
show(ui.section("kalkulyator", "1 · Kalkulyator", "Sənin vəziyyətin",
                   "Maaşını yaz və seçimlərini et — nəticə dərhal yenilənir. Rəqəmlər bina.az-dakı real elanlardan hesablanır."))


def _sector_changed():
    s = st.session_state.get("sector")
    if s and s != SECTOR_NONE:
        st.session_state["salary"] = int(round(SECTORS[s] / 10) * 10)


if "salary" not in st.session_state:
    st.session_state["salary"] = int(round(data.baku_salary))

left, right = st.columns([0.86, 1.14], gap="large")
with left:
    with st.container(key="calc"):
        st.selectbox("Sahən (istəsən, maaş sahənin orta maaşı ilə dolar)", [SECTOR_NONE] + list(SECTORS),
                     key="sector", on_change=_sector_changed)
        salary = st.number_input("Aylıq maaş (bir nəfər, AZN, vergidən əvvəl)", min_value=100, max_value=30000,
                                 step=50, key="salary")
        share = st.slider("Maaşın neçə faizini kirayəyə ayırırsan?", 10, 60, 30, 5, format="%d%%",
                          help="Beynəlxalq praktikada 30% normal sayılır") / 100
        rooms = st.segmented_control("Otaq sayı", ["Hamısı", "1", "2", "3", "4", "5+"], default="2", key="rooms") or "Hamısı"
        people = st.segmented_control("Kirayəni neçə nəfər bölür? (hər biri təxminən eyni maaşla)", [1, 2, 3, 4],
                                      default=1, key="people") or 1
        btype = st.segmented_control("Tikili növü", ["Hamısı", "Yeni tikili", "Köhnə tikili"], default="Hamısı", key="btype") or "Hamısı"
        area = st.segmented_control("Ərazi", ["Hamısı", "Bakı şəhəri", "Bakı ətrafı"], default="Hamısı", key="area",
                                    help="Bakı ətrafı = Abşeron rayonu (Masazır və s.)") or "Hamısı"
        owner = st.toggle("Yalnız sahibindən (vasitəçisiz) elanlar", key="owner")

params = core.Params(salary=float(salary), share=share, people=int(people), rooms=rooms, btype=btype,
                     area=area, owner_only=owner)
res = core.compute(data, params)
with right:
    show(ui.result_card(res, facts))
    show(ui.salary_compare(res, facts))

# ------------------------------------------------------------------ 2 · rayonlar
def district_map(dist) -> None:
    """Bakının real xəritəsi (CARTO açıq fon, token lazım deyil): rayon dairələri, rəng = büdcəyə uyğun pay."""
    import pydeck as pdk

    d = dist.dropna(subset=["latitude", "longitude"]).copy()
    nmax = d["n"].max()
    d["radius"] = 450 + 1500 * (d["n"] / nmax) ** 0.5
    d["color"] = [ui.share_rgb(s) + [190] for s in d["share"]]
    d["median_txt"] = d["median"].map(ui.az)
    d["share_txt"] = (d["share"] * 100).round().astype(int).astype(str) + "%"
    d = d[["district_name", "latitude", "longitude", "radius", "color", "median_txt", "share_txt", "n", "fit"]]
    circles = pdk.Layer("ScatterplotLayer", d, get_position="[longitude, latitude]", get_radius="radius",
                        get_fill_color="color", stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=2,
                        pickable=True, radius_min_pixels=8)
    deck = pdk.Deck(layers=[circles], map_provider="carto", map_style="light",
                    initial_view_state=pdk.ViewState(latitude=40.405, longitude=49.90, zoom=10.1, pitch=0),
                    tooltip={"html": "<b>{district_name}</b><br/>büdcəyə uyğun: <b>{share_txt}</b> ({fit} / {n} elan)<br/>median kirayə: {median_txt} AZN",
                             "style": {"background": "#1B2433", "color": "#fff", "borderRadius": "10px", "fontSize": "13px", "padding": "8px 10px"}})
    st.pydeck_chart(deck, height=440)



show(ui.section("rayonlar", "2 · Rayonlar", "Harada axtarmalı?",
                   "Hər rayonda elanların neçə faizi sənin büdcənə uyğundur. Yaşıl — seçim çoxdur, qırmızı — demək olar ki, yoxdur."))
if len(res.districts):
    m1, m2 = st.columns([1.1, 1], gap="medium")
    with m1:
        with st.container(key="mapcard"):
            show(ui.map_header())
            district_map(res.districts)
    with m2:
        show(ui.district_bars(res.districts, params.budget))
else:
    st.info("Bu filtrlərlə ən azı 20 elanı olan rayon yoxdur — filtrləri genişləndir.")
show('<div style="height:16px"></div>')
show(ui.savings(res.savings, params.budget, res.cheap_names))

# ------------------------------------------------------------------ 3 · real elanlar
show(ui.section("elanlar", "3 · Real elanlar", "Büdcənə uyğun mənzillər",
                   "bina.az-dakı real elanlar. «Aç ↗» linki elanı bina.az-da açır. Əlaqə məlumatları saytda saxlanılmır."))
with st.container(key="listings"):
    seg = core.segment(data.listings, params)
    fit = seg[seg["price_azn"] <= params.budget]
    a, b = st.columns([1, 1])
    with a:
        dopts = ["Bütün rayonlar"] + sorted(fit["district_name"].unique().tolist() if len(fit) else seg["district_name"].unique().tolist())
        dsel = st.selectbox("Rayon", dopts, key="ldist")
    with b:
        sort = st.segmented_control("Sıralama", ["Ən sərfəli (1 m²)", "Ən ucuz", "Ən geniş"], default="Ən sərfəli (1 m²)", key="lsort") or "Ən sərfəli (1 m²)"
    rows = fit if len(fit) else seg
    if not len(fit):
        st.warning(f"Büdcənə ({ui.az(params.budget)} AZN) uyğun elan tapılmadı. Aşağıda bu filtrlərdə ən ucuz elanlar göstərilir.")
    if dsel != "Bütün rayonlar":
        rows = rows[rows["district_name"] == dsel]
    key = {"Ən sərfəli (1 m²)": ["price_per_m2", True], "Ən ucuz": ["price_azn", True], "Ən geniş": ["area_m2", False]}[sort]
    rows = rows.sort_values(key[0], ascending=key[1]).head(300)
    table = rows.rename(columns={"district_name": "Rayon", "location_name": "Məkan", "rooms": "Otaq", "area_m2": "Sahə, m²",
                                 "floor": "Mərtəbə", "price_azn": "Kirayə, AZN", "price_per_m2": "1 m², AZN",
                                 "building_type": "Tikili", "url": "Elan"})
    table["Elanı verən"] = rows["is_agency"].map({"Y": "Vasitəçi", "N": "Sahibi"})
    table = table[["Rayon", "Məkan", "Otaq", "Sahə, m²", "Mərtəbə", "Kirayə, AZN", "1 m², AZN", "Tikili", "Elanı verən", "Elan"]]
    st.dataframe(table, hide_index=True, width="stretch", height=430, column_config={
        "Elan": st.column_config.LinkColumn("Elan", display_text="Aç ↗"),
        "Kirayə, AZN": st.column_config.NumberColumn(format="%d AZN"),
        "1 m², AZN": st.column_config.NumberColumn(format="%.1f"),
        "Sahə, m²": st.column_config.NumberColumn(format="%d"),
        "Mərtəbə": st.column_config.NumberColumn(format="%d"),
    })
    st.caption(f"Göstərilir: {ui.az(len(table))} elan (maksimum 300) · cəmi uyğun: {ui.az(len(fit))}")

# ------------------------------------------------------------------ 4 · AI məsləhətçi
show(ui.section("ai", "4 · Süni intellekt", "AI məsləhətçi",
                   "Gemini sənin rəqəmlərini oxuyur və sadə dillə izah edir: vəziyyət necədir və nə etmək olar."))
ctx = ai.context(res, facts)
cache = st.session_state.setdefault("ai_cache", {})
with st.container(key="ai"):
    show(ui.ai_header())
    if not ai.available():
        st.caption("AI açarı qoşulmayıb — aşağıda avtomatik izah göstərilir.")
    go = st.button("✨ Vəziyyətimi izah et", type="primary", key="explain")
    box = st.container()
    k = ("explain", ctx)
    if go and k not in cache:
        with box:
            try:
                with st.spinner("Gemini düşünür… (adətən 10–20 saniyə)"):
                    cache[k] = st.write_stream(ai.stream(ai.EXPLAIN.format(ctx=ctx)))
            except Exception:
                cache[k] = ai.fallback(res)
                st.markdown(cache[k])
                st.caption("AI hazırda cavab vermədi — avtomatik izah göstərildi.")
    elif k in cache:
        with box:
            st.markdown(cache[k])

    show('<div style="height:6px"></div>')
    hist = st.session_state.setdefault("chat", [])
    sugg = st.pills("Hazır suallar", ["Hansı rayonu seçim?", "Vasitəçisiz elan niyə ucuzdur?",
                                       "2 nəfər bölsək nə dəyişir?", "Maaşım nə qədər olmalıdır?"],
                    key=f"sugg{len(hist)}")
    q = st.chat_input("Sualını yaz… (məs. «Yasamalda 2 otaqlı tapa bilərəmmi?»)", key="ask")
    q = q or sugg
    for role, msg in hist:
        with st.chat_message(role, avatar="🧑" if role == "user" else "✨"):
            st.markdown(msg)
    if q:
        with st.chat_message("user", avatar="🧑"):
            st.markdown(q)
        with st.chat_message("assistant", avatar="✨"):
            try:
                with st.spinner("Gemini düşünür…"):
                    ans = st.write_stream(ai.stream(ai.ASK.format(q=q, ctx=ctx)))
            except Exception:
                ans = "AI hazırda əlçatan deyil. Yuxarıdakı kalkulyator və rayonlar bölməsi sualına cavab verir."
                st.markdown(ans)
        hist += [("user", q), ("assistant", ans)]
        st.rerun()

# ------------------------------------------------------------------ 5 · bazar
show(ui.section("bazar", "5 · Bazar", "Bazar bir baxışda",
                   "Bakıda kirayə qiymətini nə müəyyən edir və kimin maaşı kirayəyə çatır — bütün elanlar üzrə."))
show(ui.insight_cards(facts, core.sector_afford(data, "1", 1)))
show(ui.feedback(FEEDBACK_FORM))
show(ui.footer(facts, data.captured_at, data.rows_raw))
