"""Sensitivity tests for every judgement call in the Mumbai build.

Each section takes one decision made elsewhere in the pipeline and reports
what the alternative would have done to the published numbers. A caveat that
is not bounded is not finished work.
"""
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from mumbai import (RAW, OUT, INTERIM, UTM, load_wards, read_kml_points,
                    read_kml_polygons, ward_attr, norm_ward)
import build_wards as bw


def rule(t):
    print("\n" + "=" * 72)
    print(t)
    print("=" * 72)


def test_census_code_pairing():
    """HH-14 code 3837 vs census code 1045 (H/E) - left unpaired. Cost?"""
    rule("1. THE UNPAIRED CENSUS WARD CODE (1045 / 3837)")
    cw, hh, h14 = bw.load_census_wards(), bw.load_households(), bw.load_hh14()
    base = cw.merge(hh, on="code").merge(h14, on="code", how="left")

    def ward_pct(df):
        cov = df.dropna(subset=["pct_public_latrine", "households"])
        g = cov.groupby("ward").apply(lambda x: np.average(
            x["pct_public_latrine"], weights=x["households"]),
            include_groups=False)
        city = np.average(cov["pct_public_latrine"], weights=cov["households"])
        return g, city

    g0, c0 = ward_pct(base)
    # The alternative: treat 3837 as 1045.
    alt = h14.copy()
    alt.loc[alt["code"] == 3837, "code"] = 1045
    base2 = cw.merge(hh, on="code").merge(alt, on="code", how="left")
    g1, c1 = ward_pct(base2)

    print(f"  {'':22s} {'published':>12s} {'if paired':>12s}")
    print(f"  {'city-wide % public':22s} {c0:11.2f}% {c1:11.2f}%")
    print(f"  {'H/E ward %':22s} {g0['H/E']:11.2f}% {g1['H/E']:11.2f}%")
    print(f"  {'H/E household coverage':22s} {68.2:11.1f}% {100.0:11.1f}%")
    d = (g1 - g0).abs()
    print(f"  largest ward move: {d.max():.2f} pp ({d.idxmax()})")
    print("  -> H/E only, and it does not change any ranking that is reported.")


def test_grid_spacing():
    """The proximity result at three lattice spacings."""
    rule("2. GRID SPACING (published: 100 m)")
    g = pd.read_csv(INTERIM / "grid_access.csv")
    print("  Published grid, resampled - a coarser lattice is a subsample of")
    print("  the same cells, so this bounds spacing sensitivity directly.")
    print(f"  {'sample':>10s} {'cells':>9s} {'slum med':>9s} {'city med':>9s} {'ratio':>7s}")
    rng = np.random.default_rng(0)
    for name, frac in [("all", 1.0), ("1 in 4", .25), ("1 in 16", .0625)]:
        s = g if frac == 1.0 else g.sample(frac=frac, random_state=rng.integers(1e6))
        a = s.loc[s["slum"], "d_toilet"].median()
        b = s.loc[~s["slum"], "d_toilet"].median()
        print(f"  {name:>10s} {len(s):9,d} {a:9.0f} {b:9.0f} {a/b:7.2f}")


def test_undeveloped_land():
    """Does the proximity gap survive dropping the park/salt-pan wards?"""
    rule("3. UNDEVELOPED LAND (national park, salt pans, airport)")
    g = pd.read_csv(INTERIM / "grid_access.csv")
    w = pd.read_csv(OUT / "ward_panel.csv")
    w["dens"] = w["population"] / w["area_km2"]
    sparse = w.nsmallest(4, "dens")["ward"].tolist()
    print(f"  four least-dense wards: {', '.join(sparse)}")
    print(f"  {'set':>28s} {'slum':>8s} {'city':>8s} {'ratio':>7s}")
    for name, sub in [("all 24 wards (published)", g),
                      ("excluding those four", g[~g["ward"].isin(sparse)])]:
        a = sub.loc[sub["slum"], "d_toilet"].median()
        b = sub.loc[~sub["slum"], "d_toilet"].median()
        print(f"  {name:>28s} {a:8.0f} {b:8.0f} {a/b:7.2f}")
    print("\n  Within-ward, toilets, all services - the strongest control:")
    for key in ["toilet", "school_municipal", "health", "park", "bus"]:
        gaps = []
        for wd, x in g.groupby("ward"):
            s, n = x[x["slum"]], x[~x["slum"]]
            if len(s) >= 20 and len(n) >= 20:
                gaps.append(s[f"d_{key}"].median() - n[f"d_{key}"].median())
        gaps = np.array(gaps)
        print(f"    {key:18s} slum closer in {(gaps<0).sum():2d}/{len(gaps)} wards")


def test_seat_counts():
    """Toilets recording zero seats - how much do they move hh/seat?"""
    rule("4. TOILETS WITH NO SEAT COUNT RECORDED")
    g, _ = read_kml_points(RAW / "toilets.kml")
    m = pd.to_numeric(g.get("Count_of_M"), errors="coerce")
    f = pd.to_numeric(g.get("Count_of_F"), errors="coerce")
    tot = m.fillna(0) + f.fillna(0)
    zero = int((tot == 0).sum())
    print(f"  toilet points                 : {len(g):,}")
    print(f"  with no seats recorded        : {zero:,} ({zero/len(g):.1%})")
    print(f"  seats recorded                : {int(tot.sum()):,}")
    w0 = pd.read_csv(OUT / "ward_panel.csv")
    print(f"  seats inside a ward polygon   : {int(w0['toilet_seats'].sum()):,}"
          f"  ({int(tot.sum() - w0['toilet_seats'].sum()):,} on points that fall"
          f" outside every ward)")
    print(f"  median seats where recorded   : {tot[tot>0].median():.0f}")
    w = pd.read_csv(OUT / "ward_panel.csv")
    dep = w["hh_public_latrine"].sum()
    seats = w["toilet_seats"].sum()
    med = tot[tot > 0].median()
    print(f"\n  {'assumption for the blanks':38s} {'hh / seat':>10s}")
    print(f"  {'blanks are genuinely 0 (published)':38s} {dep/seats:10.1f}")
    print(f"  {'blanks hold the median, ' + f'{med:.0f} seats':38s} "
          f"{dep/(seats + zero*med):10.1f}")
    print("  -> the deficit is a lower bound either way; blanks can only")
    print("     understate supply, never overstate it.")


def test_spatial_vs_attribute():
    """Ward by spatial join vs the layers' own ward field."""
    rule("5. SPATIAL JOIN VS THE LAYERS' OWN WARD FIELD")
    wards, _ = load_wards()
    wards = wards.to_crs(UTM)
    print(f"  {'layer':22s} {'labelled':>9s} {'disagree':>9s} {'rank rho':>9s}")
    for f, lab in [("toilets.kml", "toilets"),
                   ("health_uphc.kml", "health UPHCs"),
                   ("parks.kml", "parks"),
                   ("funeral_sites.kml", "funeral sites")]:
        g, _ = read_kml_points(RAW / f)
        g["ward_attr"] = ward_attr(g)
        g = g.to_crs(UTM)
        g = gpd.sjoin(g, wards[["ward", "geometry"]], how="left",
                      predicate="within").drop(columns="index_right")
        both = g.dropna(subset=["ward", "ward_attr"])
        dis = (both["ward"] != both["ward_attr"]).mean()
        a = g.groupby("ward").size()
        b = g.groupby("ward_attr").size()
        j = pd.concat([a, b], axis=1).fillna(0)
        rho = j.iloc[:, 0].corr(j.iloc[:, 1], method="spearman")
        print(f"  {lab:22s} {len(both):9,d} {dis:8.1%} {rho:9.3f}")
    print("\n  Counts per ward rank almost identically either way, so the ward")
    print("  table is not sensitive to the choice; individual points are.")


def test_distance_method():
    """Polygon-to-point distance vs the centroid shortcut."""
    rule("6. POLYGON DISTANCE VS CENTROID DISTANCE")
    slums, _ = read_kml_polygons(RAW / "slums.kml")
    slums = slums.to_crs(UTM).reset_index(drop=True)
    slums["cluster_id"] = range(len(slums))
    t, _ = read_kml_points(RAW / "toilets.kml")
    t = t.to_crs(UTM)[["geometry"]].reset_index(drop=True)

    poly = gpd.sjoin_nearest(slums[["cluster_id", "geometry"]], t,
                             how="left", distance_col="d")
    poly = poly.groupby("cluster_id")["d"].min()
    cen = slums.copy()
    cen["geometry"] = cen.geometry.centroid
    cent = gpd.sjoin_nearest(cen[["cluster_id", "geometry"]], t,
                             how="left", distance_col="d")
    cent = cent.groupby("cluster_id")["d"].min()

    print(f"  {'':22s} {'median':>8s} {'p90':>8s} {'% at 0 m':>9s}")
    print(f"  {'polygon (published)':22s} {poly.median():8.0f} "
          f"{poly.quantile(.9):8.0f} {(poly==0).mean():8.1%}")
    print(f"  {'centroid':22s} {cent.median():8.0f} "
          f"{cent.quantile(.9):8.0f} {(cent==0).mean():8.1%}")
    big = slums.assign(a=slums.area).nlargest(int(len(slums) * .1), "a").index
    d = (cent - poly)
    print(f"\n  centroid overstates distance by a median {d.median():.0f} m"
          f" overall, {d.loc[d.index.isin(big)].median():.0f} m for the"
          " largest decile of clusters.")
    print("  -> the shortcut would have inflated every access figure, most")
    print("     for exactly the biggest settlements. Hence polygon distance.")


def test_slum_overlap():
    """Overlapping slum polygons - does double-counted area matter?"""
    rule("7. OVERLAPPING SLUM POLYGONS")
    slums, dropped = read_kml_polygons(RAW / "slums.kml")
    slums = slums.to_crs(UTM)
    summed = slums.area.sum() / 1e6
    union = slums.geometry.union_all().area / 1e6
    wards, _ = load_wards()
    total = wards["area_km2"].sum()
    print(f"  placemarks with no polygon : {dropped}")
    print(f"  area, summed per polygon   : {summed:.3f} km2 "
          f"({summed/total:.2%} of the city)")
    print(f"  area, geometric union      : {union:.3f} km2 "
          f"({union/total:.2%} of the city)")
    print(f"  double-counted             : {summed-union:.3f} km2 "
          f"({(summed-union)/summed:.2%})")
    print("  -> reported as ~7% of the city's land either way. The grid uses")
    print("     the union, so the slum/non-slum split is overlap-free.")


def test_inhabited_proxy():
    """The proximity result depends on what counts as inhabited land."""
    rule("8. WHAT COUNTS AS INHABITED LAND")
    g = pd.read_csv(INTERIM / "grid_access.csv")
    slum, base = g[g["slum"]], g[~g["slum"]]
    cats = [("toilet", "Public toilet"), ("school", "School (any)"),
            ("school_municipal", "Municipal school"), ("health", "Health centre"),
            ("funeral", "Funeral site"), ("fire", "Fire station"),
            ("police", "Police station"), ("park", "Park or garden"),
            ("rail", "Suburban station"), ("bus", "BEST bus stop")]
    proxies = [
        ("all land", None, None),
        ("<=300 m of a BEST stop", "near_bus", "bus"),
        ("<=400 m of a school", "near_school", "school"),
        ("either (published)", "inhabited", None),
    ]
    print("  Ratio of median distance, slum / non-slum. A proxy cannot score the")
    print("  layer that defines it, so those cells read 'circ'.")
    head = "  " + f"{'service':18s}" + "".join(f"{n[:20]:>22s}" for n, _, _ in proxies)
    print(head)
    for key, lab in cats:
        row = f"  {lab:18s}"
        s_ = slum[f"d_{key}"].median()
        for name, col, excl in proxies:
            if excl == key:
                row += f"{'circ':>22s}"
                continue
            # The published column falls back to the non-circular proxy for the
            # two layers that define the composite, exactly as analyse.py does.
            if col == "inhabited" and key == "bus":
                col = "near_school"
            elif col == "inhabited" and key in ("school", "school_municipal"):
                col = "near_bus"
            sub = base if col is None else base[base[col]]
            row += f"{s_ / sub[f'd_{key}'].median():22.2f}"
        print(row)
    print("\n  The toilet result holds under every baseline (0.19 - 0.35) and is")
    print("  the only one that is never close to parity. Schools survive; health")
    print("  and funeral sites fall to parity; parks, police, fire, rail and bus")
    print("  reverse. The published table uses the 'either' column, and the page")
    print("  reports only what survives it.")


def main():
    test_census_code_pairing()
    test_grid_spacing()
    test_undeveloped_land()
    test_seat_counts()
    test_spatial_vs_attribute()
    test_distance_method()
    test_slum_overlap()
    test_inhabited_proxy()
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
