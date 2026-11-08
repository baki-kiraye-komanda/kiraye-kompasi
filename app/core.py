"""
core.py — saytın hesablama hissəsi (Streamlit-dən asılı deyil, ayrıca yoxlanıla bilər).

Məlumat: app/data/*.csv — Oracle view-larından export_data.py ilə çıxarılır.
Power BI də eyni faylları oxuyur, ona görə saytda və dashboard-da rəqəmlər eynidir.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
NORM = 0.30  # kirayə gəlirin 30%-dən çox olmamalıdır (beynəlxalq praktika)
MIN_N = 20   # rayon statistikası üçün minimum elan sayı (az elanla median etibarlı deyil)
TOTAL_ROW = "İqtisadiyyat üzrə - cəmi"
BAKU_ROW = "Bakı şəhəri - cəmi"


@dataclass
class Data:
    listings: pd.DataFrame
    districts: pd.DataFrame
    sectors: pd.DataFrame          # son il: sahə, orta maaş
    baku_salary: float
    country_salary: float
    salary_year: int
    captured_at: str
    rows_raw: int


def load(folder: Path = DATA) -> Data:
    l = pd.read_csv(folder / "listings.csv")
    l["rooms_group"] = l["rooms_group"].astype(str)
    l["area"] = l["is_baku_city"].map({"Y": "Bakı şəhəri", "N": "Bakı ətrafı"})
    d = pd.read_csv(folder / "district.csv")
    sal = pd.read_csv(folder / "salary.csv")
    yr = int(sal["year"].max())
    sec = (sal[(sal["year"] == yr) & (sal["sector_name"] != TOTAL_ROW)]
           .sort_values("avg_salary_azn", ascending=False)[["sector_name", "avg_salary_azn"]]
           .reset_index(drop=True))
    reg = pd.read_csv(folder / "salary_region.csv")
    ryr = int(reg["year"].max())
    baku = float(reg[(reg["year"] == ryr) & (reg["region_name"] == BAKU_ROW)]["avg_salary_azn"].iloc[0])
    country = float(sal[(sal["year"] == yr) & (sal["sector_name"] == TOTAL_ROW)]["avg_salary_azn"].iloc[0])
    snap = pd.read_csv(folder / "snapshot.csv").iloc[-1]
    return Data(l, d, sec, baku, country, ryr, str(snap["captured_at"]), int(snap["rows_raw"]))


@dataclass
class Params:
    salary: float = 1383.0       # bir nəfərin aylıq maaşı (AZN)
    share: float = 0.30          # maaşın kirayəyə ayrılan payı
    people: int = 1              # kirayəni bölən nəfər (hər biri təxminən eyni maaşla)
    rooms: str = "2"             # "Hamısı", "1".."4", "5+"
    btype: str = "Hamısı"        # "Hamısı", "Yeni tikili", "Köhnə tikili"
    area: str = "Hamısı"         # "Hamısı", "Bakı şəhəri", "Bakı ətrafı"
    owner_only: bool = False     # yalnız mülkiyyətçi (vasitəçisiz) elanlar

    @property
    def budget(self) -> float:
        """Mənzil üçün ümumi aylıq büdcə."""
        return self.salary * self.share * self.people

    @property
    def income(self) -> float:
        return self.salary * self.people


def segment(l: pd.DataFrame, p: Params, ignore=()) -> pd.DataFrame:
    m = pd.Series(True, index=l.index)
    if p.rooms != "Hamısı" and "rooms" not in ignore:
        m &= l["rooms_group"] == p.rooms
    if p.btype != "Hamısı" and "btype" not in ignore:
        m &= l["building_type"] == p.btype
    if p.area != "Hamısı" and "area" not in ignore:
        m &= l["area"] == p.area
    if p.owner_only and "owner" not in ignore:
        m &= l["is_agency"] == "N"
    return l[m]


def verdict(burden: float) -> tuple[str, str]:
    """Kirayə yükünə görə qısa hökm və rəng açarı."""
    if burden != burden:  # NaN
        return "Məlumat yoxdur", "muted"
    if burden <= NORM:
        return "Rahat — normaya sığır", "teal"
    if burden <= 0.45:
        return "Mümkün, amma sıx", "amber"
    return "Çətin — maaş çatmır", "coral"


@dataclass
class Result:
    p: Params
    seg_n: int
    fit_n: int
    fit_share: float
    median: float
    p25: float
    p75: float
    burden: float                 # median / ümumi gəlir
    need_salary: float            # 30%-ə sığmaq üçün 1 nəfərin maaşı
    verdict: tuple[str, str]
    districts: pd.DataFrame       # rayon, n, fit, share, median
    best: pd.DataFrame            # ən sərfəli uyğun elanlar
    savings: list[tuple[str, float]] = field(default_factory=list)
    cheap_names: list[str] = field(default_factory=list)


def compute(data: Data, p: Params, top: int = 40) -> Result:
    l = data.listings
    seg = segment(l, p)
    fit = seg[seg["price_azn"] <= p.budget]
    med = float(seg["price_azn"].median()) if len(seg) else float("nan")
    burden = med / p.income if p.income else float("nan")

    g = seg.groupby("district_name")
    dist = pd.DataFrame({
        "n": g.size(),
        "fit": g["price_azn"].apply(lambda s: int((s <= p.budget).sum())),
        "median": g["price_azn"].median(),
        "m2": g["price_per_m2"].median(),
    })
    dist["share"] = dist["fit"] / dist["n"]
    dist = (dist[dist["n"] >= MIN_N].reset_index()
            .merge(data.districts[["district_name", "is_baku_city", "latitude", "longitude"]], on="district_name", how="left")
            .sort_values(["share", "median"], ascending=[False, True]).reset_index(drop=True))

    best = (fit.assign(score=fit["price_per_m2"])
            .sort_values(["score", "price_azn"]).head(top))

    savings, cheap = savings_path(l, p)
    return Result(p, len(seg), len(fit), len(fit) / len(seg) if len(seg) else 0.0,
                  med, float(seg["price_azn"].quantile(.25)) if len(seg) else float("nan"),
                  float(seg["price_azn"].quantile(.75)) if len(seg) else float("nan"),
                  burden, med / NORM / p.people if med == med else float("nan"),
                  verdict(burden), dist, best, savings, cheap)


def savings_path(l: pd.DataFrame, p: Params) -> tuple[list[tuple[str, float]], list[str]]:
    """Median kirayəni addım-addım necə azaltmaq olar (Bakı şəhəri, seçilmiş otaq sayı)."""
    rooms = p.rooms if p.rooms != "Hamısı" else "2"
    base = l[(l["rooms_group"] == rooms) & (l["area"] == "Bakı şəhəri")]
    if base.empty:
        return [], []
    steps = [(f"{rooms} otaqlı, Bakı şəhəri (median)", float(base["price_azn"].median()))]
    by = base.groupby("district_name")["price_azn"].agg(["size", "median"])
    cheap = by[by["size"] >= 30].sort_values("median").head(4).index.tolist()
    s1 = base[base["district_name"].isin(cheap)]
    steps.append(("Ucuz rayonlara baxın", float(s1["price_azn"].median())))
    s2 = s1[s1["building_type"] == "Köhnə tikili"]
    if len(s2) >= 30:
        steps.append(("+ köhnə tikili", float(s2["price_azn"].median())))
        s1 = s2
    s3 = s1[s1["is_agency"] == "N"]
    if len(s3) >= 20:
        steps.append(("+ mülkiyyətçi elanı (vasitəçisiz)", float(s3["price_azn"].median())))
    n = max(p.people, 2)
    steps.append((f"{n} nəfər bölüşəndə (adambaşına)", steps[-1][1] / n))
    return steps, cheap


def market_facts(data: Data) -> dict:
    """Saytın «bazar» bölməsi və AI üçün sabit faktlar."""
    l = data.listings
    city = l[l["area"] == "Bakı şəhəri"]
    med2 = float(city[city["rooms_group"] == "2"]["price_azn"].median())
    rooms = l.groupby("rooms_group")["price_azn"].median().round().astype(int).to_dict()
    by_d = l.groupby("district_name")["price_azn"].agg(["size", "median"])
    by_d = by_d[by_d["size"] >= 30].sort_values("median")
    mas = l[(l["location_name"].str.contains("Masazır", na=False)) & (l["rooms_group"] == "2")]
    return {
        "n": len(l),
        "median": float(l["price_azn"].median()),
        "median_2_city": med2,
        "burden_2_city": med2 / data.baku_salary,
        "need_salary_2": med2 / NORM,
        "rooms": rooms,
        "new": float(l[l["building_type"] == "Yeni tikili"]["price_azn"].median()),
        "old": float(l[l["building_type"] == "Köhnə tikili"]["price_azn"].median()),
        "agency": float(l[l["is_agency"] == "Y"]["price_azn"].median()),
        "owner": float(l[l["is_agency"] == "N"]["price_azn"].median()),
        "agency_share": float((l["is_agency"] == "Y").mean()),
        "cheapest": by_d.head(3)["median"].to_dict(),
        "priciest": by_d.tail(3)["median"].iloc[::-1].to_dict(),
        "masazir_2": float(mas["price_azn"].median()) if len(mas) >= 20 else None,
        "baku_salary": data.baku_salary,
        "country_salary": data.country_salary,
        "salary_year": data.salary_year,
    }


def sector_afford(data: Data, rooms: str = "1", people: int = 1) -> pd.DataFrame:
    """Hər sahənin orta maaşı ilə seçilmiş otaq sayının median kirayəsi neçə faizdir."""
    l = data.listings
    city = l[(l["area"] == "Bakı şəhəri") & (l["rooms_group"] == rooms)]
    med = float(city["price_azn"].median())
    s = data.sectors.copy()
    s["burden"] = med / people / s["avg_salary_azn"]
    return s.sort_values("burden")
