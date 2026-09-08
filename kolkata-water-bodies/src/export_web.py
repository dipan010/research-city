"""Export ward geometry, water-body points and every result as one JSON payload.

Ward polygons are projected to UTM and written as SVG path strings in a
1000-unit box, so the page draws a real map without shipping a mapping library
or a GeoJSON parser. Water bodies go out as screen coordinates in the same box
for the same reason.

The three wards KMC has but the boundary file does not are exported as a
`missing` list with their water-body counts, so the page can state the gap
rather than quietly drawing 141 polygons and calling it Kolkata.
"""
import json
import sys
import warnings

warnings.filterwarnings("ignore")
import geopandas as gpd                            # noqa: E402
import pandas as pd                                # noqa: E402

import kolkata as K                                # noqa: E402

W = 1000.0


def main() -> int:
    wards = gpd.read_file(K.INTERIM / "wards.gpkg").to_crs(K.UTM)
    wb = gpd.read_file(K.INTERIM / "water_bodies.gpkg").to_crs(K.UTM)
    panel = pd.read_csv(K.OUT / "ward_panel.csv")
    results = json.loads((K.OUT / "results.json").read_text())
    robust = json.loads((K.OUT / "robustness.json").read_text())
    manifest = json.loads((K.RAW / "manifest.json").read_text())

    wards = wards.merge(panel, on="ward", how="left", suffixes=("", "_p"))
    # ~25 m simplification, well below what a screen-width map resolves.
    wards["geometry"] = wards.geometry.simplify(25)

    minx, miny, maxx, maxy = wards.total_bounds
    H = W * (maxy - miny) / (maxx - minx)

    def sx(x):
        return (x - minx) / (maxx - minx) * W

    def sy(y):
        return H - (y - miny) / (maxy - miny) * H   # flip for SVG

    def path_of(geom, prec=1):
        polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        out = []
        for poly in polys:
            if poly.is_empty:
                continue
            for ring in [poly.exterior, *poly.interiors]:
                pts = []
                for c in ring.coords:               # rings carry a z value
                    pts.append(f"{sx(c[0]):.{prec}f} {sy(c[1]):.{prec}f}")
                if len(pts) > 3:
                    out.append("M" + "L".join(pts) + "Z")
        return "".join(out)

    ward_rows = []
    for _, r in wards.iterrows():
        ward_rows.append({
            "ward": int(r["ward"]),
            "borough": r["borough"],
            "d": path_of(r.geometry),
            "n": int(r["n"]),
            "area_ha": round(float(r["area_ha"]), 2),
            "area_km2": round(float(r["area_km2"]), 3),
            "electors": int(r["electors"]),
            "n_disused": int(r["n_disused"]),
            "n_municipal": int(r["n_municipal"]),
            "n_per_km2": round(float(r["n_per_km2"]), 2),
            "area_pct_of_ward": round(float(r["area_pct_of_ward"]), 3),
            "n_per_10k_electors": round(float(r["n_per_10k_electors"]), 2),
            "disused_share": (None if pd.isna(r["disused_share"])
                              else round(float(r["disused_share"]), 4)),
            "municipal_share": (None if pd.isna(r["municipal_share"])
                                else round(float(r["municipal_share"]), 4)),
        })

    pts = []
    for _, r in wb.iterrows():
        pts.append([
            round(sx(r.geometry.x), 1), round(sy(r.geometry.y), 1),
            round(float(r["area_ha"]), 2),
            1 if r["in_use"] else 0,
            1 if r["municipal"] else 0,
        ])

    # The wards the boundary file cannot draw, and what they hold.
    missing = [
        {"ward": w,
         "n": int(panel.loc[panel["ward"] == w, "n"].iloc[0]),
         "area_ha": round(float(panel.loc[panel["ward"] == w, "area_ha"].iloc[0]), 2)}
        for w in K.WARDS_WITHOUT_POLYGON
    ]

    payload = {
        "viewBox": f"0 0 {W:.0f} {H:.0f}",
        "wards": ward_rows,
        "points": pts,
        "missing_wards": missing,
        "results": results,
        "robustness": robust,
        "sources": manifest,
    }
    dest = K.OUT / "web_data.json"
    dest.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"{dest}  {dest.stat().st_size / 1024:.0f} KB  "
          f"({len(ward_rows)} ward polygons, {len(pts)} water bodies, "
          f"{len(missing)} wards with no polygon)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
