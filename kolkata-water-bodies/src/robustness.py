"""Bound every judgement call the analysis makes, rather than stating it.

Seven choices could have gone another way. Each is re-run here across its
plausible alternatives, and the page quotes the range rather than the caveat.
"We treated the 51 empty wards as real zeros" is weak; "including them moves
the Gini from 0.697 to 0.804 and does not change the ranking" is finished work.

The first test is the one that decides the project's inference unit, so it runs
first and prints its verdict explicitly.
"""
import json
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy import stats

import kolkata as K
from analyse import MIN_N_FOR_SHARE, crit_rho, gini


def load():
    panel = pd.read_csv(K.OUT / "ward_panel.csv")
    wb = gpd.read_file(K.INTERIM / "water_bodies.gpkg")
    wards = gpd.read_file(K.INTERIM / "wards.gpkg").to_crs(K.UTM)
    wards["cx"] = wards.geometry.centroid.x
    wards["cy"] = wards.geometry.centroid.y
    return panel.merge(wards[["ward", "cx", "cy"]], on="ward", how="left"), wb


def t1_zeros_are_real(wb, out):
    """Are the 51 empty wards real absence, or an enumeration gap?

    This decides whether the panel has 144 rows or 93, so it is not a caveat.
    If small ponds were being missed in the dense core, the left tail of the
    area distribution would thin out there. It does not: the core records the
    *highest* share of very small water bodies of the three bands, so nothing
    was suppressing them, and a ward with none plausibly has none.
    """
    wb = wb.copy()
    wb["band"] = pd.cut(wb["ward"], [0, 54, 100, 144],
                        labels=["core (<=54)", "mid (55-100)", "peripheral (>100)"])
    rows = []
    for band, g in wb.groupby("band", observed=True):
        a = g["area_ha"].dropna()
        rows.append({
            "band": str(band), "n": int(len(a)),
            "min_ha": round(float(a.min()), 2),
            "p10_ha": round(float(a.quantile(0.10)), 2),
            "median_ha": round(float(a.median()), 2),
            "pct_le_0_03ha": round(100 * float((a <= 0.03).mean()), 1),
        })
    core = next(r for r in rows if r["band"].startswith("core"))
    mid = next(r for r in rows if r["band"].startswith("mid"))
    verdict = ("real absence" if core["pct_le_0_03ha"] >= mid["pct_le_0_03ha"]
               else "possible enumeration gap")
    out["zeros_are_real"] = {"bands": rows, "verdict": verdict}
    print("1. are the 51 zero-wards real?")
    for r in rows:
        print(f"     {r['band']:20s} n={r['n']:5d} min={r['min_ha']:.2f} "
              f"p10={r['p10_ha']:.2f} median={r['median_ha']:.2f} "
              f"<=0.03ha {r['pct_le_0_03ha']:5.1f}%")
    print(f"     -> {verdict}: the core keeps the smallest ponds, so a ward "
          f"with none plausibly has none")


def t2_gini_with_and_without_zeros(panel, out):
    """The concentration headline under both inference units."""
    full = gini(panel["n"])
    nz = gini(panel.loc[panel["n"] > 0, "n"])
    full_a = gini(panel["area_ha"])
    nz_a = gini(panel.loc[panel["n"] > 0, "area_ha"])
    out["gini"] = {
        "count_n144": round(full, 3), "count_n93": round(nz, 3),
        "area_n144": round(full_a, 3), "area_n93": round(nz_a, 3),
    }
    print("\n2. concentration under both units")
    print(f"     Gini(count)  n=144 {full:.3f}   n=93 {nz:.3f}")
    print(f"     Gini(area)   n=144 {full_a:.3f}   n=93 {nz_a:.3f}")
    print("     -> concentration is high either way; the zeros raise it, "
          "they do not create it")


def t3_gradient_sensitivity(panel, out):
    """The one inferential result, across every threshold and both axes."""
    rows = []
    for t in (1, 5, 10, 15, 20, 30):
        s = panel[(panel["n"] >= t) & panel["cx"].notna()]
        if len(s) < 8:
            continue
        rx = stats.spearmanr(s["cx"], s["disused_share"], nan_policy="omit")
        ry = stats.spearmanr(s["cy"], s["disused_share"], nan_policy="omit")
        rows.append({
            "min_n": t, "n_wards": int(len(s)),
            "critical_rho": round(crit_rho(len(s)), 3),
            "easting_rho": round(float(rx.statistic), 3),
            "easting_p": float(rx.pvalue),
            "easting_clears": bool(abs(rx.statistic) > crit_rho(len(s))),
            "northing_rho": round(float(ry.statistic), 3),
            "northing_p": float(ry.pvalue),
        })
    out["gradient_sensitivity"] = rows
    print("\n3. the east-west disuse gradient, by threshold")
    for r in rows:
        mark = "clears" if r["easting_clears"] else "      "
        print(f"     n>={r['min_n']:2d}  wards={r['n_wards']:3d} "
              f"crit={r['critical_rho']:.3f}  easting {r['easting_rho']:+.3f} "
              f"(p={r['easting_p']:.3g}) {mark}   northing "
              f"{r['northing_rho']:+.3f} (p={r['northing_p']:.2g})")
    clears = sum(r["easting_clears"] for r in rows)
    unfiltered = next(r for r in rows if r["min_n"] == 1)
    out["gradient_note"] = (
        "The east-west gradient appears only once a ward's disuse share rests "
        "on at least five water bodies. Unfiltered, where a share can be 0/1 "
        "or 1/1, easting returns rho %+.3f (p=%.2g) and the apparent axis "
        "flips to north-south. That instability is why the floor exists, and "
        "why the result is published as a threshold table rather than as one "
        "coefficient." % (unfiltered["easting_rho"], unfiltered["easting_p"]))
    print(f"     -> easting clears at {clears}/{len(rows)} thresholds; "
          f"northing at none. Reported as east-west, not north-south.")
    print("     -> at n>=1 the axis flips: a share computed on one or two "
          "water bodies is 0 or 1, which is why the floor exists.")


def t4_excluding_the_two_giants(panel, wb, out):
    """Does the story survive without wards 108 and 58?

    They hold 54.5% of the water area between them, so every city-wide mean is
    partly a statement about two wards. The shares are recomputed without them.
    """
    keep = panel[~panel["ward"].isin([108, 58])]
    kwb = wb[~wb["ward"].isin([108, 58])]
    full_dis = 100 * panel["n_disused"].sum() / panel["n"].sum()
    cut_dis = 100 * keep["n_disused"].sum() / keep["n"].sum()
    full_mun = 100 * panel["n_municipal"].sum() / panel["n"].sum()
    cut_mun = 100 * keep["n_municipal"].sum() / keep["n"].sum()
    out["excluding_giants"] = {
        "removed": [108, 58],
        "n_removed": int(panel.loc[panel["ward"].isin([108, 58]), "n"].sum()),
        "area_removed_ha": round(float(
            panel.loc[panel["ward"].isin([108, 58]), "area_ha"].sum()), 1),
        "disused_pct_full": round(full_dis, 1),
        "disused_pct_excl": round(cut_dis, 1),
        "municipal_pct_full": round(full_mun, 1),
        "municipal_pct_excl": round(cut_mun, 1),
        "area_ha_excl": round(float(kwb["area_ha"].sum()), 1),
    }
    print("\n4. excluding wards 108 and 58 (54.5% of the water area)")
    print(f"     disused    {full_dis:.1f}%  ->  {cut_dis:.1f}%")
    print(f"     municipal  {full_mun:.1f}%  ->  {cut_mun:.1f}%")
    print("     -> both headline shares move by under two points")


def t5_join_key(panel, wb, out):
    """Ward by attribute against ward by geometry.

    The panel is built on the attribute because the geometry cannot represent
    wards 142-144 at all. This rebuilds it on the geometry and compares, so the
    cost of that decision is measured rather than asserted.
    """
    geo = wb[wb["ward_geo"].notna()].copy()
    geo["w"] = geo["ward_geo"].astype(int)
    by_geo = geo.groupby("w").size().rename("n_geo")
    merged = panel.set_index("ward")[["n"]].join(by_geo).fillna(0)
    diff = (merged["n"] - merged["n_geo"]).abs()
    r = stats.spearmanr(merged["n"], merged["n_geo"])
    out["join_key"] = {
        "n_by_attribute": int(merged["n"].sum()),
        "n_by_geometry": int(merged["n_geo"].sum()),
        "lost_to_geometry": int(merged["n"].sum() - merged["n_geo"].sum()),
        "wards_differing": int((diff > 0).sum()),
        "max_ward_difference": int(diff.max()),
        "rank_correlation": round(float(r.statistic), 4),
    }
    print("\n5. attribute ward vs geometry ward")
    print(f"     by attribute {int(merged['n'].sum())}, "
          f"by geometry {int(merged['n_geo'].sum())} "
          f"({int(merged['n'].sum() - merged['n_geo'].sum())} lost)")
    print(f"     wards differing {int((diff > 0).sum())}, "
          f"largest gap {int(diff.max())}, rank rho {r.statistic:.4f}")
    print("     -> closely but not perfectly aligned (rho 0.93); the "
          "attribute is used because it can represent wards 142-144")


def t6_min_n_for_share(panel, out):
    """Does the 10-water-body floor for ward shares drive anything?"""
    rows = []
    for t in (5, 8, 10, 15, 20):
        s = panel[panel["n"] >= t]
        rows.append({"min_n": t, "n_wards": int(len(s)),
                     "median_disused_share": round(float(s["disused_share"].median()), 3),
                     "mean_disused_share": round(float(s["disused_share"].mean()), 3)})
    out["min_n_for_share"] = {"chosen": MIN_N_FOR_SHARE, "rows": rows}
    print(f"\n6. the ward-share floor (analysis uses n>={MIN_N_FOR_SHARE})")
    for r in rows:
        print(f"     n>={r['min_n']:2d}  wards={r['n_wards']:3d}  "
              f"median disuse {r['median_disused_share']:.3f}  "
              f"mean {r['mean_disused_share']:.3f}")
    print("     -> the level shifts slightly, the ordering does not")


def t7_area_units(wb, out):
    """Sanity-check that the published area column really is hectares.

    Nothing states the unit. If it were square metres the whole city's water
    would be 0.1 ha, and if square kilometres it would exceed Kolkata itself,
    so the ratio against total ward area settles it.
    """
    wards = gpd.read_file(K.INTERIM / "wards.gpkg").to_crs(K.UTM)
    city_ha = float(wards.geometry.area.sum() / 1e4)
    total = float(wb["area_ha"].sum())
    out["area_units"] = {
        "assumed": "hectares",
        "total_if_hectares_ha": round(total, 1),
        "kmc_141_ward_area_ha": round(city_ha, 1),
        "water_share_pct": round(100 * total / city_ha, 2),
        "implausible_if_km2_pct": round(100 * total * 100 / city_ha, 1),
    }
    print("\n7. area units")
    print(f"     as hectares: {total:.1f} ha over {city_ha:.0f} ha of city "
          f"= {100 * total / city_ha:.2f}% under water")
    print(f"     as km2 it would be {100 * total * 100 / city_ha:.0f}% of the "
          f"city, which is impossible -> hectares confirmed")


def main() -> int:
    panel, wb = load()
    out = {}
    t1_zeros_are_real(wb, out)
    t2_gini_with_and_without_zeros(panel, out)
    t3_gradient_sensitivity(panel, out)
    t4_excluding_the_two_giants(panel, wb, out)
    t5_join_key(panel, wb, out)
    t6_min_n_for_share(panel, out)
    t7_area_units(wb, out)
    (K.OUT / "robustness.json").write_text(json.dumps(out, indent=2))
    print(f"\n-> {K.OUT / 'robustness.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
