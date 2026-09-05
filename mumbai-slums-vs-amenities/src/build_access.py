"""Spatial build: slum clusters, amenity layers, and distance to service.

Three tables come out of this:

  cluster_access.csv  one row per slum polygon (n=2,542) - the unit that
                      actually carries statistical weight
  grid_access.csv     a 100 m lattice over Greater Mumbai, tagged slum /
                      non-slum, so slum access can be compared against the
                      rest of the city on equal area terms. Written to
                      data/interim - it is 9 MB and fully regenerable, so it
                      is an input to the analysis rather than an output of it
  ward_amenities.csv  per-ward counts and toilet seats, for the map and table

Wards are assigned by spatial join, never by the layers' own ward attribute -
geometry is what is being analysed. The attribute is kept alongside and the
disagreement rate is reported, because that rate is itself a finding about the
data.
"""
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

from mumbai import (RAW, OUT, INTERIM, UTM, WGS84, load_wards, read_kml_points,
                    read_kml_polygons, ward_attr)

# Amenity layers, grouped into the service categories the analysis reports.
LAYERS = {
    "toilet":   ["toilets.kml"],
    "health":   ["health_dispensaries.kml", "health_uphc.kml",
                 "health_hospitals.kml", "health_maternity.kml"],
    "school":   ["schools_municipal.kml", "schools_aided.kml",
                 "schools_unaided.kml"],
    "school_municipal": ["schools_municipal.kml"],
    "park":     ["parks.kml"],
    "fire":     ["fire_stations.kml"],
    "police":   ["police_stations.kml"],
    "bus":      ["best_stops.kml"],
    "rail":     ["rail_stations.kml"],
    "funeral":  ["funeral_sites.kml"],
}

GRID_M = 100          # lattice spacing, metres


def load_amenities(wards_utm):
    """Every amenity point, ward-joined spatially, with the attribute check."""
    frames, report = {}, []
    for cat, files in LAYERS.items():
        parts = []
        for f in files:
            g, dropped = read_kml_points(RAW / f, f)
            g["ward_attr"] = ward_attr(g)
            parts.append(g)
            # school_municipal re-reads a file already counted under school;
            # record each file once so the report does not double-count it.
            if not any(r["file"] == f for r in report):
                report.append({"file": f, "category": cat, "points": len(g),
                               "placemarks_no_geometry": dropped})
        g = pd.concat(parts, ignore_index=True)
        g = gpd.GeoDataFrame(g, geometry="geometry", crs=WGS84).to_crs(UTM)
        # Spatial ward assignment - the authoritative one.
        g = gpd.sjoin(g, wards_utm[["ward", "geometry"]],
                      how="left", predicate="within").drop(columns="index_right")
        frames[cat] = g
    return frames, pd.DataFrame(report)


def toilet_seats(g):
    """Male and female seat counts on the public-toilet layer."""
    def num(col):
        if col not in g.columns:
            return pd.Series(0.0, index=g.index)
        return pd.to_numeric(
            g[col].astype(str).str.replace(",", "", regex=False),
            errors="coerce").fillna(0.0)
    m, f = num("Count_of_M"), num("Count_of_F")
    return m, f


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wards, ward_drop = load_wards()
    wards_utm = wards.to_crs(UTM)
    print(f"wards   : {len(wards)}  {wards['area_km2'].sum():.1f} km2 total"
          f"  ({ward_drop} placemarks without polygon)")

    # ---- slum clusters -------------------------------------------------
    slums, slum_drop = read_kml_polygons(RAW / "slums.kml", "slums")
    slums = slums.to_crs(UTM)
    slums["cluster_id"] = range(len(slums))
    slums["area_m2"] = slums.area
    print(f"slums   : {len(slums)} polygons "
          f"({slum_drop} placemarks without polygon)")

    # Duplicate and overlap hygiene - double-counted area is the summary-row
    # trap in spatial form, so check before summing anything.
    wkb = slums.geometry.apply(lambda g: g.wkb)
    dupes = int(wkb.duplicated().sum())
    raw_area = slums["area_m2"].sum() / 1e6
    union_area = slums.geometry.union_all().area / 1e6
    print(f"          duplicate geometries : {dupes}")
    print(f"          area summed          : {raw_area:.2f} km2")
    print(f"          area of union        : {union_area:.2f} km2 "
          f"(overlap {raw_area - union_area:.2f} km2, "
          f"{(raw_area - union_area) / raw_area:.1%})")

    # Ward by largest overlap, since clusters can straddle a ward boundary.
    ov = gpd.overlay(slums[["cluster_id", "geometry"]],
                     wards_utm[["ward", "geometry"]], how="intersection")
    ov["ov_area"] = ov.area
    best = ov.sort_values("ov_area").groupby("cluster_id").tail(1)
    slums = slums.merge(best[["cluster_id", "ward"]], on="cluster_id", how="left")
    outside = int(slums["ward"].isna().sum())
    print(f"          clusters outside every ward polygon: {outside}")

    # ---- amenities -----------------------------------------------------
    frames, report = load_amenities(wards_utm)
    print("\nlayer                       points  no-geom  ward attr disagrees")
    for cat, g in frames.items():
        if cat == "school_municipal":
            continue
        both = g.dropna(subset=["ward", "ward_attr"])
        dis = (both["ward"] != both["ward_attr"]).mean() if len(both) else np.nan
        nog = int(report[report["category"] == cat]["placemarks_no_geometry"].sum())
        miss = int(g["ward_attr"].isna().sum())
        print(f"  {cat:12s} {len(g):9d} {nog:8d} "
              f"{'':6s}{dis:6.1%} of {len(both)} labelled"
              f"{'' if not miss else f'  ({miss} unlabelled)'}")
    report.to_csv(OUT / "layer_report.csv", index=False)

    # ---- cluster-level access -----------------------------------------
    # Polygon-to-point distance, so a large cluster is not judged by how far
    # its centroid sits from a toilet that stands at its edge. Distance is 0
    # when the amenity falls inside the cluster.
    acc = slums[["cluster_id", "ward", "area_m2", "geometry"]].copy()
    for cat, g in frames.items():
        pts = g[["geometry"]].reset_index(drop=True)
        near = gpd.sjoin_nearest(acc[["cluster_id", "geometry"]], pts,
                                 how="left", distance_col=f"d_{cat}")
        near = near.groupby("cluster_id")[f"d_{cat}"].min()
        acc[f"d_{cat}"] = acc["cluster_id"].map(near)
        # Count of amenities falling inside the cluster.
        inside = gpd.sjoin(pts, acc[["cluster_id", "geometry"]],
                           how="inner", predicate="within")
        acc[f"n_{cat}"] = acc["cluster_id"].map(
            inside.groupby("cluster_id").size()).fillna(0).astype(int)

    # Toilet seats inside each cluster.
    tg = frames["toilet"].copy()
    m, f = toilet_seats(tg)
    tg["seats"] = m + f
    tg["seats_f"] = f
    ins = gpd.sjoin(tg[["seats", "seats_f", "geometry"]],
                    acc[["cluster_id", "geometry"]],
                    how="inner", predicate="within")
    acc["toilet_seats"] = acc["cluster_id"].map(
        ins.groupby("cluster_id")["seats"].sum()).fillna(0)
    acc["toilet_seats_f"] = acc["cluster_id"].map(
        ins.groupby("cluster_id")["seats_f"].sum()).fillna(0)

    acc.drop(columns="geometry").to_csv(OUT / "cluster_access.csv", index=False)
    print(f"\n-> {OUT/'cluster_access.csv'}  ({len(acc)} clusters)")

    # ---- grid comparison -----------------------------------------------
    # A 100 m lattice over the city, tagged slum / non-slum. This is what
    # makes "further from services" a comparison rather than a bare number:
    # slum land and the rest of the city are measured the same way, on equal
    # area terms. It needs no population estimate, which is the point - there
    # is no published slum population to use.
    minx, miny, maxx, maxy = wards_utm.total_bounds
    xs = np.arange(minx + GRID_M / 2, maxx, GRID_M)
    ys = np.arange(miny + GRID_M / 2, maxy, GRID_M)
    xx, yy = np.meshgrid(xs, ys)
    grid = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xx.ravel(), yy.ravel()),
                            crs=UTM)
    grid = gpd.sjoin(grid, wards_utm[["ward", "geometry"]],
                     how="inner", predicate="within").drop(columns="index_right")
    grid = grid.reset_index(drop=True)
    grid["cell_id"] = range(len(grid))
    slum_union = gpd.GeoDataFrame(
        geometry=[slums.geometry.union_all()], crs=UTM)
    in_slum = gpd.sjoin(grid[["cell_id", "geometry"]], slum_union,
                        how="inner", predicate="within")
    grid["slum"] = grid["cell_id"].isin(in_slum["cell_id"])
    print(f"\ngrid    : {len(grid):,} cells at {GRID_M} m "
          f"({grid['slum'].sum():,} slum, {(~grid['slum']).sum():,} non-slum)")

    for cat, g in frames.items():
        pts = g[["geometry"]].reset_index(drop=True)
        near = gpd.sjoin_nearest(grid[["cell_id", "geometry"]], pts,
                                 how="left", distance_col=f"d_{cat}")
        grid[f"d_{cat}"] = grid["cell_id"].map(
            near.groupby("cell_id")[f"d_{cat}"].min())

    INTERIM.mkdir(parents=True, exist_ok=True)
    # "Inhabited" proxy. Comparing slum land against ALL non-slum land is
    # unfair to the city: that baseline includes the national park, mangroves,
    # salt pans, creeks and the airport, none of which have services near them
    # and none of which contain slums. A cell is treated as inhabited if it is
    # within 300 m of a BEST stop or 400 m of a school - two dense layers that
    # between them trace where people actually live. Each service is compared
    # against a proxy it does not itself define; the bus and school rows are
    # circular on their own proxy and are reported on the other.
    grid["near_bus"] = grid["d_bus"] <= 300
    grid["near_school"] = grid["d_school"] <= 400
    grid["inhabited"] = grid["near_bus"] | grid["near_school"]
    inh = grid[~grid["slum"]]["inhabited"].sum()
    print(f"          non-slum cells treated as inhabited: {inh:,} of "
          f"{(~grid['slum']).sum():,} ({inh/(~grid['slum']).sum():.0%})")

    grid.drop(columns="geometry").to_csv(INTERIM / "grid_access.csv", index=False)
    print(f"-> {INTERIM/'grid_access.csv'}  ({len(grid)} cells)")

    # ---- ward table ----------------------------------------------------
    w = wards[["ward", "area_km2"]].copy()
    for cat, g in frames.items():
        w[f"n_{cat}"] = w["ward"].map(
            g.groupby("ward").size()).fillna(0).astype(int)
    tg2 = frames["toilet"].copy()
    m, f = toilet_seats(tg2)
    tg2["seats"], tg2["seats_f"] = m + f, f
    w["toilet_seats"] = w["ward"].map(
        tg2.groupby("ward")["seats"].sum()).fillna(0)
    w["toilet_seats_f"] = w["ward"].map(
        tg2.groupby("ward")["seats_f"].sum()).fillna(0)
    sl = slums.dropna(subset=["ward"])
    w["slum_area_km2"] = w["ward"].map(
        sl.groupby("ward")["area_m2"].sum() / 1e6).fillna(0)
    w["slum_clusters"] = w["ward"].map(
        sl.groupby("ward").size()).fillna(0).astype(int)
    w["slum_area_share"] = w["slum_area_km2"] / w["area_km2"]

    cen = pd.read_csv(OUT / "ward_census.csv")
    w = w.merge(cen, on="ward", how="left")
    # Households dependent on a public latrine - a measured demand
    # denominator, not an estimated slum population.
    w["hh_public_latrine"] = w["households"] * w["pct_public_latrine"] / 100

    w.to_csv(OUT / "ward_amenities.csv", index=False)
    print(f"-> {OUT/'ward_amenities.csv'}  ({len(w)} wards)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
