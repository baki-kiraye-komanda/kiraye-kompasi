"""
make_report.py — Power BI hesabatını (PBIR formatı) koddan yaradır.

Nə edir: layout.py-dakı koordinatlarla hər səhifəni, fon şəklini, temanı, naviqasiya
düymələrini, kartları, qrafikləri, slicer-ləri və cədvəlləri JSON fayllar kimi yazır.
Niyə kodla: dizayn dəqiq və təkrar oluna bilən olur; bir dəyişiklik (rəng, ölçü)
bütün səhifələrə eyni anda tətbiq edilir.
Nəticə: powerbi/BakuKiraye.Report/definition/... və StaticResources/RegisteredResources/...
"""
import json
import shutil
import sys
from pathlib import Path

from layout import C, NAV, PAGES, nav_rect

HERE = Path(__file__).resolve().parent
REPORT = HERE.parent / "powerbi" / "BakuKiraye.Report"
DEF = REPORT / "definition"
RES = REPORT / "StaticResources" / "RegisteredResources"
M = "Ölçülər"
VC_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
HOME_FOLDER = "34f92686e8eb5293919d"   # Power BI-ın yaratdığı ilk səhifə qovluğu (ana səhifə kimi istifadə olunur)
# tooltip və drill-through səhifələri Power BI Desktop-da yaradılıb (qovluq adları onundur), məzmunu bu skript yazır
TOOLTIP_FOLDER, LISTINGS_FOLDER = "9a5cbde2a2708060d800", "d324fa85b2010c802001"
PAGE_FOLDER = {"home": HOME_FOLDER, "market": "market", "budget": "budget", "salary": "salary", "method": "method",
               "tooltip": TOOLTIP_FOLDER, "listings": LISTINGS_FOLDER}
DISPLAY = {"home": "Ana səhifə", "market": "Bazar", "budget": "Büdcəm", "salary": "Maaş", "method": "Metodologiya",
           "tooltip": "Rayon tooltip", "listings": "Elanlar"}
# Büdcəm səhifəsindəki hazır ssenarilər (bookmark-lar Power BI-da yaradılıb: definition/bookmarks/)
SCENARIOS = [("1ba8c28e322728156960", "Standart: 700 AZN, 1 nəfər"), ("ed559dca16e078d243e6", "Tələbə: 350 AZN, 2 nəfər, 2 otaq"),
             ("f89d4691618690bc0617", "Gənc mütəxəssis: 700 AZN, 1 otaq"), ("f9c0192e04b24818d899", "Ailə: 1200 AZN, 3 otaq")]


def rayon_binding(page_type, filter_name, binding_name, param_name):
    """Drill-through / tooltip səhifəsinin Rayon sahəsinə bağlanması (Power BI-ın yazdığı formatda)."""
    fld = {"Column": {"Expression": {"SourceRef": {"Entity": "Rayon"}}, "Property": "Rayon"}}
    return {
        "filterConfig": {"filters": [{"name": filter_name, "field": fld, "type": "Categorical", "howCreated": "Drillthrough"}]},
        "pageBinding": {"name": binding_name, "type": page_type, "parameters": [{
            "name": param_name, "boundFilter": filter_name, "asAggregation": False,
            "qnaSingleSelectRequired": False, "fieldExpr": fld}]},
        "type": page_type,
    }


SPECIAL = {
    "tooltip": {"size": (480, 320), "display": "ActualSize", "hidden": True,  # oxu rejimində tab kimi görünməsin
                "extra": rayon_binding("Tooltip", "7b6c89d074905ea266e1", "a1ceae0c23ab7032b074", "7ad7566d5035d15d3729")},
    "listings": {"size": (1920, 1080), "display": "FitToPage",
                 "extra": rayon_binding("Drillthrough", "de6646891172a04c4e11", "1eef5f29845320d5404c", "6bb74fdf723d95105d67")},
}


# ---------- JSON köməkçiləri ----------
def lit(v):
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, (int, float)):
        s = f"{v}D"
    else:
        s = "'" + str(v).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": s}}}


def color(hex_):
    return {"solid": {"color": lit(hex_)}}


def measure(name, table=M):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def column(table, name):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def agg(table, name, fn=1):  # 0 Sum, 1 Avg, 3 Min, 4 Max
    return {"Aggregation": {"Expression": column(table, name), "Function": fn}}


def proj(field, ref, native=None):
    return {"field": field, "queryRef": ref, "nativeQueryRef": native or ref.split(".", 1)[-1]}


def pm(name):
    return proj(measure(name), f"{M}.{name}", name)


def pc(table, name):
    return proj(column(table, name), f"{table}.{name}", name)


def measure_color(name):
    return {"solid": {"color": {"expr": measure(name)}}}


WILDCARD = {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}


def container(name, x, y, w, h, visual, z=1000, tab=0, extra=None):
    v = {"$schema": VC_SCHEMA, "name": name,
         "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": tab}, "visual": visual}
    if extra:
        v.update(extra)
    return v


NO_CHROME = {
    "background": [{"properties": {"show": lit(False)}}],
    "border": [{"properties": {"show": lit(False)}}],
    "title": [{"properties": {"show": lit(False)}}],
    "dropShadow": [{"properties": {"show": lit(False)}}],
    "visualHeader": [{"properties": {"show": lit(False)}}],
}


# ---------- vizual növləri ----------
def card(name, rect, measure_name, size=36, col=None, show_label=False, label_col=None, wrap=False, font="Segoe UI Semibold", align=None):
    x, y, w, h = rect
    objects = {
        "labels": [{"properties": {"color": color(col or C["text"]), "fontSize": lit(size), "fontFamily": lit(font),
                                   "labelDisplayUnits": lit(1)}}],
        "categoryLabels": [{"properties": {"show": lit(show_label), "color": color(label_col or C["muted"]), "fontSize": lit(12)}}],
    }
    if wrap:
        objects["wordWrap"] = [{"properties": {"show": lit(True)}}]
    visual = {"visualType": "card", "query": {"queryState": {"Values": {"projections": [pm(measure_name)]}}},
              "objects": objects, "visualContainerObjects": NO_CHROME, "drillFilterOtherVisuals": True}
    return container(name, x, y, w, h, visual)


def bar(name, rect, cat_field, value_measure, color_measure=None, label_fmt_size=12, sort_desc=True, tooltips=None):
    x, y, w, h = rect
    cat = pc(*cat_field)
    qs = {"Category": {"projections": [cat]}, "Y": {"projections": [pm(value_measure)]}}
    if tooltips:
        qs["Tooltips"] = {"projections": [pm(t) for t in tooltips]}
    objects = {
        "labels": [{"properties": {"show": lit(True), "color": color(C["text"]), "fontSize": lit(label_fmt_size)}}],
        "categoryAxis": [{"properties": {"show": lit(True), "labelColor": color("#C9D3EE"), "fontSize": lit(13),
                                         "showAxisTitle": lit(False)}}],
        "valueAxis": [{"properties": {"show": lit(False), "gridlineShow": lit(False)}}],
        "legend": [{"properties": {"show": lit(False)}}],
    }
    if color_measure:
        objects["dataPoint"] = [{"properties": {"fill": measure_color(color_measure)}, "selector": WILDCARD}]
    visual = {"visualType": "barChart",
              "query": {"queryState": qs,
                        "sortDefinition": {"sort": [{"field": measure(value_measure),
                                                     "direction": "Descending" if sort_desc else "Ascending"}]}},
              "objects": objects, "visualContainerObjects": NO_CHROME, "drillFilterOtherVisuals": True}
    return container(name, x, y, w, h, visual)


def multi_bar(name, rect, measures_colors):
    x, y, w, h = rect
    qs = {"Y": {"projections": [pm(m_) for m_, _ in measures_colors]}}
    objects = {
        "labels": [{"properties": {"show": lit(True), "color": color(C["text"]), "fontSize": lit(16)}}],
        "categoryAxis": [{"properties": {"show": lit(False)}}],
        "valueAxis": [{"properties": {"show": lit(False), "gridlineShow": lit(False)}}],
        "legend": [{"properties": {"show": lit(True), "position": lit("Bottom"), "labelColor": color(C["muted"]), "fontSize": lit(12)}}],
        "dataPoint": [{"properties": {"fill": color(col)}, "selector": {"metadata": f"{M}.{m_}"}} for m_, col in measures_colors],
    }
    visual = {"visualType": "clusteredBarChart", "query": {"queryState": qs}, "objects": objects,
              "visualContainerObjects": NO_CHROME, "drillFilterOtherVisuals": True}
    return container(name, x, y, w, h, visual)


def scatter(name, rect):
    x, y, w, h = rect
    qs = {"Category": {"projections": [pc("Rayon", "Rayon")]},
          "X": {"projections": [pm("X koordinat")]},
          "Y": {"projections": [pm("Y koordinat")]},
          "Size": {"projections": [pm("Elan sayı")]},
          "Tooltips": {"projections": [pm("Median kirayə"), pm("Qiymət aralığı"), pm("Median 1 m²")]}}
    objects = {
        "categoryLabels": [{"properties": {"show": lit(True), "color": color(C["text"]), "fontSize": lit(13)}}],
        "dataPoint": [{"properties": {"fill": measure_color("Median rəngi")}, "selector": WILDCARD}],
        "categoryAxis": [{"properties": {"show": lit(False), "gridlineShow": lit(False), "showAxisTitle": lit(False)}}],
        "valueAxis": [{"properties": {"show": lit(False), "gridlineShow": lit(False), "showAxisTitle": lit(False)}}],
        "bubbles": [{"properties": {"bubbleSize": lit(-12)}}],
        "legend": [{"properties": {"show": lit(False)}}],
    }
    visual = {"visualType": "scatterChart", "query": {"queryState": qs}, "objects": objects,
              "visualContainerObjects": NO_CHROME, "drillFilterOtherVisuals": True}
    return container(name, x, y, w, h, visual)


def slicer(name, rect, field, mode="Dropdown", title=None, single=False, horizontal=False, start=None):
    x, y, w, h = rect
    objects = {
        "data": [{"properties": {"mode": lit(mode)}}],
        "header": [{"properties": {"show": lit(bool(title)), "fontColor": color(C["muted"]), "textSize": lit(11)}}],
        "items": [{"properties": {"fontColor": color(C["text"]), "background": color("#14214A"), "textSize": lit(13)}}],
    }
    if single:
        objects["selection"] = [{"properties": {"singleSelect": lit(True), "strictSingleSelect": lit(True)}}]
    if horizontal:
        objects["general"] = [{"properties": {"orientation": lit(1)}}]
    if start is not None:  # what-if slayderin ilkin dəyəri (Power BI-ın özünün saxladığı formatda)
        objects["data"][0]["properties"]["numericStart"] = lit(start)
        objects["general"] = [{"properties": {"filter": {"filter": {
            "Version": 2, "From": [{"Name": "b", "Entity": field[0], "Type": 0}],
            "Where": [{"Condition": {"Comparison": {"ComparisonKind": 0,
                                                    "Left": {"Column": {"Expression": {"SourceRef": {"Source": "b"}}, "Property": field[1]}},
                                                    "Right": {"Literal": {"Value": f"{start}D"}}}}}]}}}}]
    vco = dict(NO_CHROME)
    if title:
        vco = {**NO_CHROME}
        objects["header"][0]["properties"]["text"] = lit(title)
    visual = {"visualType": "slicer", "query": {"queryState": {"Values": {"projections": [pc(*field)]}}},
              "objects": objects, "visualContainerObjects": vco, "drillFilterOtherVisuals": True}
    return container(name, x, y, w, h, visual)


def table(name, rect, fields, names=None, sort=None, url_icon=False, color_diff=True, text_size=12):
    x, y, w, h = rect
    projs = []
    for i, f in enumerate(fields):
        p_ = pc(*f) if isinstance(f, tuple) else pm(f)
        if names:
            p_["displayName"] = names[i]
        projs.append(p_)
    objects = {
        "grid": [{"properties": {"gridVertical": lit(False), "gridHorizontal": lit(True),
                                 "gridHorizontalColor": color("#22305A"), "rowPadding": lit(6), "textSize": lit(text_size)}}],
        "columnHeaders": [{"properties": {"fontColor": color(C["muted"]), "backColor": color("#0D1735"), "fontSize": lit(text_size - 1)}}],
        "values": [{"properties": {"fontColorPrimary": color(C["text"]), "backColorPrimary": color("#0E1938"),
                                   "fontColorSecondary": color(C["text"]), "backColorSecondary": color("#111E42"),
                                   "urlIcon": lit(url_icon)}}],
        "total": [{"properties": {"totals": lit(False)}}],
    }
    if color_diff:
        objects["values"].append({"properties": {"fontColor": measure_color("Fərq rəngi")},
                                  "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"{M}.Büdcə fərqi"}})
    query = {"queryState": {"Values": {"projections": projs}}}
    if sort:
        query["sortDefinition"] = {"sort": [{"field": column(*sort), "direction": "Ascending"}]}
    visual = {"visualType": "tableEx", "query": query,
              "objects": objects, "visualContainerObjects": NO_CHROME, "drillFilterOtherVisuals": True}
    return container(name, x, y, w, h, visual)


def nav_button(name, rect, target, tip, z=3000, link=None):
    x, y, w, h = rect
    visual = {
        "visualType": "actionButton",
        "objects": {
            "icon": [{"properties": {"shapeType": lit("blank")}, "selector": {"id": "default"}}],
            "text": [{"properties": {"show": lit(False)}, "selector": {"id": "default"}}],
            "outline": [{"properties": {"show": lit(False)}, "selector": {"id": "default"}}],
            "fill": [{"properties": {"show": lit(True), "fillColor": color(C["teal"]), "transparency": lit(100)},
                      "selector": {"id": "default"}},
                     {"properties": {"show": lit(True), "fillColor": color(C["teal"]), "transparency": lit(88)},
                      "selector": {"id": "hover"}},
                     {"properties": {"show": lit(True), "fillColor": color(C["teal"]), "transparency": lit(80)},
                      "selector": {"id": "selected"}}],
            "shape": [{"properties": {"tileShape": lit("rectangleRounded"), "roundEdge": lit(18)}}],
        },
        "visualContainerObjects": {
            **NO_CHROME,
            "visualLink": [{"properties": link or {"show": lit(True), "type": lit("PageNavigation"),
                                                   "navigationSection": lit(PAGE_FOLDER[target]), "tooltip": lit(tip)}}],
        },
        "drillFilterOtherVisuals": True,
    }
    return container(name, x, y, w, h, visual, z=z)


# ---------- səhifələr ----------
def inner(rect, top=64, pad=16, bottom=12):
    x, y, w, h = rect
    return (x + pad, y + top, w - 2 * pad, h - top - bottom)


def common(key):
    vis = []
    for i, (k, lab, _) in enumerate(NAV):
        vis.append(nav_button(f"nav_{key}_{k}", nav_rect(i), k, DISPLAY[k]))
    vis.append(card(f"src_{key}", (1100, 100, 796, 34), "Mənbə qeydi", 11, C["dim"], font="Segoe UI"))
    return vis


def image(name, rect, measure_name):
    """Standart Image vizualı: şəkil DAX ölçüsündən gəlir (animasiyalı SVG, Vizual cədvəli)."""
    x, y, w, h = rect
    vco = {**NO_CHROME, "padding": [{"properties": {"top": lit(0), "right": lit(0), "bottom": lit(0), "left": lit(0)}}]}
    visual = {"visualType": "image",
              "objects": {"image": [{"properties": {"sourceType": lit("imageData"),
                                                    "sourceField": {"expr": measure(measure_name, "Vizual")}}}]},
              "visualContainerObjects": vco, "drillFilterOtherVisuals": True}
    return container(name, x, y, w, h, visual, z=500)


def stub(name):
    """Köhnə vizualın yerinə gizli boş forma (cihazdakı köhnə faylı silmək mümkün olmadığı üçün)."""
    return {"$schema": VC_SCHEMA, "name": name, "position": {"x": 0, "y": 0, "z": 0, "height": 1, "width": 1, "tabOrder": 9999},
            "visual": {"visualType": "shape", "drillFilterOtherVisuals": True}, "isHidden": True}


def page_home():
    c = PAGES["home"]["cards"]
    v = [image("home_ticker", c["ticker"], "VZ Ticker"),
         image("home_hero", c["hero_img"], "VZ Hero"),
         image("home_kpi0", c["kpi0"], "VZ KPI Elan"),
         image("home_kpi1", c["kpi1"], "VZ KPI Median"),
         image("home_kpi2", c["kpi2"], "VZ KPI Maaş"),
         image("home_tiles", c["tiles_img"], "VZ Plitələr")]
    for i, t in enumerate(["market", "budget", "salary", "method"]):
        v.append(nav_button(f"home_tile{i}", c[f"tile{i}"], t, DISPLAY[t], z=2500))
    return v


def page_market():
    c = PAGES["market"]["cards"]
    v = [image(f"mk_kpi{i}", c[f"kpi{i}"], m) for i, m in
         enumerate(["VZ MK Elan", "VZ MK Median", "VZ MK M2", "VZ MK Tikili", "VZ MK Vasitəçi"])]
    v.append(scatter("mk_map", inner(c["map"], top=72, pad=16, bottom=12)))
    v.append(image("mk_range", c["range_img"], "VZ Rayon aralığı"))
    v.append(image("mk_drivers", c["drivers_img"], "VZ Amillər"))
    fx, fy, fw, fh = c["filters"]
    sl = [(("Elanlar", "Otaq"), "Otaq sayı"), (("Elanlar", "Tikili növü"), "Tikili növü"),
          (("Rayon", "Ərazi"), "Ərazi"), (("Elanlar", "Elanı verən"), "Elanı verən")]
    sw = (fw - 260 - 3 * 20) // 4
    for i, (field, title) in enumerate(sl):
        v.append(slicer(f"mk_sl{i}", (fx + 240 + i * (sw + 20), fy + 6, sw, fh - 12), field, "Dropdown", title))
    return v


def page_budget():
    c = PAGES["budget"]["cards"]
    v = [
        slicer("bd_budget", c["ctl_budget"], ("Büdcə", "Büdcə (AZN)"), "Single", start=700),
        slicer("bd_people", c["ctl_people"], ("Nəfər", "Nəfər sayı"), "Basic", single=True, horizontal=True),
        slicer("bd_rooms", c["ctl_rooms"], ("Elanlar", "Otaq"), "Dropdown"),
        slicer("bd_type", c["ctl_type"], ("Elanlar", "Tikili növü"), "Dropdown"),
        image("bd_headline", c["headline_img"], "VZ Büdcə"),
        bar("bd_bars", inner(c["bars"], top=100, pad=16, bottom=16), ("Rayon", "Rayon"), "Büdcəyə uyğun pay (30+)",
            "Büdcə rəngi", tooltips=["Büdcəyə uyğun elan", "Elan sayı", "Adambaşına median", "Büdcə fərqi"]),
        image("bd_savings", c["savings_img"], "VZ Qənaət"),
    ]
    for i, (bm, tip) in enumerate(SCENARIOS):  # bookmark düymələri (mətn fon şəklindədir)
        v.append(nav_button(f"bd_scn{i}", c[f"scn{i}"], None, tip, z=3500,
                            link={"show": lit(True), "type": lit("Bookmark"), "bookmark": lit(bm), "tooltip": lit(tip)}))
    return v


def page_salary():
    c = PAGES["salary"]["cards"]
    v = [image(f"sl_kpi{i}", c[f"kpi{i}"], m) for i, m in enumerate(["VZ SL Maaş", "VZ SL Yük", "VZ SL Lazım"])]
    v.append(bar("sl_bars", inner(c["bars"], top=80, pad=16, bottom=16), ("Maaş", "Sahə"), "Kirayə yükü", "Yük rəngi",
                 tooltips=["Orta maaş", "Kirayədən sonra qalan"]))
    v.append(slicer("sl_rooms", c["side_rooms"], ("Elanlar", "Otaq"), "Dropdown"))
    v.append(slicer("sl_people", c["side_people"], ("Nəfər", "Nəfər sayı"), "Basic", single=True, horizontal=True))
    v.append(image("sl_afford", c["afford_img"], "VZ Əlçatanlıq"))
    return v


def page_method():
    c = PAGES["method"]["cards"]
    return [image("mt_funnel", c["funnel_img"], "VZ Huni"), image("mt_valid", c["valid_img"], "VZ Yoxlama")]


def page_tooltip():
    # 480 x 320 hover-kartı: Rayon sahəsi olan vizualın üzərinə gələndə avtomatik açılır
    return [image("tt_card", (0, 0, 480, 320), "VZ Tooltip")]


def page_listings():
    c = PAGES["listings"]["cards"]
    v = [image("ls_head", c["head"], "VZ Elanlar başlıq")]
    v.append(table("ls_table", inner(c["table"], top=86, pad=16, bottom=16),
                   [("Elanlar", "Məkan"), ("Elanlar", "Otaq"), ("Elanlar", "Sahə (m²)"), ("Elanlar", "Mərtəbə"),
                    ("Elanlar", "Kirayə (AZN/ay)"), ("Elanlar", "1 m² qiyməti (AZN)"), ("Elanlar", "Tikili növü"),
                    ("Elanlar", "Elanı verən"), ("Elanlar", "Link")],
                   ["Məkan", "Otaq", "Sahə, m²", "Mərtəbə", "Kirayə, AZN", "1 m², AZN", "Tikili", "Elanı verən", "Link"],
                   sort=("Elanlar", "Kirayə (AZN/ay)"), url_icon=True, color_diff=False, text_size=15))
    v.append(slicer("ls_rooms", c["side_rooms"], ("Elanlar", "Otaq"), "Dropdown"))
    v.append(slicer("ls_type", c["side_type"], ("Elanlar", "Tikili növü"), "Dropdown"))
    v.append(slicer("ls_agent", c["side_agent"], ("Elanlar", "Elanı verən"), "Dropdown"))
    # "Geri" düyməsi: Power BI-ın yaratdığı vizualın adı saxlanılır (köhnə fayl üzərinə yazılsın)
    v.append(nav_button("f78d2c2737c0986b408a", c["back"], None, "Əvvəlki səhifəyə qayıt", z=3500,
                        link={"show": lit(True), "type": lit("Back"), "tooltip": lit("Əvvəlki səhifəyə qayıt")}))
    return v


BUILDERS = {"home": page_home, "market": page_market, "budget": page_budget, "salary": page_salary, "method": page_method,
            "tooltip": page_tooltip, "listings": page_listings}


def page_json(key):
    folder = PAGE_FOLDER[key]
    sp = SPECIAL.get(key, {})
    w, h = sp.get("size", (1920, 1080))
    page = {
        "$schema": PAGE_SCHEMA, "name": folder, "displayName": DISPLAY[key], "displayOption": sp.get("display", "FitToPage"),
        **({"visibility": "HiddenInViewMode"} if sp.get("hidden") else {}),
        "height": h, "width": w,
        "objects": {
            "background": [{"properties": {
                "image": {"image": {"name": lit(f"bg_{key}.png"),
                                    "url": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources",
                                                                             "PackageType": 1, "ItemName": f"bg_{key}.png"}}},
                                    "scaling": lit("Fit")}},
                "transparency": lit(0)}}],
            "outspace": [{"properties": {"color": color(C["bg0"])}}],
        },
    }
    page.update(sp.get("extra", {}))
    return page


THEME = {
    "name": "Baku Kiraye Dark",
    "dataColors": [C["cyan"], C["magenta"], C["violet"], C["amber"], C["teal"], C["blue"], C["coral"], "#94A3B8"],
    "foreground": C["text"], "foregroundNeutralSecondary": C["muted"], "foregroundNeutralTertiary": C["dim"],
    "background": C["bg1"], "backgroundLight": "#1A2366", "backgroundNeutral": "#232E7A",
    "tableAccent": C["cyan"], "good": C["teal"], "neutral": C["amber"], "bad": C["coral"],
    "maximum": C["coral"], "center": C["amber"], "minimum": C["teal"],
    "textClasses": {
        "callout": {"fontSize": 36, "fontFace": "Segoe UI Semibold", "color": C["text"]},
        "title": {"fontSize": 13, "fontFace": "Segoe UI Semibold", "color": C["muted"]},
        "header": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": C["text"]},
        "label": {"fontSize": 11, "fontFace": "Segoe UI", "color": "#C9D3EE"},
    },
    "visualStyles": {
        "*": {"*": {
            "background": [{"show": False, "transparency": 100}],
            "border": [{"show": False}],
            "dropShadow": [{"show": False}],
            "title": [{"show": False}],
            "visualHeader": [{"show": False}],
            "visualTooltip": [{"background": {"solid": {"color": "#0D1440"}},
                               "titleFontColor": {"solid": {"color": C["muted"]}},
                               "valueFontColor": {"solid": {"color": C["text"]}}}],
        }},
        "page": {"*": {"outspace": [{"color": {"solid": {"color": C["bg0"]}}}]}},
    },
}


def write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    pages_dir = DEF / "pages"
    # Yalnız bu skriptin yaratdığı 5 səhifə yenidən yazılır. Power BI-da əl ilə yaradılan
    # səhifələr (tooltip, drill-through) silinmir və sıranın sonunda saxlanılır.
    extra = sorted(p.name for p in pages_dir.iterdir()
                   if p.is_dir() and p.name not in PAGE_FOLDER.values()) if pages_dir.exists() else []
    order = []
    live = {}
    for key, build in BUILDERS.items():
        folder = PAGE_FOLDER[key]
        old = set()
        if (pages_dir / folder).exists():
            vd = pages_dir / folder / "visuals"
            old = {p.name for p in vd.iterdir()} if vd.exists() else set()
            shutil.rmtree(pages_dir / folder)
        order.append(folder)
        write(pages_dir / folder / "page.json", page_json(key))
        visuals = build() + (common(key) if key != "tooltip" else [])
        if key == "home":  # Power BI-ın yaratdığı test vizualını əvəz edirik (fayl adı eyni qalır)
            visuals[0]["name"] = "49a926be108db6581442"
        names = {v["name"] for v in visuals}
        visuals += [stub(n) for n in sorted(old - names)]  # köhnə vizuallar gizlədilir
        for v in visuals:
            write(pages_dir / folder / "visuals" / v["name"] / "visual.json", v)
        live[folder] = names
        print(f"{key:8} {len(visuals):3} vizual")
    # bookmark-larda artıq olmayan vizualların vəziyyəti çıxarılır
    for bf in (DEF / "bookmarks").glob("*.bookmark.json"):
        bm = json.loads(bf.read_text(encoding="utf-8"))
        for sec, st in bm.get("explorationState", {}).get("sections", {}).items():
            vc = st.get("visualContainers", {})
            for n in [n for n in vc if sec in live and n not in live[sec]]:
                del vc[n]
        write(bf, bm)
    write(pages_dir / "pages.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": order + extra, "activePageName": HOME_FOLDER})

    RES.mkdir(parents=True, exist_ok=True)
    items = []
    for key in BUILDERS:  # tooltip fonu make_backgrounds.py-da 480x320 ölçüdə çəkilir
        shutil.copy(HERE / "backgrounds" / f"bg_{key}.png", RES / f"bg_{key}.png")
        items.append({"name": f"bg_{key}.png", "path": f"bg_{key}.png", "type": "Image"})
    write(RES / "BakuKirayeTheme.json", THEME)
    items.append({"name": "BakuKirayeTheme.json", "path": "BakuKirayeTheme.json", "type": "CustomTheme"})

    report = json.loads((DEF / "report.json").read_text(encoding="utf-8"))
    report["themeCollection"]["customTheme"] = {
        "name": "BakuKirayeTheme.json",
        "reportVersionAtImport": report["themeCollection"]["baseTheme"]["reportVersionAtImport"],
        "type": "RegisteredResources"}
    report["resourcePackages"] = [p for p in report["resourcePackages"] if p["name"] != "RegisteredResources"]
    report["resourcePackages"].append({"name": "RegisteredResources", "type": "RegisteredResources", "items": items})
    write(DEF / "report.json", report)
    print("report.json yeniləndi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
