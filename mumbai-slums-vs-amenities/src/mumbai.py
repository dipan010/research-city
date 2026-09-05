"""Shared loading utilities: KML parsing, ward labels, projections.

Kept in one place because every build step needs the same three things, and
because the two traps these functions exist to defuse - placemarks that carry
no geometry, and ward labels spelled four different ways - are silent when got
wrong. Both are counted and reported rather than dropped.
"""
import pathlib
import re
import xml.etree.ElementTree as ET

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPolygon

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "data" / "out"

KNS = "{http://www.opengis.net/kml/2.2}"

# WGS84 for the source files; UTM 43N for anything measured in metres.
# Mumbai sits at ~72.8E, inside zone 43N's 72-78E band - checked, not assumed.
WGS84 = "EPSG:4326"
UTM = "EPSG:32643"

# BMC's 24 administrative wards, in the spelling the ward KML uses.
CANONICAL_WARDS = [
    "A", "B", "C", "D", "E", "F/N", "F/S", "G/N", "G/S", "H/E", "H/W",
    "K/E", "K/W", "L", "M/E", "M/W", "N", "P/N", "P/S", "R/C", "R/N",
    "R/S", "S", "T",
]


def norm_ward(label):
    """Normalise a ward label to BMC's canonical form, or None.

    The layers spell the same 24 wards inconsistently - the toilet layer says
    `KE`, the ward map says `K/E`, others use `K-E`, `K/ E` or lowercase. This
    maps every variant onto the canonical list by exact lookup after stripping
    separators; anything that does not land on a real ward returns None rather
    than being guessed at.
    """
    if label is None or (isinstance(label, float) and pd.isna(label)):
        return None
    key = re.sub(r"[^A-Z]", "", str(label).upper())
    if not key:
        return None
    lookup = {re.sub(r"[^A-Z]", "", w): w for w in CANONICAL_WARDS}
    return lookup.get(key)


def _coords(text):
    """Parse a KML <coordinates> blob into (lon, lat) pairs.

    KML tuples carry a third z value, so unpacking as `x, y` raises - split to
    at most three and keep the first two.
    """
    pts = []
    for tok in text.split():
        parts = tok.split(",")
        if len(parts) >= 2:
            pts.append((float(parts[0]), float(parts[1])))
    return pts


def _placemark_fields(pm):
    """Attribute dict for a placemark: SimpleData plus <name>."""
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
    """Every <Point> placemark in a KML, as a GeoDataFrame in WGS84.

    Returns (gdf, dropped) - `dropped` counts placemarks carrying no point, so
    the caller can report the loss instead of silently analysing fewer
    features than the file claims to hold.
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
        for lon, lat in pts[:1]:                   # one point per placemark
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
        g = polys[0] if len(polys) == 1 else MultiPolygon(
            [p for poly in polys for p in
             (poly.geoms if isinstance(poly, MultiPolygon) else [poly])])
        rows.append(_placemark_fields(pm))
        geoms.append(g)
    gdf = gpd.GeoDataFrame(rows, geometry=geoms, crs=WGS84)
    gdf["layer"] = name or pathlib.Path(path).stem
    return gdf, dropped


def ward_attr(gdf):
    """Pull whatever column a layer used for its ward label.

    Layers disagree: `Ward`, `WARD`, `Ward_s`. Take the first that exists and
    normalise it; the spatial join is what actually assigns wards, this is
    only kept so the two can be compared.
    """
    for col in ("Ward", "WARD", "Ward_s", "ward"):
        if col in gdf.columns:
            return gdf[col].map(norm_ward)
    return pd.Series([None] * len(gdf), index=gdf.index, dtype=object)


def load_wards():
    """The 24 BMC ward polygons, with area in km2."""
    g, dropped = read_kml_polygons(RAW / "wards.kml", "wards")
    g["ward"] = g["NAME"].map(norm_ward) if "NAME" in g.columns else g["_name"].map(norm_ward)
    missing = g["ward"].isna().sum()
    if missing:
        raise SystemExit(f"{missing} ward polygons did not map to a canonical ward")
    g = g.dissolve(by="ward", as_index=False)[["ward", "geometry"]]
    g["area_km2"] = g.to_crs(UTM).area / 1e6
    if len(g) != 24:
        raise SystemExit(f"expected 24 wards, got {len(g)}")
    return g, dropped
