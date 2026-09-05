"""Ward choropleths for BBMP spending and complaints.

Uses "BBMP Ward Map - 2015", the only published BBMP ward KML with exactly 198
features - i.e. the same ward regime as the grievance and work-order extracts.
(The file named "BBMP Ward Map - 2022" holds 243 wards and "BBMP Final Wards
Map - 2023" holds 225; neither matches the data used here.)

Kept separate from analyse.py so the rest of the pipeline runs without geopandas.
"""
import pathlib
import re
import sys
import warnings

warnings.filterwarnings("ignore")

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.patches import Patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW, OUT, FIG = (ROOT / "data" / "raw", ROOT / "data" / "out", ROOT / "figures")

WARD_KML = RAW / "bbmp_ward_map_2015.kml"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8880"
SURFACE, MISSING = "#fcfcfb", "#e5e4df"
CR = 1e7

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "text.color": INK, "figure.dpi": 160, "savefig.dpi": 160,
    "savefig.facecolor": SURFACE, "savefig.bbox": "tight",
})


def load_wards() -> gpd.GeoDataFrame:
    if not WARD_KML.exists():
        raise SystemExit(
            f"missing {WARD_KML}\nDownload 'BBMP Ward Map - 2015' (KML) from the "
            "BBMP Ward Information dataset on data.opencity.in into data/raw/.")
    g = gpd.read_file(WARD_KML)
    # Name is "Ward 1" .. "Ward 198", with a non-breaking space.
    g["ward_no"] = (g["Name"].astype(str)
                    .str.replace("\xa0", " ", regex=False)
                    .str.extract(r"(\d+)").astype(float))
    g = g[g["ward_no"].notna()].copy()
    g["ward_no"] = g["ward_no"].astype(int)
    if len(g) != 198:
        print(f"  !! expected 198 ward polygons, got {len(g)}")
    return g


N_BINS = 5


def panel(ax, gdf, col, cmap, title, sub, fmt):
    """Quantile-classified choropleth.

    Ward spending and complaints are both heavily right-skewed, so a linear
    ramp washes out all but the few extreme wards. Equal-count bins show the
    spatial pattern; the legend carries the real value ranges.
    """
    have = gdf[gdf[col].notna()]
    miss = gdf[gdf[col].isna()]

    edges = np.unique(np.quantile(have[col], np.linspace(0, 1, N_BINS + 1)))
    nb = len(edges) - 1
    cm = matplotlib.colormaps[cmap]
    # Assign each ward an explicit bin colour. Passing a BoundaryNorm through
    # GeoDataFrame.plot does not classify reliably, so bin here instead.
    idx = np.clip(np.searchsorted(edges, have[col].to_numpy(), side="right") - 1,
                  0, nb - 1)
    colors = [cm((i + .5) / nb) for i in idx]

    if len(miss):
        miss.plot(ax=ax, color=MISSING, edgecolor=SURFACE, linewidth=.35)
    have.plot(ax=ax, color=colors, edgecolor=SURFACE, linewidth=.35)
    ax.set_axis_off()
    ax.set_title(title, loc="left", fontsize=12.5, fontweight="bold",
                 color=INK, pad=16)
    ax.text(0, 1.005, sub, transform=ax.transAxes, fontsize=9,
            color=MUTED, va="bottom")

    handles = [
        Patch(facecolor=cm((i + .5) / nb), edgecolor=SURFACE,
              label=f"{fmt(edges[i])} - {fmt(edges[i + 1])}")
        for i in range(nb)
    ]
    if len(miss):
        handles.append(Patch(facecolor=MISSING, edgecolor=SURFACE,
                             label="no data"))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(.5, -.01),
              ncol=3, frameon=False, fontsize=8.5, handlelength=1.1,
              handleheight=1.1, columnspacing=1.4, labelcolor=INK2)


def main() -> int:
    FIG.mkdir(exist_ok=True)
    g = load_wards()
    p = pd.read_csv(OUT / "panel_ward.csv")
    gdf = g.merge(p, on="ward_no", how="left")
    print(f"ward polygons {len(g)} | joined to panel rows "
          f"{gdf['spend_total'].notna().sum()}")

    gdf["spend_cr"] = gdf["spend_total"] / CR
    # Ward area, in an equal-area projection - BBMP's outer wards are many
    # times larger than its core wards, which drives the raw-total pattern.
    gdf["area_km2"] = gdf.to_crs(32643).geometry.area / 1e6
    gdf["spend_per_km2"] = gdf["spend_cr"] / gdf["area_km2"]
    gdf["compl_per_km2"] = gdf["complaints"] / gdf["area_km2"]
    print(f"ward area km2: inner-quartile median "
          f"{gdf['area_km2'].quantile(.25):.1f}, "
          f"outer {gdf['area_km2'].quantile(.75):.1f}")

    fig, axes = plt.subplots(2, 2, figsize=(13, 13.4))
    panel(axes[0][0], gdf, "spend_cr", "Blues",
          "Work-order spending, total",
          "Gross work orders 2018-23, Rs crore per ward",
          lambda v: f"{v:,.0f}")
    panel(axes[0][1], gdf, "complaints", "Blues",
          "Citizen complaints, total",
          "Grievances lodged 2020-24, per ward",
          lambda v: f"{v:,.0f}")
    panel(axes[1][0], gdf, "spend_per_km2", "Blues",
          "Work-order spending, per sq km",
          "Rs crore per square kilometre",
          lambda v: f"{v:,.0f}")
    panel(axes[1][1], gdf, "compl_per_km2", "Blues",
          "Citizen complaints, per sq km",
          "Complaints per square kilometre",
          lambda v: f"{v:,.0f}")
    fig.suptitle("Both patterns invert once you divide by ward area",
                 x=0.005, y=1.005, ha="left", fontsize=14.5,
                 fontweight="bold", color=INK)
    fig.text(0.005, 0.978,
             "Top row: raw totals rise toward the periphery. But BBMP's outer "
             "wards are several times larger than its core wards, so the totals "
             "mostly track ward size.\nBottom row: per square kilometre, the "
             "old core is denser in both spending and complaints. "
             "Quantile bins; each map has its own scale.",
             ha="left", fontsize=9.5, color=MUTED, va="top")
    dest = FIG / "fig5_ward_maps.png"
    fig.savefig(dest)
    plt.close(fig)
    print(f"-> {dest}")

    # spend per complaint - where money and demand diverge most
    gdf["spc"] = gdf["spend_total"] / gdf["complaints"] / 1e5  # Rs lakh
    fig, ax = plt.subplots(figsize=(7.4, 7.0))
    panel(ax, gdf, "spc", "Blues",
          "Rupees spent per complaint lodged",
          "Work-order spend 2018-23 divided by complaints 2020-24, "
          "Rs lakh per complaint",
          lambda v: f"{v:,.1f}")
    dest2 = FIG / "fig6_spend_per_complaint.png"
    fig.savefig(dest2)
    plt.close(fig)
    print(f"-> {dest2}")

    d = gdf.dropna(subset=["spc"])
    print("\nhighest spend per complaint:")
    for _, r in d.nlargest(5, "spc").iterrows():
        print(f"  {r['canonical_name']:<26} Rs {r['spc']:5.1f} lakh/complaint")
    print("lowest spend per complaint:")
    for _, r in d.nsmallest(5, "spc").iterrows():
        print(f"  {r['canonical_name']:<26} Rs {r['spc']:5.1f} lakh/complaint")
    print(f"\nratio highest:lowest = "
          f"{d['spc'].max() / d['spc'].min():.0f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
