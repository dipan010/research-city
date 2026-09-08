"""Assign water bodies to wards, then build the per-ward panel.

Two decisions here carry the whole analysis, and both are Mumbai lessons.

**Assign spatially, keep the attribute.** The census stores a ward inside its
`village` field *and* carries independent coordinates. The spatial join is what
assigns the ward; the attribute is kept only to measure how often the two
disagree, which is a data-quality finding in its own right rather than a thing
to quietly reconcile.

**The 51 zero-wards are real, so the panel has 144 rows, not 93.** Wards with no
water body are carried as genuine zeros. The evidence is in `robustness.py`:
enumerators recorded ponds down to 0.02 ha inside the dense core, at a higher
small-pond share than the mid band, so no size threshold was suppressing them
there. The n=93 restriction is run alongside as the sensitivity case.

The ward polygons are the pre-2015 141-ward set, so wards 142-144 have no
geometry. Their water bodies can only be placed by attribute, and the count is
reported rather than dropped.
"""
import json
import sys

import geopandas as gpd
import numpy as np
import pandas as pd

import kolkata as K

# `water_spread_area_of_water_body` is published in hectares. Checked against
# the coordinates rather than assumed: the largest body reads 38.93, and its
# footprint on the ground is consistent with tens of hectares, not tens of
# square metres or square kilometres.
AREA_COL = "water_spread_area_of_water_body"

# Fields the census defines but did not populate for Kolkata: every one of the
# 3,051 records carries the same value. Dropped from the panel, and reported on
# the page, because a constant column is not a result. The encroachment field
# especially: the instrument collects it nationally, so a uniformly negative
# column in a city with a litigated pond-filling history is evidence the field
# was never filled in, not evidence of no encroachment.
DEAD_FIELDS = ("waterbody_encroached", "water_body_nature")


def load_water_bodies():
    g, dropped = K.read_kml_points(K.RAW / "water_bodies.kml", "water_bodies")
    g["ward_attr"] = g["village"].map(K.ward_from_village)
    g["area_ha"] = pd.to_numeric(g[AREA_COL], errors="coerce")
    g["in_use"] = g["waterbody_use_notuse"].str.strip().str.lower().eq("yes")
    g["municipal"] = g["water_body_ownership"].str.strip().eq("Muncipal authority")
    # `enumeration_date` is epoch milliseconds. This is the file's only real
    # vintage evidence: the portal describes it as 2018-19 and names the
    # resource "2023", and both are wrong.
    g["enumerated"] = pd.to_datetime(
        pd.to_numeric(g["enumeration_date"], errors="coerce"),
        unit="ms", errors="coerce")
    return g, dropped


def check_dead_fields(g):
    out = {}
    for col in DEAD_FIELDS:
        vals = g[col].dropna().unique()
        out[col] = {"distinct": len(vals), "value": vals[0] if len(vals) == 1 else None}
    return out


def assign_wards(wb, wards):
    """Spatial join to ward polygons, with the attribute kept alongside."""
    joined = gpd.sjoin(
        wb.to_crs(K.UTM),
        wards.to_crs(K.UTM)[["ward", "geometry"]].rename(columns={"ward": "ward_geo"}),
        how="left", predicate="within")
    # A point on a shared boundary can match two polygons; keep the first and
    # count how often it happened rather than letting the row count inflate.
    dupes = int(joined.index.duplicated().sum())
    joined = joined[~joined.index.duplicated(keep="first")]
    joined["ward_geo"] = joined["ward_geo"].astype("Int64")
    return joined.to_crs(K.WGS84), dupes


def agreement_report(g):
    """How often the census's own ward label matches where the point falls.

    Split three ways, because the three cases mean different things:
      * both present and equal / unequal - the real disagreement rate
      * attribute present, no polygon    - wards 142-144, the boundary caveat
      * fell outside every ward polygon  - point outside KMC's 141-ward extent
    """
    has_geo = g["ward_geo"].notna()
    has_attr = g["ward_attr"].notna()
    both = has_geo & has_attr
    agree = int((g.loc[both, "ward_geo"] == g.loc[both, "ward_attr"]).sum())
    outside = g.loc[~has_geo & has_attr]
    in_missing = outside["ward_attr"].isin(K.WARDS_WITHOUT_POLYGON)
    return {
        "total": int(len(g)),
        "both_present": int(both.sum()),
        "agree": agree,
        "disagree": int(both.sum()) - agree,
        "disagree_pct": round(100 * (int(both.sum()) - agree) / max(int(both.sum()), 1), 1),
        "no_polygon_but_attr": int((~has_geo & has_attr).sum()),
        "in_wards_142_144": int(in_missing.sum()),
        "outside_and_not_142_144": int((~in_missing).sum()),
        "no_attr": int((~has_attr).sum()),
    }


def build_panel(g, wards, boroughs, electors):
    """One row per KMC ward, all 144, zeros carried.

    Ward is taken from the attribute, not the geometry, for one reason: the
    geometry cannot represent wards 142-144 at all, and silently excluding
    three wards from a 144-ward panel is precisely the trap this project set
    out to avoid. The spatial join's role is to validate that choice, and it
    does - the agreement rate is reported on the page.
    """
    g = g[g["ward_attr"].notna()].copy()
    g["ward"] = g["ward_attr"].astype(int)

    agg = g.groupby("ward").agg(
        n=("ward", "size"),
        area_ha=("area_ha", "sum"),
        area_median_ha=("area_ha", "median"),
        area_max_ha=("area_ha", "max"),
        n_in_use=("in_use", "sum"),
        n_municipal=("municipal", "sum"),
    ).reset_index()

    panel = pd.DataFrame({"ward": range(1, K.N_WARDS_KMC + 1)})
    panel = panel.merge(agg, on="ward", how="left")
    for col in ("n", "area_ha", "n_in_use", "n_municipal"):
        panel[col] = panel[col].fillna(0)
    panel["n"] = panel["n"].astype(int)
    panel["n_in_use"] = panel["n_in_use"].astype(int)
    panel["n_municipal"] = panel["n_municipal"].astype(int)

    panel = panel.merge(boroughs, on="ward", how="left")
    panel = panel.merge(electors, on="ward", how="left")
    panel = panel.merge(wards[["ward", "area_km2"]], on="ward", how="left")

    panel["has_polygon"] = panel["area_km2"].notna()
    panel["n_disused"] = panel["n"] - panel["n_in_use"]
    # Rates. Every one names its denominator; three of them disagree about the
    # geography, which is the Bengaluru lesson and is shown on the page.
    with np.errstate(divide="ignore", invalid="ignore"):
        panel["n_per_km2"] = panel["n"] / panel["area_km2"]
        panel["area_pct_of_ward"] = 100 * (panel["area_ha"] / 100) / panel["area_km2"]
        panel["n_per_10k_electors"] = 1e4 * panel["n"] / panel["electors"]
        panel["disused_share"] = np.where(
            panel["n"] > 0, panel["n_disused"] / panel["n"], np.nan)
        panel["municipal_share"] = np.where(
            panel["n"] > 0, panel["n_municipal"] / panel["n"], np.nan)
    return panel


def main() -> int:
    K.INTERIM.mkdir(parents=True, exist_ok=True)
    K.OUT.mkdir(parents=True, exist_ok=True)

    wards, ward_dropped = K.load_wards()
    boroughs = K.load_boroughs()
    electors = K.load_electorate()
    wb, wb_dropped = load_water_bodies()

    print(f"ward polygons      {len(wards):5d}  (dropped {ward_dropped}) "
          f"- KMC has {K.N_WARDS_KMC}, absent: {K.WARDS_WITHOUT_POLYGON}")
    print(f"water bodies       {len(wb):5d}  (dropped {wb_dropped} with no geometry)")
    print(f"boroughs           {boroughs['borough'].nunique():5d} "
          f"covering wards 1-{boroughs['ward'].max()}")

    dead = check_dead_fields(wb)
    for col, info in dead.items():
        print(f"  dead field: {col} = {info['value']!r} for all {len(wb)}")

    joined, boundary_dupes = assign_wards(wb, wards)
    agree = agreement_report(joined)
    print(f"\nspatial vs attribute ward:")
    print(f"  both present     {agree['both_present']:5d}")
    print(f"  disagree         {agree['disagree']:5d}  ({agree['disagree_pct']}%)")
    print(f"  no polygon       {agree['no_polygon_but_attr']:5d}  "
          f"of which {agree['in_wards_142_144']} in wards 142-144")
    print(f"  outside extent   {agree['outside_and_not_142_144']:5d}")
    if boundary_dupes:
        print(f"  boundary double-matches resolved: {boundary_dupes}")

    panel = build_panel(joined, wards, boroughs, electors)
    covered = int((panel["n"] > 0).sum())
    print(f"\npanel  {len(panel)} wards, {covered} with at least one water body, "
          f"{len(panel) - covered} genuine zeros")
    print(f"  total water bodies {int(panel['n'].sum())}, "
          f"total spread {panel['area_ha'].sum():.1f} ha")

    panel.to_csv(K.OUT / "ward_panel.csv", index=False)
    # KMC publishes its borough-to-ward mapping only as a free-text column
    # (`123,124,125,126,142,143 &144`) inside an office-address table. Written
    # out as a clean two-column CSV because it is the only way to place the
    # borough-only amenity tables, and nobody appears to publish one.
    boroughs.sort_values(["ward"]).to_csv(
        K.OUT / "borough_ward_crosswalk.csv", index=False)
    keep = ["ward", "ward_attr", "ward_geo", "area_ha", "in_use", "municipal",
            "water_body_ownership", "waterbody_use", "enumerated",
            "longitude", "latitude", "geometry"]
    pts = joined.copy()
    pts["ward"] = pts["ward_attr"]
    pts[[c for c in keep if c in pts.columns]].to_file(
        K.INTERIM / "water_bodies.gpkg", driver="GPKG", layer="water_bodies")
    wards.to_file(K.INTERIM / "wards.gpkg", driver="GPKG", layer="wards")

    (K.OUT / "join_report.json").write_text(json.dumps({
        "agreement": agree,
        "boundary_double_matches": boundary_dupes,
        "dead_fields": dead,
        "water_bodies_dropped_no_geometry": wb_dropped,
        "ward_polygons_dropped": ward_dropped,
        "enumerated_from": str(wb["enumerated"].min().date()),
        "enumerated_to": str(wb["enumerated"].max().date()),
    }, indent=2))
    print(f"\n-> {K.OUT / 'ward_panel.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
