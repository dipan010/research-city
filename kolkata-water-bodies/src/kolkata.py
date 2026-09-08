"""Shared loading utilities: KML parsing, ward geometry, denominators.

Kept in one place because every build step needs the same handful of things,
and because the traps these functions exist to defuse are silent when got
wrong. Three specific to Kolkata:

  * The ward KML is the **pre-2015, 141-ward** boundary set despite being named
    "Kolkata Wards Map 2022". KMC has had 144 wards since the 2015 poll, when
    the Joka area was annexed into Borough XVI. `load_wards()` asserts 141 and
    names the three it does not hold, rather than letting a caller assume the
    file matches the corporation.
  * 68 water bodies sit in wards 142-144, which therefore have no polygon to
    land in. `WARDS_WITHOUT_POLYGON` exists so that loss is reported, not
    silently dropped by a spatial join.
  * KML rings carry a z coordinate, so unpacking a coordinate tuple as `x, y`
    raises. `_coords` splits to at most three and keeps the first two.
"""
import pathlib
import re
import xml.etree.ElementTree as ET

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Point, Polygon

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "data" / "out"

KNS = "{http://www.opengis.net/kml/2.2}"

# WGS84 for the source files; UTM 45N for anything measured in metres or
# hectares. Kolkata sits at ~88.4E, inside zone 45N's 84-90E band - checked
# against the water bodies file's own longitude range (88.244 to 88.458),
# not assumed.
WGS84 = "EPSG:4326"
UTM = "EPSG:32645"

# KMC's formal ward count since the 2015 election.
N_WARDS_KMC = 144
# What the published boundary file actually holds.
N_WARDS_KML = 141
WARDS_WITHOUT_POLYGON = (142, 143, 144)


# --------------------------------------------------------------------------
# KML parsing
# --------------------------------------------------------------------------
def _coords(text):
    """Parse a KML <coordinates> blob into (lon, lat) pairs."""
    pts = []
    for tok in text.split():
        parts = tok.split(",")
        if len(parts) >= 2:
            pts.append((float(parts[0]), float(parts[1])))
    return pts


def _placemark_fields(pm):
    """Attribute dict for a placemark: SimpleData, Data, plus <name>."""
    d = {}
    for sd in pm.iter(f"{KNS}SimpleData"):
        name = sd.get("name")
        if name:
            d[name] = (sd.text or "").strip()
    for dat in pm.iter(f"{KNS}Data"):
        name = dat.get("name")
        val = dat.find(f"{KNS}value")
        if name and val is not None:
            d.setdefault(name, (val.text or "").strip())
    nm = pm.find(f"{KNS}name")
    if nm is not None and nm.text:
        d.setdefault("_name", nm.text.strip())
    return d


def _polygons(pm):
    out = []
    for poly in pm.iter(f"{KNS}Polygon"):
        outer = poly.find(f".//{KNS}outerBoundaryIs//{KNS}coordinates")
        if outer is None or not outer.text:
            continue
        shell = _coords(outer.text)
        if len(shell) < 4:
            continue
        holes = []
        for inner in poly.findall(f".//{KNS}innerBoundaryIs//{KNS}coordinates"):
            ring = _coords(inner.text or "")
            if len(ring) >= 4:
                holes.append(ring)
        try:
            g = Polygon(shell, holes)
            if not g.is_valid:
                g = g.buffer(0)
            if not g.is_empty:
                out.append(g)
        except Exception:                          # noqa: BLE001
            continue
    return out


def read_kml_points(path, name=None):
    """Every <Point> placemark in a KML as a GeoDataFrame, plus a drop count.

    `dropped` counts placemarks carrying no point, so the caller can report the
    loss instead of silently analysing fewer features than the file holds.
    """
    root = ET.parse(path).getroot()
    rows, geoms, dropped = [], [], 0
    for pm in root.iter(f"{KNS}Placemark"):
        pts = []
        for p in pm.iter(f"{KNS}Point"):
            c = p.find(f"{KNS}coordinates")
            if c is not None and c.text:
                pts += _coords(c.text)
        if not pts:
            dropped += 1
            continue
        fields = _placemark_fields(pm)
        lon, lat = pts[0]
        rows.append(fields)
        geoms.append(Point(lon, lat))
    gdf = gpd.GeoDataFrame(rows, geometry=geoms, crs=WGS84)
    gdf["layer"] = name or pathlib.Path(path).stem
    return gdf, dropped


def read_kml_polygons(path, name=None):
    """Every polygon placemark in a KML, dissolved per placemark."""
    root = ET.parse(path).getroot()
    rows, geoms, dropped = [], [], 0
    for pm in root.iter(f"{KNS}Placemark"):
        polys = _polygons(pm)
        if not polys:
            dropped += 1
            continue
        if len(polys) == 1:
            g = polys[0]
        else:
            g = MultiPolygon([
                p for poly in polys
                for p in (poly.geoms if isinstance(poly, MultiPolygon) else [poly])
            ])
        rows.append(_placemark_fields(pm))
        geoms.append(g)
    gdf = gpd.GeoDataFrame(rows, geometry=geoms, crs=WGS84)
    gdf["layer"] = name or pathlib.Path(path).stem
    return gdf, dropped


# --------------------------------------------------------------------------
# Ward identity
# --------------------------------------------------------------------------
def ward_num(value):
    """Parse a KMC ward number from a label, or None.

    Kolkata's ward identifiers are numeric, so this is far less hazardous than
    Mumbai's four-way spellings - but the same rule applies: return None rather
    than guess, and range-check against KMC's 144 so a stray code cannot be
    mistaken for a ward.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    m = re.search(r"\d+", str(value))
    if not m:
        return None
    n = int(m.group())
    return n if 1 <= n <= N_WARDS_KMC else None


def ward_from_village(value):
    """Ward number out of the water census `village` field.

    The census stores the ward inside a village label, e.g.
    `KOLKATA (M CORP.) WARD NO.-0108`. Matched strictly on that pattern so a
    label of another shape returns None instead of yielding whatever digits it
    happens to contain.
    """
    if value is None:
        return None
    m = re.search(r"WARD\s*NO\.?-\s*(\d+)", str(value).upper())
    return ward_num(m.group(1)) if m else None


def load_wards():
    """KMC ward polygons from the published KML, with area in km2.

    Returns (gdf, dropped). Asserts the count the file actually holds rather
    than the count KMC has, and leaves the caller to handle the difference.
    """
    g, dropped = read_kml_polygons(RAW / "wards.kml", "wards")
    src = "WARD" if "WARD" in g.columns else "_name"
    g["ward"] = g[src].map(ward_num)
    missing = int(g["ward"].isna().sum())
    if missing:
        raise SystemExit(f"{missing} ward polygons carry no usable ward number")
    if g["ward"].duplicated().any():
        dupes = sorted(g.loc[g["ward"].duplicated(), "ward"])
        raise SystemExit(f"duplicate ward polygons: {dupes}")
    g = g[["ward", "geometry"]].sort_values("ward").reset_index(drop=True)
    if len(g) != N_WARDS_KML:
        raise SystemExit(
            f"expected {N_WARDS_KML} ward polygons in the published KML, "
            f"got {len(g)} - re-check the file vintage before continuing")
    absent = tuple(w for w in range(1, N_WARDS_KMC + 1)
                   if w not in set(g["ward"]))
    if absent != WARDS_WITHOUT_POLYGON:
        raise SystemExit(
            f"expected wards {WARDS_WITHOUT_POLYGON} to be the absent ones, "
            f"got {absent}")
    g["area_km2"] = g.to_crs(UTM).area / 1e6
    return g, dropped


def load_boroughs():
    """Borough -> ward lookup from `KMC Borough Committees Office`.

    KMC's only published crosswalk between its 16 boroughs and its 144 wards,
    and the only way to place the borough-only amenity tables. The ward list is
    free text (`123,124,125,126,142,143 &144`), so it is parsed and then
    checked to cover 1-144 exactly once.
    """
    df = pd.read_csv(RAW / "boroughs.csv", dtype=str)
    rows = []
    for _, r in df.iterrows():
        borough = str(r["Borough Committee"]).strip()
        for tok in re.split(r"[,&]", str(r["Wards"])):
            n = ward_num(tok)
            if n is not None:
                rows.append({"borough": borough, "ward": n})
    out = pd.DataFrame(rows)
    covered = sorted(out["ward"])
    expected = list(range(1, N_WARDS_KMC + 1))
    if covered != expected:
        dupes = sorted({w for w in covered if covered.count(w) > 1})
        gaps = [w for w in expected if w not in set(covered)]
        raise SystemExit(
            f"borough table does not partition 1-{N_WARDS_KMC}: "
            f"duplicates {dupes}, gaps {gaps}")
    return out


def load_electorate():
    """Registered electors per ward from the 2015 KMC election.

    The only complete per-ward denominator KMC publishes that is not sourced
    from Kolkata *district*, which is smaller than KMC's jurisdiction. It is an
    electorate rather than a population and it is a decade old; both are stated
    wherever it is used as a divisor.

    The file is candidate-level, so electors repeat across every candidate in a
    ward. Taking `max` per ward rather than `first` guards against a blank on
    any single row.
    """
    df = pd.read_csv(RAW / "election_2015.csv", dtype=str, low_memory=False)
    df["ward"] = df["Ward_No"].map(ward_num)
    df["electors"] = pd.to_numeric(
        df["Total_Electors"].astype(str).str.replace(",", "", regex=False),
        errors="coerce")
    out = (df.dropna(subset=["ward"])
             .groupby("ward", as_index=False)["electors"].max())
    out["ward"] = out["ward"].astype(int)
    if len(out) != N_WARDS_KMC:
        raise SystemExit(
            f"expected {N_WARDS_KMC} wards in the 2015 election file, "
            f"got {len(out)}")
    if out["electors"].isna().any():
        bad = sorted(out.loc[out["electors"].isna(), "ward"])
        raise SystemExit(f"wards with no elector count: {bad}")
    return out
