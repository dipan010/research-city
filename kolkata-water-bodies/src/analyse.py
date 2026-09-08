"""The analysis. Produces every number the page quotes, as JSON.

What this does and does not claim, decided before the numbers were written up:

**Descriptive results carry the chapter.** Concentration, ownership composition
and disuse are exact counts on complete denominators, and they need no
inference. They are the findings.

**One inferential result survived.** Disuse has an east-west gradient at ward
level, stable across three count thresholds and clearing the 5% critical value
at each. It is reported with its critical value alongside, because at n=47 that
matters more than the p-value does.

**Three results were dropped for being artifacts, and are reported as nulls.**
The disuse-vs-pond-count correlation looks strong at n>=1 and evaporates by
n>=30, so it was measuring the coarseness of a share computed on two or three
water bodies. Municipal ownership does not predict lower disuse at ward level.
And the water-body-level chi-square on ownership against use is significant only
because 3,051 clustered points are treated as independent, which is the Mumbai
grid-cell mistake in a different costume - it is computed here so the page can
say why it is not reported.
"""
import json
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy import stats

import kolkata as K

PERIPHERAL = ("XIII", "XIV", "XV", "XVI")
BOROUGH_ORDER = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII",
                 "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI"]

# Minimum water bodies per ward before a *share* computed on that ward is
# treated as meaningful. 10 keeps 47 wards; the sensitivity to this choice is
# in robustness.py rather than asserted here.
MIN_N_FOR_SHARE = 10

# East Kolkata Wetlands Ramsar site, hectares. Used only to show the published
# census is not a wetlands dataset.
EKW_RAMSAR_HA = 12_500

# Prior counts of Kolkata's ponds, from Mohit Ray's CSE presentation
# "Water bodies of Kolkata". Different instruments and different vintages, so
# these frame a question rather than support a loss estimate.
PRIOR_COUNTS = {"KMC 1997": 1786, "KMC 2006": 3873,
                "NATMO 2006": 8731, "Satellite imagery": 4889}


def gini(x):
    """Gini over all 144 wards, zeros included.

    Computed on the full ward set rather than the 93 non-empty ones: a ward
    with no water body is a real part of how unequally the stock is spread,
    and dropping it would flatter the distribution.
    """
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return float("nan")
    return float((2 * np.sum(np.arange(1, n + 1) * x) / (n * x.sum())) - (n + 1) / n)


def crit_rho(n):
    """Approximate two-sided 5% critical value for Spearman's rho."""
    return float(1.96 / np.sqrt(n - 1))


def spear(a, b):
    r = stats.spearmanr(a, b, nan_policy="omit")
    return {"rho": round(float(r.statistic), 3),
            "p": float(r.pvalue), "n": int(min(len(a), len(b)))}


def main() -> int:
    panel = pd.read_csv(K.OUT / "ward_panel.csv")
    wb = gpd.read_file(K.INTERIM / "water_bodies.gpkg")
    wards = gpd.read_file(K.INTERIM / "wards.gpkg").to_crs(K.UTM)
    wards["cx"] = wards.geometry.centroid.x
    wards["cy"] = wards.geometry.centroid.y
    panel = panel.merge(wards[["ward", "cx", "cy"]], on="ward", how="left")
    join = json.loads((K.OUT / "join_report.json").read_text())

    total_n = int(panel["n"].sum())
    total_ha = float(panel["area_ha"].sum())
    covered = int((panel["n"] > 0).sum())
    R = {}

    # ---- 1. scale and concentration ----------------------------------
    order = panel.sort_values("n", ascending=False)
    top2 = panel[panel["ward"].isin([108, 58])]
    areas = np.sort(wb["area_ha"].dropna().values)[::-1]
    top5pct = areas[:max(1, int(round(len(areas) * 0.05)))]
    R["scale"] = {
        "n_water_bodies": total_n,
        "total_area_ha": round(total_ha, 1),
        "wards_total": K.N_WARDS_KMC,
        "wards_with_any": covered,
        "wards_zero": K.N_WARDS_KMC - covered,
        "median_area_ha": round(float(wb["area_ha"].median()), 3),
        "p95_area_ha": round(float(wb["area_ha"].quantile(0.95)), 2),
        "max_area_ha": round(float(wb["area_ha"].max()), 2),
        "min_area_ha": round(float(wb["area_ha"].min()), 2),
        "gini_count": round(gini(panel["n"]), 3),
        "gini_area": round(gini(panel["area_ha"]), 3),
        "top20_share_pct": round(100 * order["n"].head(20).sum() / total_n, 1),
        "top10_share_pct": round(100 * order["n"].head(10).sum() / total_n, 1),
        "ward108_58_area_ha": round(float(top2["area_ha"].sum()), 1),
        "ward108_58_area_pct": round(100 * float(top2["area_ha"].sum()) / total_ha, 1),
        "largest_5pct_area_share": round(100 * float(top5pct.sum()) / total_ha, 1),
    }

    # ---- 2. ownership -------------------------------------------------
    muni = int(panel["n_municipal"].sum())
    per = panel[panel["borough"].isin(PERIPHERAL)]
    rest = panel[~panel["borough"].isin(PERIPHERAL)]
    R["ownership"] = {
        "municipal": muni,
        "municipal_pct": round(100 * muni / total_n, 1),
        "private_pct": round(100 * (total_n - muni) / total_n, 1),
        "municipal_area_ha": round(float(wb.loc[wb["municipal"], "area_ha"].sum()), 1),
        "breakdown": (wb["water_body_ownership"].value_counts()
                      .head(8).astype(int).to_dict()),
        "peripheral": {
            "boroughs": list(PERIPHERAL),
            "wards": int(len(per)),
            "n": int(per["n"].sum()),
            "share_of_city_pct": round(100 * per["n"].sum() / total_n, 1),
            "municipal": int(per["n_municipal"].sum()),
            "municipal_pct": round(100 * per["n_municipal"].sum() / per["n"].sum(), 1),
        },
        "rest": {
            "wards": int(len(rest)),
            "n": int(rest["n"].sum()),
            "municipal": int(rest["n_municipal"].sum()),
            "municipal_pct": round(100 * rest["n_municipal"].sum() / rest["n"].sum(), 1),
        },
    }

    # ---- 3. disuse ----------------------------------------------------
    disused = int(panel["n_disused"].sum())
    xivxv = panel[panel["borough"].isin(["XIV", "XV"])]
    bor = (panel.groupby("borough")[["n", "n_disused", "n_municipal", "area_ha"]]
           .sum().reindex(BOROUGH_ORDER).fillna(0))
    bor["disused_pct"] = (100 * bor["n_disused"] / bor["n"]).round(1)
    bor["municipal_pct"] = (100 * bor["n_municipal"] / bor["n"]).round(1)
    bor["wards"] = panel.groupby("borough").size().reindex(BOROUGH_ORDER)
    R["disuse"] = {
        "n_disused": disused,
        "pct": round(100 * disused / total_n, 1),
        "use_breakdown": (wb.loc[wb["in_use"], "waterbody_use"]
                          .value_counts().astype(int).to_dict()),
        "xiv_xv": {
            "n": int(xivxv["n"].sum()),
            "stock_share_pct": round(100 * xivxv["n"].sum() / total_n, 1),
            "disused": int(xivxv["n_disused"].sum()),
            "disused_share_of_all_pct": round(
                100 * xivxv["n_disused"].sum() / disused, 1),
        },
        "by_borough": [
            {"borough": b, "wards": int(r["wards"]), "n": int(r["n"]),
             "area_ha": round(float(r["area_ha"]), 1),
             "disused": int(r["n_disused"]),
             "disused_pct": (None if r["n"] == 0 else float(r["disused_pct"])),
             "municipal": int(r["n_municipal"]),
             "municipal_pct": (None if r["n"] == 0 else float(r["municipal_pct"]))}
            for b, r in bor.iterrows()
        ],
        # Boroughs whose rate rests on a denominator too small to read. Kept
        # visible on the page rather than silently filtered out of the table.
        "small_denominator_boroughs": [
            b for b, r in bor.iterrows() if 0 < r["n"] < 20],
    }

    # ---- 4. the one inferential result -------------------------------
    q = panel[(panel["n"] >= MIN_N_FOR_SHARE) & panel["cx"].notna()]
    R["gradient"] = {
        "unit": "ward",
        "min_n": MIN_N_FOR_SHARE,
        "n_wards": int(len(q)),
        "critical_rho_5pct": round(crit_rho(len(q)), 3),
        "easting_vs_disuse": spear(q["cx"], q["disused_share"]),
        "northing_vs_disuse": spear(q["cy"], q["disused_share"]),
        "thresholds": [
            {"min_n": t,
             "n_wards": int(len(s)),
             "critical_rho_5pct": round(crit_rho(len(s)), 3),
             "easting": spear(s["cx"], s["disused_share"])}
            for t in (5, 10, 20)
            for s in [panel[(panel["n"] >= t) & panel["cx"].notna()]]
        ],
    }

    # ---- 5. nulls, reported because they were tested -----------------
    ct = pd.crosstab(wb["municipal"], wb["in_use"])
    chi = stats.chi2_contingency(ct)
    R["nulls"] = {
        "municipal_vs_disuse_ward": spear(q["municipal_share"], q["disused_share"]),
        "count_vs_disuse_by_threshold": [
            {"min_n": t, "n_wards": int(len(s)),
             **spear(s["n"], s["disused_share"])}
            for t in (1, 5, 10, 20, 30)
            for s in [panel[panel["n"] >= t]]
        ],
        "waterbody_level_chi2": {
            "municipal_in_use": int(ct.loc[True, True]),
            "municipal_total": int(ct.loc[True].sum()),
            "private_in_use": int(ct.loc[False, True]),
            "private_total": int(ct.loc[False].sum()),
            "p": float(chi.pvalue),
            "why_not_reported": (
                "3,051 points clustered in 93 wards, 453 of them in ward 108, "
                "are not independent observations. The ward-level test on the "
                "same question returns nothing."),
        },
    }

    # ---- 6. denominators ---------------------------------------------
    nz = panel[panel["n"] > 0]
    R["denominators"] = {
        "note": ("Unlike Bengaluru, the choice of denominator barely moves the "
                 "geography here. Only the share of ward area under water "
                 "reorders the ranking, and it picks out single large ponds "
                 "rather than pond-rich wards."),
        "pairs": [
            {"a": a, "b": b, **spear(nz[a], nz[b])}
            for a, b in [("n", "n_per_km2"),
                         ("n", "n_per_10k_electors"),
                         ("n_per_km2", "n_per_10k_electors"),
                         ("n_per_km2", "area_pct_of_ward")]
        ],
        "top10_by": {c: [int(w) for w in panel.nlargest(10, c)["ward"]]
                     for c in ("n", "n_per_km2", "n_per_10k_electors",
                               "area_pct_of_ward")},
        "electorate_caveat": (
            "Registered electors, 2015 KMC election. An electorate, not a "
            "population, and a decade older than the water bodies census. It "
            "is used because it is the only complete per-ward denominator KMC "
            "publishes that is not sourced from Kolkata district, which is "
            "smaller than KMC's jurisdiction."),
    }

    # ---- 7. what the data is not -------------------------------------
    R["not_ekw"] = {
        "total_area_ha": round(total_ha, 1),
        "ramsar_ha": EKW_RAMSAR_HA,
        "ratio_pct": round(100 * total_ha / EKW_RAMSAR_HA, 1),
        "max_body_ha": round(float(wb["area_ha"].max()), 2),
        "east_of_bypass": {
            "lon_cut": 88.40,
            "n": int((pd.to_numeric(wb["longitude"], errors="coerce") >= 88.40).sum()),
            "area_ha": round(float(wb.loc[
                pd.to_numeric(wb["longitude"], errors="coerce") >= 88.40,
                "area_ha"].sum()), 1),
        },
        "max_longitude": round(float(pd.to_numeric(wb["longitude"],
                                                   errors="coerce").max()), 3),
    }
    R["prior_counts"] = {
        "counts": PRIOR_COUNTS,
        "this_census": total_n,
        "source": ("Mohit Ray, 'Water bodies of Kolkata', Centre for Science "
                   "and Environment. Different instruments and vintages, so "
                   "the gap frames a question about what each counted, not a "
                   "loss estimate."),
    }

    # ---- 8. data quality ---------------------------------------------
    R["quality"] = {
        "join": join["agreement"],
        "dead_fields": join["dead_fields"],
        "enumerated_from": join["enumerated_from"],
        "enumerated_to": join["enumerated_to"],
        "ward_polygons": K.N_WARDS_KML,
        "wards_kmc": K.N_WARDS_KMC,
        "wards_without_polygon": list(K.WARDS_WITHOUT_POLYGON),
    }

    R["wards"] = json.loads(panel.drop(columns=["cx", "cy"]).to_json(orient="records"))

    (K.OUT / "results.json").write_text(json.dumps(R, indent=2))

    # ---- console summary ---------------------------------------------
    s, o, d, g = R["scale"], R["ownership"], R["disuse"], R["gradient"]
    print(f"{s['n_water_bodies']} water bodies, {s['total_area_ha']} ha, "
          f"{s['wards_with_any']}/{s['wards_total']} wards "
          f"({s['wards_zero']} zeros)")
    print(f"concentration  gini {s['gini_count']} (count), {s['gini_area']} (area); "
          f"top 20 wards {s['top20_share_pct']}%; "
          f"wards 108+58 hold {s['ward108_58_area_pct']}% of area")
    print(f"ownership      municipal {o['municipal']} ({o['municipal_pct']}%); "
          f"peripheral boroughs {o['peripheral']['municipal']}/"
          f"{o['peripheral']['n']} ({o['peripheral']['municipal_pct']}%) "
          f"vs {o['rest']['municipal_pct']}% elsewhere")
    print(f"disuse         {d['n_disused']} ({d['pct']}%); "
          f"XIV+XV hold {d['xiv_xv']['stock_share_pct']}% of stock but "
          f"{d['xiv_xv']['disused_share_of_all_pct']}% of all disused")
    print(f"gradient       easting rho {g['easting_vs_disuse']['rho']} "
          f"(p={g['easting_vs_disuse']['p']:.3g}, n={g['n_wards']}, "
          f"crit={g['critical_rho_5pct']}); "
          f"northing rho {g['northing_vs_disuse']['rho']} "
          f"(p={g['northing_vs_disuse']['p']:.2g}) - null")
    print(f"not EKW        {s['total_area_ha']} ha vs Ramsar "
          f"{EKW_RAMSAR_HA} ha = {R['not_ekw']['ratio_pct']}%")
    print(f"\n-> {K.OUT / 'results.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
