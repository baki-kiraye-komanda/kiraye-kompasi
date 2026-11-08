"""
ai.py — Gemini (Google Generative AI) ilə nəticənin sadə dildə izahı.

Açar haradan götürülür (birincisi tapılan):
  1) Streamlit Cloud: Settings → Secrets → GEMINI_API_KEY
  2) Lokal kompüter: layihə qovluğundakı .env faylı (GEMINI_API_KEY=...)
Açar heç vaxt ekrana və ya loga yazılmır.

Model əlçatan olmasa, növbəti model sınanır; heç biri işləməsə, sayt AI-sız,
qaydalara əsaslanan qısa izah göstərir (sayt heç vaxt «sınmır»).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator

FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite"]  # 08.11.2026 yoxlanılıb: 3.5-flash ~2 san.
RETIRED = ("gemini-2.5", "gemini-2.0", "gemini-1.5")  # artıq yeni istifadəçilər üçün yoxdur (404)

SYSTEM = """Sən «Kirayə Kompası» saytının məsləhətçisisən: Bakıda kirayə mənzil axtaran insanlara kömək edirsən.
QAYDALAR:
- Yalnız sənə verilən JSON-dakı rəqəmlərdən istifadə et. Rəqəm, rayon, elan və ya qiymət UYDURMA.
- Məlumatda olmayan şeyi soruşsalar, düzünü de: «bu barədə məlumatımız yoxdur».
- Azərbaycan dilində, sadə və səmimi yaz; texniki termin işlətsən, mötərizədə izah et.
- Qısa ol. Markdown istifadə et (qalın, qısa siyahı). Başlıqlar üçün ### işlət.
- Pul məbləğlərini «850 AZN» kimi, faizləri tam ədədlə («61%») yaz.
- Hüquqi və ya investisiya məsləhəti vermə.
Kontekst: «kirayə yükü» = median kirayə ÷ aylıq gəlir; beynəlxalq praktikada 30%-ə qədər normal sayılır.
Məlumat bina.az-dakı aylıq kirayə elanlarından (təkrar və qeyri-adi elanlar çıxarılıb) və Dövlət Statistika Komitəsinin maaş məlumatından gəlir.
Elan qiyməti — istənilən qiymətdir, real razılaşma bir az fərqli ola bilər."""

EXPLAIN = """İstifadəçinin vəziyyətini izah et. Struktur:
### Qısa hökm
1–2 cümlə: büdcəsi nə qədərdir, elanların neçə faizi uyğundur, kirayə yükü normaya sığırmı.
### Nə etmək olar
3 konkret addım — rayon adları və məbləğlərlə (JSON-dakı «districts» və «savings_path»-dan).
### Bir qeyd
1 cümlə: diqqət ediləcək məqam.
Cəmi 120–170 söz.

MƏLUMAT (JSON):
{ctx}"""

ASK = """İstifadəçinin sualı: «{q}»
Yalnız aşağıdakı məlumata əsaslanaraq qısa cavab ver (maksimum 120 söz).

MƏLUMAT (JSON):
{ctx}"""


def _key() -> str | None:
    try:
        import streamlit as st
        k = st.secrets.get("GEMINI_API_KEY")
        if k:
            return str(k)
    except Exception:
        pass
    if not os.getenv("GEMINI_API_KEY"):
        try:
            from dotenv import load_dotenv
            root = Path(__file__).resolve().parents[1]
            for name in (".env", ".env.txt"):
                if (root / name).exists():
                    load_dotenv(root / name, override=False)
                    break
        except Exception:
            pass
    k = os.getenv("GEMINI_API_KEY", "").strip()
    return k if k and not k.startswith("BURAYA") else None


def available() -> bool:
    return _key() is not None


def _models() -> list[str]:
    first = None
    try:
        import streamlit as st
        first = st.secrets.get("GEMINI_MODEL")
    except Exception:
        pass
    first = first or os.getenv("GEMINI_MODEL")
    out = [first] if first and not str(first).startswith(RETIRED) else []
    return out + [m for m in FALLBACK_MODELS if m != first]


def stream(prompt: str) -> Iterator[str]:
    """Gemini cavabını hissə-hissə qaytarır. Uğursuz olsa RuntimeError."""
    key = _key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY tapılmadı")
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=25_000))  # 25 san.-dən çox gözləmə
    base = dict(system_instruction=SYSTEM, temperature=0.4, max_output_tokens=4096)
    try:  # modelin «düşüncə» mətni cavaba qarışmasın
        cfg = types.GenerateContentConfig(**base, thinking_config=types.ThinkingConfig(include_thoughts=False))
    except Exception:
        cfg = types.GenerateContentConfig(**base)
    last = None
    for model in _models():
        try:
            got = False
            for chunk in client.models.generate_content_stream(model=model, contents=prompt, config=cfg):
                for t in _texts(chunk):
                    got = True
                    yield t
            if got:
                return
        except Exception as e:  # model yoxdur / limit / şəbəkə — növbəti modeli sına
            last = e
            msg = str(e)
            if "API key" in msg or "PERMISSION_DENIED" in msg:
                break
    raise RuntimeError(f"Gemini cavab vermədi: {type(last).__name__ if last else 'boş cavab'}")


def _texts(chunk):
    """Yalnız cavab mətnini qaytarır; «thought» (modelin daxili düşüncəsi) hissələri atılır."""
    try:
        for cand in chunk.candidates or []:
            for part in (cand.content.parts or []) if cand.content else []:
                if getattr(part, "text", None) and not getattr(part, "thought", False):
                    yield part.text
    except Exception:
        t = getattr(chunk, "text", None)
        if t:
            yield t


def context(r, f: dict) -> str:
    """AI-a veriləcək məlumat: yalnız hesablanmış rəqəmlər (şəxsi məlumat yoxdur)."""
    p = r.p
    d = r.districts.head(8)
    ctx = {
        "user": {"monthly_salary_per_person_azn": round(p.salary), "share_for_rent": p.share, "people_sharing": p.people,
                 "rooms": p.rooms, "building_type": p.btype, "area": p.area, "owner_only": p.owner_only},
        "budget_azn": round(p.budget),
        "listings_in_filter": r.seg_n, "listings_within_budget": r.fit_n, "share_within_budget_pct": round(r.fit_share * 100),
        "median_rent_azn": r.median, "p25_p75_azn": [r.p25, r.p75],
        "rent_burden_pct": round(r.burden * 100) if r.burden == r.burden else None,
        "salary_needed_for_30pct_per_person_azn": round(r.need_salary) if r.need_salary == r.need_salary else None,
        "verdict": r.verdict[0],
        "districts": [{"name": x.district_name, "listings": int(x.n), "within_budget": int(x.fit),
                       "share_pct": round(float(x.share) * 100), "median_azn": round(float(x.median))} for x in d.itertuples()],
        "savings_path": [{"step": s, "median_azn": round(v)} for s, v in r.savings],
        "market": {"baku_avg_salary_azn": f["baku_salary"], "salary_year": f["salary_year"],
                   "median_2_rooms_baku_city": f["median_2_city"], "agency_median": f["agency"], "owner_median": f["owner"],
                   "new_building_median": f["new"], "old_building_median": f["old"], "rooms_median": f["rooms"]},
    }
    return json.dumps(ctx, ensure_ascii=False)


def fallback(r) -> str:
    """AI əlçatan olmayanda: eyni rəqəmlərlə qısa, qaydaya əsaslanan izah."""
    from ui import az, pct
    p = r.p
    lines = [f"### Qısa hökm",
             f"Büdcən **{az(p.budget)} AZN**-dir. Seçdiyin filtrlərlə **{az(r.seg_n)}** elandan **{az(r.fit_n)}**-i "
             f"(**{pct(r.fit_share)}**) bu büdcəyə uyğundur. Median kirayə **{az(r.median)} AZN** — gəlirin **{pct(r.burden)}**-i "
             f"({'normaya sığır' if r.burden <= .3 else 'norma 30%-dən çoxdur'}).",
             "### Nə etmək olar"]
    top = r.districts.head(3)
    if len(top):
        lines.append("- Ən əlçatan rayonlar: " + ", ".join(f"**{x.district_name}** ({pct(x.share)})" for x in top.itertuples()) + ".")
    if len(r.savings) >= 2:
        lines.append(f"- Ucuz rayon + köhnə tikili + sahibindən elan seçsən, median **{az(r.savings[0][1])}** → **{az(r.savings[-2][1])} AZN** olur.")
        lines.append(f"- Kirayəni bölüşmək ən güclü addımdır: adambaşına təxminən **{az(r.savings[-1][1])} AZN**.")
    lines += ["### Bir qeyd", "Elan qiyməti istənilən qiymətdir — sahibi ilə danışıqda bir az endirim mümkündür."]
    return "\n".join(lines)
