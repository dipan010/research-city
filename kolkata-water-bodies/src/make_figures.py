"""Static figures for the write-up.

Kept deliberately plain: one idea per figure, no chartjunk, and every axis
names its denominator. The choropleths draw the 141 published ward polygons and
hatch the three wards KMC has but the boundary file does not, so the gap is
visible on the map rather than only in the prose.
"""
import json
import sys

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt                    # noqa: E402
from matplotlib.lines import Line2D                # noqa: E402

import kolkata as K                                # noqa: E402

FIG = K.ROOT / "figures"
INK = "#1b1b1b"
MUTED = "#6b6b6b"
GRID = "#e3e3e3"
WATER = "#2a6f8f"
WARM = "#c2562f"
SAND = "#d9c9a3"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})


def load():
    panel = pd.read_csv(K.OUT / "ward_panel.csv")
    wards = gpd.read_file(K.INTERIM / "wards.gpkg")
    wb = gpd.read_file(K.INTERIM / "water_bodies.gpkg")
    return panel, wards.merge(panel, on="ward", how="left"), wb


def _choropleth(ax, g, col, title, cmap, label, log=False):
    vals = g[col]
    kw = {}
    if log:
        kw["norm"] = matplotlib.colors.SymLogNorm(
            linthresh=1, vmin=0, vmax=float(vals.max()))
    g.plot(ax=ax, column=col, cmap=cmap, linewidth=0.25,
           edgecolor="white", legend=True,
           legend_kwds={"label": label, "shrink": 0.62}, **kw)
    ax.set_title(title, fontsize=10, loc="left", pad=8)
    ax.set_axis_off()


def fig1_distribution(panel, wb):
    """How the stock is spread, and how small the bodies are."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))

    ax = axes[0]
    counts = np.sort(panel["n"].values)[::-1]
    ax.bar(range(1, len(counts) + 1), counts, color=WATER, width=1.0)
    ax.set_xlabel("wards, ranked (all 144, including 51 with none)")
    ax.set_ylabel("water bodies")
    ax.set_title("A few wards hold most of the stock", fontsize=10, loc="left")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.annotate(f"ward 108: {counts[0]}", xy=(1, counts[0]),
                xytext=(18, counts[0] - 40), fontsize=8, color=MUTED,
                arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.7})
    ax.axvline(93.5, color=WARM, lw=0.9, ls="--")
    ax.annotate("51 wards\nwith none", xy=(112, max(counts) * 0.55),
                fontsize=8, color=WARM, ha="center")

    ax = axes[1]
    a = wb["area_ha"].dropna()
    ax.hist(a, bins=np.logspace(np.log10(a.min()), np.log10(a.max()), 45),
            color=WATER)
    ax.set_xscale("log")
    ax.set_xlabel("water spread area (hectares, log scale)")
    ax.set_ylabel("water bodies")
    ax.set_title("Almost all of them are small ponds", fontsize=10, loc="left")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.axvline(a.median(), color=WARM, lw=1.0)
    ax.annotate(f"median {a.median():.2f} ha", xy=(a.median(), ax.get_ylim()[1] * 0.86),
                xytext=(6, 0), textcoords="offset points",
                fontsize=8, color=WARM)

    fig.tight_layout()
    fig.savefig(FIG / "fig1_distribution.png", dpi=200)
    plt.close(fig)


def fig2_maps(g):
    """Where they are, and where they have fallen out of use."""
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.6))
    _choropleth(axes[0], g, "n", "Water bodies per ward",
                "Blues", "count", log=True)
    _choropleth(axes[1], g, "area_pct_of_ward",
                "Share of ward area under water", "Blues", "% of ward area")
    sub = g.copy()
    sub.loc[sub["n"] < 10, "disused_share"] = np.nan
    sub.plot(ax=axes[2], color="#f2f2f2", linewidth=0.25, edgecolor="white")
    sub.dropna(subset=["disused_share"]).plot(
        ax=axes[2], column="disused_share", cmap="OrRd", linewidth=0.25,
        edgecolor="white", legend=True,
        legend_kwds={"label": "share not in use", "shrink": 0.62})
    axes[2].set_title("Recorded not in use\n(wards with 10 or more)",
                      fontsize=10, loc="left", pad=8)
    axes[2].set_axis_off()
    fig.suptitle(
        "Wards 142-144 are absent from every panel: KMC has 144 wards, the "
        "published boundary file holds 141",
        fontsize=8.5, color=MUTED, y=0.045)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(FIG / "fig2_maps.png", dpi=200)
    plt.close(fig)


def fig3_boroughs(panel):
    """Disuse and municipal ownership, by borough, on real denominators."""
    b = (panel.groupby("borough")[["n", "n_disused", "n_municipal"]]
         .sum().query("n >= 20"))
    b["disused_pct"] = 100 * b["n_disused"] / b["n"]
    b["municipal_pct"] = 100 * b["n_municipal"] / b["n"]
    b = b.sort_values("disused_pct")

    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    y = np.arange(len(b))
    ax.barh(y - 0.2, b["disused_pct"], height=0.38, color=WARM,
            label="recorded not in use")
    ax.barh(y + 0.2, b["municipal_pct"], height=0.38, color=WATER,
            label="owned by KMC")
    ax.set_yticks(y)
    ax.set_yticklabels([f"Borough {i}  (n={int(n)})"
                        for i, n in zip(b.index, b["n"])])
    ax.set_xlabel("% of the borough's water bodies")
    # Deliberately descriptive. An earlier draft titled this "disuse is worst
    # where KMC owns least", which the data does not support: across the ten
    # boroughs the two shares do not correlate (rho +0.17, p = 0.65).
    ax.set_title("Disuse and municipal ownership both vary sharply by borough",
                 fontsize=10, loc="left")
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    fig.text(0.012, 0.015,
             "Boroughs with at least 20 water bodies. The two bars are shown "
             "together because both vary, not because one explains the other:\n"
             "across boroughs they do not correlate (rho +0.17, p = 0.65, "
             "n = 10).",
             fontsize=7.5, color=MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.10, 1, 1))
    fig.savefig(FIG / "fig3_boroughs.png", dpi=200)
    plt.close(fig)


def fig4_gradient(panel, wards):
    """The one inferential result, with its own instability shown."""
    w = wards.to_crs(K.UTM)
    cen = pd.DataFrame({"ward": w["ward"], "cx": w.geometry.centroid.x})
    p = panel.merge(cen, on="ward", how="left")
    q = p[(p["n"] >= 10) & p["cx"].notna()]

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9))
    ax = axes[0]
    ax.scatter((q["cx"] - q["cx"].min()) / 1000, 100 * q["disused_share"],
               s=18 + 40 * q["n"] / q["n"].max(), color=WATER, alpha=0.75,
               edgecolor="white", linewidth=0.5)
    ax.set_xlabel("ward centroid, km east of the westernmost ward")
    ax.set_ylabel("% of water bodies not in use")
    ax.set_title("Disuse falls from west to east", fontsize=10, loc="left")
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.text(0.97, 0.94, "rho -0.35, p = 0.015\nn = 47 wards, 5% critical rho 0.29",
            transform=ax.transAxes, ha="right", va="top", fontsize=8,
            color=MUTED)

    ax = axes[1]
    rows = json.loads((K.OUT / "robustness.json").read_text())["gradient_sensitivity"]
    x = [r["min_n"] for r in rows]
    ax.plot(x, [r["easting_rho"] for r in rows], "o-", color=WATER,
            label="east-west")
    ax.plot(x, [r["northing_rho"] for r in rows], "o-", color=SAND,
            label="north-south")
    ax.plot(x, [-r["critical_rho"] for r in rows], ls=":", color=MUTED,
            lw=0.9, label="5% critical value")
    ax.plot(x, [r["critical_rho"] for r in rows], ls=":", color=MUTED, lw=0.9)
    ax.axhline(0, color=MUTED, lw=0.7)
    ax.set_xlabel("minimum water bodies per ward")
    ax.set_ylabel("Spearman rho vs disuse share")
    ax.set_title("Why the floor exists", fontsize=10, loc="left")
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    ax.annotate("unfiltered, a share\ncan be 0/1 or 1/1", xy=(1, -0.09),
                xytext=(4.5, 0.20), fontsize=7.5, color=MUTED,
                arrowprops={"arrowstyle": "->", "color": MUTED, "lw": 0.7})

    fig.tight_layout()
    fig.savefig(FIG / "fig4_gradient.png", dpi=200)
    plt.close(fig)


def fig5_not_ekw(wb):
    """The correction: this is pond stock, not the wetlands."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))

    ax = axes[0]
    lon = pd.to_numeric(wb["longitude"], errors="coerce")
    lat = pd.to_numeric(wb["latitude"], errors="coerce")
    ax.scatter(lon, lat, s=2.2, color=WATER, alpha=0.5, linewidth=0)
    ax.axvline(88.40, color=WARM, lw=0.9, ls="--")
    ax.annotate("EM Bypass, roughly", xy=(88.402, 22.462), fontsize=7.5,
                color=WARM)
    ax.axvline(lon.max(), color=MUTED, lw=0.8)
    ax.annotate(f"census stops at {lon.max():.3f} E,\nKMC's eastern boundary",
                xy=(lon.max(), 22.452), xytext=(-7, 0),
                textcoords="offset points", ha="right", va="bottom",
                fontsize=7.5, color=MUTED)
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.set_title("Every water body in the census", fontsize=10, loc="left")
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)

    ax = axes[1]
    total = wb["area_ha"].sum()
    ax.bar(["this census\n(3,051 bodies)", "East Kolkata Wetlands\nRamsar site"],
           [total, 12500], color=[WATER, SAND], width=0.55)
    ax.set_ylabel("hectares")
    ax.set_title("It is not the wetlands dataset", fontsize=10, loc="left")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for i, v in enumerate([total, 12500]):
        ax.text(i, v + 300, f"{v:,.0f} ha", ha="center", fontsize=8.5)
    fig.text(0.012, 0.015,
             f"The whole published stock is {100 * total / 12500:.0f}% of the "
             f"Ramsar site's area, and its largest single water body is "
             f"{wb['area_ha'].max():.0f} ha. The East Kolkata Wetlands lie "
             f"mostly east of KMC's boundary,\nso the sewage-fed bheris are "
             f"not in this file at all.",
             fontsize=7.5, color=MUTED, ha="left", va="bottom")

    fig.tight_layout(rect=(0, 0.11, 1, 1))
    fig.savefig(FIG / "fig5_not_ekw.png", dpi=200)
    plt.close(fig)


def main() -> int:
    FIG.mkdir(parents=True, exist_ok=True)
    panel, g, wb = load()
    fig1_distribution(panel, wb)
    fig2_maps(g)
    fig3_boroughs(panel)
    fig4_gradient(panel, gpd.read_file(K.INTERIM / "wards.gpkg"))
    fig5_not_ekw(wb)
    for p in sorted(FIG.glob("*.png")):
        print(f"  {p.name:26s} {p.stat().st_size / 1024:6.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
