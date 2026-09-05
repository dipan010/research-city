"""Export ward geometry, slum geometry and the panels as one JSON payload."""
import json
import sys
import warnings

warnings.filterwarnings("ignore")
import geopandas as gpd
import pandas as pd

from mumbai import RAW, OUT, INTERIM, UTM, load_wards, read_kml_polygons

CATS = [
    ("toilet", "Public toilet"), ("bus", "BEST bus stop"),
    ("school", "School (any)"), ("school_municipal", "Municipal school"),
    ("park", "Park or garden"), ("health", "Health centre"),
    ("funeral", "Funeral site"), ("police", "Police station"),
    ("rail", "Suburban station"), ("fire", "Fire station"),
]


def main():
    wards, _ = load_wards()
    wards = wards.to_crs(UTM)
    panel = pd.read_csv(OUT / "ward_panel.csv")
    wards = wards.merge(panel, on="ward", how="left", suffixes=("", "_p"))
    # ~30 m simplification - far below what a screen-width map resolves.
    wards["geometry"] = wards.geometry.simplify(30)

    slums, _ = read_kml_polygons(RAW / "slums.kml")
    slums = slums.to_crs(UTM)
    slums["geometry"] = slums.geometry.simplify(25)

    minx, miny, maxx, maxy = wards.total_bounds
    W = 1000.0
    H = W * (maxy - miny) / (maxx - minx)

    def path_of(geom, prec=1):
        polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        out = []
        for poly in polys:
            if poly.is_empty:
                continue
            for ring in [poly.exterior, *poly.interiors]:
                pts = []
                for c in ring.coords:          # rings carry a z value
                    sx = (c[0] - minx) / (maxx - minx) * W
                    sy = H - (c[1] - miny) / (maxy - miny) * H   # flip for SVG
                    pts.append(f"{sx:.{prec}f} {sy:.{prec}f}")
                if len(pts) > 3:
                    out.append("M" + "L".join(pts) + "Z")
        return "".join(out)

    ward_rows = []
    for _, r in wards.iterrows():
        ward_rows.append({
            "w": r["ward"],
            "pop": int(r["population"]),
            "hh": int(r["households"]),
            "area": round(r["area_km2"], 2),
            "slumShare": round(r["slum_area_share"] * 100, 1),
            "slumKm": round(r["slum_area_km2"], 2),
            "clusters": int(r["slum_clusters"]),
            "seats": int(r["toilet_seats"]),
            "fShare": round(r["female_share"] * 100, 1),
            "pctPub": round(r["pct_public_latrine"], 1),
            "depHH": int(r["hh_public_latrine"]),
            "hhSeat": round(r["hh_per_seat"], 1),
            "seatsKm": round(r["seats_per_km2"]),
            "d": path_of(r.geometry),
        })

    grid = pd.read_csv(INTERIM / "grid_access.csv")
    cluster = pd.read_csv(OUT / "cluster_access.csv")
    base = grid[~grid["slum"]]
    access = []
    for key, lab in CATS:
        # Each service is scored against an inhabited-land proxy it does not
        # itself define, so the comparison is never circular.
        if key == "bus":
            mask = base["near_school"]
        elif key in ("school", "school_municipal"):
            mask = base["near_bus"]
        else:
            mask = base["inhabited"]
        s_ = grid.loc[grid["slum"], f"d_{key}"].median()
        access.append({
            "k": key, "label": lab,
            "slum": round(s_),
            "city": round(base[f"d_{key}"].median()),
            "inhab": round(base[mask][f"d_{key}"].median()),
            "ratioAll": round(s_ / base[f"d_{key}"].median(), 2),
            "ratioInh": round(s_ / base[mask][f"d_{key}"].median(), 2),
            "inside": round((cluster[f"n_{key}"] > 0).mean() * 100, 1),
            "med": round(cluster[f"d_{key}"].median()),
            "p90": round(cluster[f"d_{key}"].quantile(.9)),
        })

    payload = {
        "viewBox": f"0 0 {W:.0f} {H:.0f}",
        "wards": ward_rows,
        "slums": path_of(slums.geometry.union_all(), prec=1),
        "access": access,
        "totals": {
            "clusters": int(len(cluster)),
            "slumKm": round(cluster["area_m2"].sum() / 1e6, 1),
            "cityKm": round(panel["area_km2"].sum(), 1),
            "slumShare": round(cluster["area_m2"].sum() / 1e6
                               / panel["area_km2"].sum() * 100, 1),
            "pop": int(panel["population"].sum()),
            "seats": int(panel["toilet_seats"].sum()),
            "seatsInSlum": int(cluster["toilet_seats"].sum()),
            "seatsInSlumPct": round(cluster["toilet_seats"].sum()
                                    / panel["toilet_seats"].sum() * 100, 1),
            "depHH": int(panel["hh_public_latrine"].sum()),
            "pctPub": round(panel["hh_public_latrine"].sum()
                            / panel["households"].sum() * 100, 1),
            "hhSeat": round(panel["hh_public_latrine"].sum()
                            / panel["toilet_seats"].sum(), 1),
            "fShare": round(panel["toilet_seats_f"].sum()
                            / panel["toilet_seats"].sum() * 100, 1),
            "gridCells": int(len(grid)),
            "gridSlum": int(grid["slum"].sum()),
            "gridInhab": int(base["inhabited"].sum()),
            "gridNonSlum": int(len(base)),
        },
    }
    dest = OUT / "web_data.json"
    dest.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"{dest}  {dest.stat().st_size/1024:.0f} KB  "
          f"{len(ward_rows)} wards, viewBox {payload['viewBox']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
