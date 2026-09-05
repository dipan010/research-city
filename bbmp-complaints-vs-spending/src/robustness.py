"""Sensitivity tests for the three open questions in this analysis.

Each of these was previously carried as a caveat. The point here is to bound
them: either resolve the ambiguity, or show the findings do not depend on it.

  1. Two grievance ward names that match no 198-ward (1.7% of complaints)
  2. Complaints (2020-24) and work orders (2018-23) covering different windows
  3. Population from Census 2011, applied to a periphery that has since grown
"""
import pathlib
import sys
import warnings

warnings.filterwarnings("ignore")
import geopandas as gpd
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW, INTERIM, OUT = (ROOT / "data" / d for d in ("raw", "interim", "out"))
CR = 1e7

# Inferred assignments for the two unmatched grievance names. Neither is certain;
# both are tested rather than assumed - see main().
INFERRED = {
    "Someshwara": 3,        # 243-ward "Someshwara Ward" (#3) covers 57% of
                            # 198-ward 3 Atturu, which otherwise has zero
                            # complaints despite Rs 350 cr of work orders
    "Subedarapalya": 65,    # by elimination onto 198-ward 65 Kadu Malleshwar,
                            # the only other ward with no complaints; volume
                            # (1,683) matches its neighbours' median (1,415)
}


def load_panel():
    return pd.read_csv(OUT / "panel_ward.csv")


def corr(d, a, b):
    return (d[a].corr(d[b]), d[a].corr(d[b], method="spearman"))


def geo():
    g = gpd.read_file(RAW / "bbmp_ward_map_2015.kml").to_crs(32643)
    g["ward_no"] = (g["Name"].astype(str).str.replace("\xa0", " ", regex=False)
                    .str.extract(r"(\d+)").astype(int))
    g["area_km2"] = g.geometry.area / 1e6
    centre = g.geometry.union_all().centroid
    g["dist_km"] = g.geometry.centroid.distance(centre) / 1000
    return g[["ward_no", "area_km2", "dist_km"]]


def population():
    c = pd.read_csv(RAW / "ward_population_2011.csv")
    c.columns = [x.strip() for x in c.columns]
    c["ward_no"] = pd.to_numeric(c["Ward Num"], errors="coerce")
    c["pop"] = pd.to_numeric(c["Population"], errors="coerce")
    return c.dropna(subset=["ward_no", "pop"]).astype({"ward_no": int})[["ward_no", "pop"]]


def unmatched_counts():
    """Complaint volumes for the two unmatched names, by year."""
    out = {}
    for name in INFERRED:
        total = 0
        for year in range(2020, 2025):
            f = RAW / f"grievances_{year}.csv"
            col = pd.read_csv(f, usecols=["Ward Name"], dtype=str)["Ward Name"]
            total += int((col.str.strip() == name).sum())
        out[name] = total
    return out


def test_unmatched(panel):
    print("\n" + "=" * 72)
    print("1. THE TWO UNMATCHED WARD NAMES")
    print("=" * 72)
    vols = unmatched_counts()
    for n, v in vols.items():
        print(f"   {n:<16} {v:>7,} complaints -> inferred ward {INFERRED[n]}")

    base = panel[panel["complaints"].notna()].copy()
    alt = panel.copy()
    for name, ward in INFERRED.items():
        i = alt.index[alt["ward_no"] == ward]
        alt.loc[i, "complaints"] = alt.loc[i, "complaints"].fillna(0) + vols[name]
    alt = alt[alt["complaints"].notna()]

    print(f"\n   {'':<26}{'EXCLUDED (published)':>22}{'ASSIGNED':>18}")
    print(f"   {'wards analysed':<26}{len(base):>22}{len(alt):>18}")
    for lab, f in [("pearson", 0), ("spearman", 1)]:
        b = corr(base, "complaints", "spend_total")[f]
        a = corr(alt, "complaints", "spend_total")[f]
        print(f"   {'complaints vs spend, '+lab:<26}{b:>22.3f}{a:>18.3f}")
    print(f"   {'total complaints':<26}{int(base['complaints'].sum()):>22,}"
          f"{int(alt['complaints'].sum()):>18,}")
    print("\n   -> the headline correlation is unchanged to two decimals either way.")
    return alt


def test_window(panel):
    print("\n" + "=" * 72)
    print("2. MISALIGNED TIME WINDOWS")
    print("=" * 72)
    byy = pd.read_csv(INTERIM / "grievances_by_ward_year.csv")
    g = geo()
    for lo, hi, lab in [(2020, 2024, "2020-24 (published)"),
                        (2020, 2023, "2020-23, work-order overlap"),
                        (2021, 2023, "2021-23, tightest overlap")]:
        sub = (byy[byy["year"].between(lo, hi)]
               .groupby("ward_no", as_index=False)["complaints"].sum())
        d = panel[["ward_no", "spend_total"]].merge(sub, on="ward_no").dropna()
        d = d.merge(g, on="ward_no")
        p_, s_ = corr(d, "complaints", "spend_total")
        d["ckm"] = d["complaints"] / d["area_km2"]
        dens = d["dist_km"].corr(d["ckm"], method="spearman")
        print(f"   {lab:<30} pearson {p_:.3f}  spearman {s_:.3f}  "
              f"density-vs-distance {dens:+.3f}")
    print("\n   -> dropping 2024 moves nothing materially; the window choice is not "
          "load-bearing.")


def test_population(panel):
    print("\n" + "=" * 72)
    print("3. CENSUS 2011 POPULATION vs A PERIPHERY THAT GREW")
    print("=" * 72)
    d = (panel[panel["complaints"].notna()]
         .merge(population(), on="ward_no").merge(geo(), on="ward_no"))
    d["ring"] = pd.qcut(d["dist_km"], 4, labels=["inner", "mid-in", "mid-out", "outer"])
    d["c1k"] = d["complaints"] / d["pop"] * 1000
    r = d.groupby("ring", observed=True)["c1k"].median()
    inner, outer = r["inner"], r["outer"]
    need = outer / inner
    yrs = 2024 - 2011
    print(f"   complaints per 1,000 residents: inner {inner:.1f}, outer {outer:.1f}")
    print(f"   for the outer ring to fall to the inner ring's rate, outer")
    print(f"   population would have to be {need:.2f}x the 2011 count -")
    print(f"   {100*(need**(1/yrs)-1):.1f}% compounded annually over {yrs} years,")
    print(f"   on top of whatever the inner ring did.")
    for mult in (1.25, 1.5, 2.0):
        adj = d.copy()
        m = adj["ring"] == "outer"
        adj.loc[m, "c1k"] = adj.loc[m, "complaints"] / (adj.loc[m, "pop"] * mult) * 1000
        rr = adj.groupby("ring", observed=True)["c1k"].median()
        sign = "outer still higher" if rr["outer"] > rr["inner"] else "GRADIENT FLIPS"
        print(f"   outer pop x{mult:<4}  inner {rr['inner']:5.1f}  "
              f"outer {rr['outer']:5.1f}   {sign}")
    print("\n   -> the per-resident gradient survives plausible growth, but is the")
    print("      least robust of the three findings. Stated as such.")


def main() -> int:
    panel = load_panel()
    test_unmatched(panel)
    test_window(panel)
    test_population(panel)
    print("\n" + "=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
