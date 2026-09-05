"""Export ward geometry + panel data as one JSON payload for the web page."""
import json
import pathlib
import warnings

warnings.filterwarnings("ignore")
import geopandas as gpd
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "out"
CR = 1e7

g = gpd.read_file(RAW / "bbmp_ward_map_2015.kml")
g["ward_no"] = (g["Name"].astype(str).str.replace("\xa0", " ", regex=False)
                .str.extract(r"(\d+)").astype(int))
g = g.to_crs(32643)
g["area_km2"] = g.geometry.area / 1e6
g["geometry"] = g.geometry.simplify(40)          # ~40 m, plenty for a web map

p = pd.read_csv(OUT / "panel_ward.csv")

# Ward population (Census 2011) gives the third denominator. The geography of
# this data depends entirely on which one you pick, so the page offers all three.
cen = pd.read_csv(RAW / "ward_population_2011.csv")
cen.columns = [c.strip() for c in cen.columns]
cen["ward_no"] = pd.to_numeric(cen["Ward Num"], errors="coerce")
cen["pop"] = pd.to_numeric(cen["Population"], errors="coerce")
cen = cen.dropna(subset=["ward_no", "pop"])
cen["ward_no"] = cen["ward_no"].astype(int)

d = g.merge(p, on="ward_no", how="left").merge(
    cen[["ward_no", "pop"]], on="ward_no", how="left")

minx, miny, maxx, maxy = d.total_bounds
W = 1000.0
H = W * (maxy - miny) / (maxx - minx)


def path_of(geom):
    polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    out = []
    for poly in polys:
        for ring in [poly.exterior, *poly.interiors]:
            pts = []
            for c in ring.coords:            # KML rings carry a z value
                x, y = c[0], c[1]
                sx = (x - minx) / (maxx - minx) * W
                sy = H - (y - miny) / (maxy - miny) * H     # flip for SVG
                pts.append(f"{sx:.1f} {sy:.1f}")
            out.append("M" + "L".join(pts) + "Z")
    return "".join(out)


wards = []
for _, r in d.iterrows():
    spend = None if pd.isna(r["spend_total"]) else r["spend_total"] / CR
    pop = None if pd.isna(r.get("pop")) else int(r["pop"])
    comp = None if pd.isna(r["complaints"]) else int(r["complaints"])
    wards.append({
        "no": int(r["ward_no"]),
        "name": r["canonical_name"] if pd.notna(r["canonical_name"]) else f"Ward {int(r['ward_no'])}",
        "area": round(r["area_km2"], 2),
        "spend": None if spend is None else round(spend, 1),
        "comp": comp,
        "spendKm": None if spend is None else round(spend / r["area_km2"], 1),
        "compKm": None if comp is None else round(comp / r["area_km2"]),
        "pop": pop,
        "spendRes": None if (spend is None or not pop) else round(spend * CR / pop),
        "compRes": None if (comp is None or not pop) else round(comp / pop * 1000, 1),
        "res": None if pd.isna(r["resolution_rate"]) else round(r["resolution_rate"] * 100, 1),
        "spc": None if (spend is None or not comp) else round(spend * CR / comp / 1e5, 2),
        "d": path_of(r.geometry),
    })

theme = pd.read_csv(OUT / "panel_ward_category.csv")
have = set(x["no"] for x in wards if x["comp"] is not None)
th = theme[theme["ward_no"].isin(have)].groupby("theme").agg(
    complaints=("complaints", "sum"), spend=("spend", "sum")).reset_index()

dd = p[p["complaints"].notna() & p["spend_total"].notna()].copy()
dd["q"] = pd.qcut(dd["spend_total"], 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
quint = dd.groupby("q", observed=True).agg(
    res=("resolution_rate", "median"), spend=("spend_total", "median")).reset_index()

payload = {
    "viewBox": f"0 0 {W:.0f} {H:.0f}",
    "wards": wards,
    "categories": [
        {"name": t["theme"], "complaints": int(t["complaints"]),
         "spend": round(t["spend"] / CR)} for _, t in th.iterrows()],
    "quintiles": [
        {"q": q["q"], "res": round(q["res"] * 100, 1),
         "spend": round(q["spend"] / CR)} for _, q in quint.iterrows()],
    "scatter": [{"c": int(r["complaints"]), "s": round(r["spend_total"] / CR, 1),
                 "n": r["canonical_name"]} for _, r in dd.iterrows()],
    "totals": {
        "grand": 23241, "ward": 15218, "untagged": 8023,
        "complaints": int(dd["complaints"].sum()),
        "wards": int(len(dd)),
        "pearson": round(dd["complaints"].corr(dd["spend_total"]), 2),
        "spearman": round(dd["complaints"].corr(dd["spend_total"], method="spearman"), 2),
    },
}
dest = OUT / "web_data.json"
dest.write_text(json.dumps(payload, separators=(",", ":")))
print(f"{dest}  {dest.stat().st_size/1024:.0f} KB  "
      f"{len(wards)} wards, viewBox {payload['viewBox']}")
