"""Ward choropleths and the slum-cluster map.

Kept separate from analyse.py so the rest of the pipeline runs without a
geospatial stack, the same split the sibling BBMP project uses.
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from mumbai import RAW, OUT, UTM, load_wards, read_kml_polygons, read_kml_points

ROOT = OUT.parents[1]
FIG = ROOT / "figures"

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8880"
SURFACE, NODATA = "#fcfcfb", "#d8d6d0"
C_SLUM = "#2a78d6"
# Single-hue sequential ramp, light -> dark, matching the web page's r1..r5.
RAMP = LinearSegmentedColormap.from_list(
    "blues", ["#e8f0fa", "#b0cdeb", "#7fb0dd", "#4d8ecb", "#1f5fae"])

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "text.color": INK, "figure.dpi": 160, "savefig.dpi": 160,
    "savefig.facecolor": SURFACE, "savefig.bbox": "tight",
})


def panel(ax, wards, col, title, sub, fmt=lambda v: f"{v:,.0f}"):
    wards.plot(ax=ax, column=col, cmap=RAMP, edgecolor="white", linewidth=.7,
               missing_kwds={"color": NODATA})
    ax.set_axis_off()
    ax.set_title(title, loc="left", fontsize=11.5, fontweight="bold",
                 color=INK, pad=16)
    ax.text(0, 1.005, sub, transform=ax.transAxes, fontsize=8.6,
            color=MUTED, va="bottom")
    lo, hi = wards[col].min(), wards[col].max()
    ax.text(0.02, 0.02, f"{fmt(lo)}  -  {fmt(hi)}", transform=ax.transAxes,
            fontsize=8.4, color=MUTED)
    # Label the extremes only - a number on all 24 wards is unreadable here.
    for _, r in wards.loc[[wards[col].idxmin(), wards[col].idxmax()]].iterrows():
        c = r.geometry.representative_point()
        ax.annotate(r["ward"], (c.x, c.y), ha="center", va="center",
                    fontsize=8, fontweight="bold", color=INK,
                    bbox=dict(boxstyle="round,pad=0.18", fc=SURFACE,
                              ec="none", alpha=.85))


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    wards, _ = load_wards()
    wards = wards.to_crs(UTM)
    panel_df = pd.read_csv(OUT / "ward_panel.csv")
    wards = wards.merge(panel_df, on="ward", how="left", suffixes=("", "_p"))

    slums, _ = read_kml_polygons(RAW / "slums.kml")
    slums = slums.to_crs(UTM)

    # --- fig 6: where the slums are, and where the toilets are -----------
    toilets, _ = read_kml_points(RAW / "toilets.kml")
    toilets = toilets.to_crs(UTM)
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 8.2))
    for ax in axes:
        wards.plot(ax=ax, color="#f0eeea", edgecolor="white", linewidth=.7)
        ax.set_axis_off()
    slums.plot(ax=axes[0], color=C_SLUM, edgecolor="none")
    axes[0].set_title("Slum clusters", loc="left", fontsize=11.5,
                      fontweight="bold", color=INK, pad=16)
    axes[0].text(0, 1.005, f"{len(slums):,} polygons, "
                 f"{slums.area.sum()/1e6:.1f} km2 - 7.1% of the city's land",
                 transform=axes[0].transAxes, fontsize=8.6, color=MUTED,
                 va="bottom")
    toilets.plot(ax=axes[1], color=C_SLUM, markersize=1.1, alpha=.55)
    axes[1].set_title("Public toilet blocks", loc="left", fontsize=11.5,
                      fontweight="bold", color=INK, pad=16)
    axes[1].text(0, 1.005, f"{len(toilets):,} points, "
                 f"{int(panel_df['toilet_seats'].sum()):,} seats - "
                 "51.5% of them inside a slum cluster",
                 transform=axes[1].transAxes, fontsize=8.6, color=MUTED,
                 va="bottom")
    fig.tight_layout()
    fig.savefig(FIG / "fig6_slums_and_toilets.png")
    plt.close(fig)

    # --- fig 7: three ward choropleths -----------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(13.4, 6.6))
    panel(axes[0], wards, "slum_area_share",
          "Slum share of ward land",
          "share of ward area inside a slum cluster",
          lambda v: f"{v:.1%}")
    panel(axes[1], wards, "pct_public_latrine",
          "Households depending on a public latrine",
          "Census 2011, household-weighted", lambda v: f"{v:.0f}%")
    panel(axes[2], wards, "hh_per_seat",
          "Households per toilet seat",
          "dependent households / seats on BMC's layer",
          lambda v: f"{v:.0f}")
    fig.tight_layout()
    fig.savefig(FIG / "fig7_ward_maps.png")
    plt.close(fig)

    print(f"figures -> {FIG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
