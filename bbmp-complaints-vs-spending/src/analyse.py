"""Findings and figures for BBMP complaints vs ward spending.

Reads the panels built by build_panel.py, prints every number quoted in the
write-up, and renders four figures into figures/.
"""
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT, FIG = ROOT / "data" / "out", ROOT / "figures"

# Validated categorical slots 1-3 (light mode, all-pairs). See dataviz palette.
C_ROADS, C_LIGHT, C_WASTE = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8880"
SURFACE, GRID = "#fcfcfb", "#e5e4df"
CR = 1e7  # one crore

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "text.color": INK, "axes.labelcolor": INK2, "axes.edgecolor": GRID,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "figure.dpi": 160, "savefig.dpi": 160,
    "savefig.facecolor": SURFACE, "savefig.bbox": "tight",
})


def style(ax, title=None, sub=None, xlab=None, ylab=None):
    if title:
        ax.set_title(title, loc="left", fontsize=13, fontweight="bold",
                     color=INK, pad=18 if sub else 10)
    if sub:
        ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9.5,
                color=MUTED, va="bottom")
    ax.set_xlabel(xlab or "", fontsize=9.5)
    ax.set_ylabel(ylab or "", fontsize=9.5)
    ax.tick_params(length=0, labelsize=9)
    return ax


def fig_untagged(untagged, ward_total, path):
    total = untagged + ward_total
    fig, ax = plt.subplots(figsize=(9, 2.5))
    ax.barh([0], [ward_total / CR], color=C_ROADS, height=.42,
            label="Attributed to a ward")
    ax.barh([0], [untagged / CR], left=ward_total / CR + total / CR * 0.004,
            color="#e34948", height=.42, label="Untagged / multiple wards")
    ax.text(ward_total / CR / 2, 0, f"Rs {ward_total/CR:,.0f} cr\n65.5%",
            ha="center", va="center", color="white", fontsize=10.5,
            fontweight="bold")
    ax.text(ward_total / CR + untagged / CR / 2, 0,
            f"Rs {untagged/CR:,.0f} cr\n34.5%", ha="center", va="center",
            color="white", fontsize=10.5, fontweight="bold")
    ax.set_yticks([])
    ax.set_xlim(0, total / CR)
    ax.grid(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_xticks([])
    style(ax, "A third of BBMP's work-order spending belongs to no ward",
          f"Gross work orders 2018-23, Rs {total/CR:,.0f} crore total. "
          "The untagged block cannot be traced to any of the 198 wards.")
    ax.legend(frameon=False, fontsize=9, loc="upper left",
              bbox_to_anchor=(0, -0.08), ncol=2)
    fig.savefig(path)
    plt.close(fig)


def fig_mismatch(theme, wards, path):
    order = ["Roads and Drains", "Streetlighting", "Waste Management"]
    cols = {"Roads and Drains": C_ROADS, "Streetlighting": C_LIGHT,
            "Waste Management": C_WASTE}
    theme = theme[theme["ward_no"].isin(wards)]
    agg = (theme.groupby("theme")
                .agg(complaints=("complaints", "sum"), spend=("spend", "sum"))
                .reindex(order))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, col, fmt, title in (
        (axes[0], "complaints", lambda v: f"{v:,.0f}",
         "What residents complain about"),
        (axes[1], "spend", lambda v: f"Rs {v/CR:,.0f} cr",
         "Where the money goes"),
    ):
        vals = agg[col].values
        y = np.arange(len(order))[::-1]
        ax.barh(y, vals, color=[cols[o] for o in order], height=.55)
        for yi, v in zip(y, vals):
            ax.text(v + max(vals) * .02, yi, fmt(v), va="center",
                    fontsize=10, color=INK, fontweight="bold")
        ax.set_yticks(y)
        ax.set_yticklabels(order, fontsize=10)
        ax.set_xlim(0, max(vals) * 1.28)
        ax.set_xticks([])
        ax.grid(False)
        ax.spines["bottom"].set_visible(False)
        style(ax, title)
        ax.set_title(title, loc="left", fontsize=11.5, fontweight="bold",
                     color=INK, pad=10)
    fig.suptitle("Complaints and spending point at different problems",
                 x=0.005, y=1.14, ha="left", fontsize=14, fontweight="bold",
                 color=INK)
    fig.text(0.005, 1.045,
             "Complaints 2020-24 vs gross work orders 2018-23, across the 196 "
             "wards with both. Separate scales - the panels are not comparable "
             "in width.",
             ha="left", fontsize=9.5, color=MUTED)
    fig.savefig(path)
    plt.close(fig)


def fig_scatter(d, path):
    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    ax.scatter(d["complaints"], d["spend_total"] / CR, s=34, color=C_ROADS,
               alpha=.72, edgecolor=SURFACE, linewidth=1.1, zorder=3)
    ax.set_xscale("log")
    ax.set_yscale("log")
    marked = pd.concat([d.nlargest(2, "spend_total"),
                        d.nlargest(2, "complaints")]).drop_duplicates("ward_no")
    for i, (_, r) in enumerate(marked.iterrows()):
        ax.annotate(r["canonical_name"],
                    (r["complaints"], r["spend_total"] / CR),
                    textcoords="offset points",
                    xytext=(-10, 12 if i % 2 == 0 else -16),
                    ha="right", fontsize=8.5, color=INK2, zorder=4)
    plain = FuncFormatter(lambda v, _: f"{v:,.0f}")
    blank = FuncFormatter(lambda v, _: "")
    ax.set_xticks([500, 1000, 2000, 5000, 10000, 20000])
    ax.set_yticks([20, 50, 100, 200, 400])
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_formatter(plain)
        axis.set_minor_formatter(blank)
    ax.set_xlim(d["complaints"].min() * .8, d["complaints"].max() * 1.35)
    ax.set_ylim(d["spend_total"].min() / CR * .8,
                d["spend_total"].max() / CR * 1.35)
    style(ax, "More complaints, more money - but only loosely",
          "Each dot is one of 196 wards. Log scales.",
          "Complaints, 2020-24", "Work-order spend, Rs crore (2018-23)")
    r_p = d["complaints"].corr(d["spend_total"])
    r_s = d["complaints"].corr(d["spend_total"], method="spearman")
    ax.text(.98, .04, f"Pearson r = {r_p:.2f}\nSpearman rho = {r_s:.2f}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=9.5,
            color=INK2,
            bbox=dict(boxstyle="round,pad=0.5", fc=SURFACE, ec=GRID))
    fig.savefig(path)
    plt.close(fig)


def fig_resolution(d, path):
    q = (d.groupby("spend_q", observed=True)
           .agg(res=("resolution_rate", "median"),
                spend=("spend_total", "median")))
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    x = np.arange(len(q))
    ax.bar(x, q["res"] * 100, color=C_ROADS, width=.55)
    for xi, v in zip(x, q["res"] * 100):
        ax.text(xi, v + .6, f"{v:.1f}%", ha="center", fontsize=10,
                color=INK, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{i}\nmedian Rs {s/CR:,.0f} cr"
                        for i, s in zip(q.index, q["spend"])], fontsize=9)
    ax.set_axisbelow(True)
    ax.xaxis.grid(False)
    ax.set_ylim(0, 108)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    style(ax, "Spending more does not resolve more complaints",
          "Median ward complaint-closure rate, by ward spending quintile.",
          "Ward spending quintile", "Complaints closed")
    fig.savefig(path)
    plt.close(fig)


def main() -> int:
    FIG.mkdir(exist_ok=True)
    p = pd.read_csv(OUT / "panel_ward.csv")
    d = p[p["complaints"].notna() & p["spend_total"].notna()].copy()
    theme = pd.read_csv(OUT / "panel_ward_category.csv")

    ward_total = p["spend_total"].sum()
    untagged = 80230466998  # untagged row, BBMP categorised work orders
    d["spend_q"] = pd.qcut(d["spend_total"], 5,
                           labels=["Q1", "Q2", "Q3", "Q4", "Q5"])

    print(f"wards analysed              {len(d)}")
    print(f"complaints 2020-24          {int(d['complaints'].sum()):,}")
    print(f"ward-attributed spend       Rs {ward_total/CR:,.0f} cr")
    print(f"untagged spend              Rs {untagged/CR:,.0f} cr "
          f"({100*untagged/(untagged+ward_total):.1f}%)")
    print(f"spend  median/min/max (cr)  {d['spend_total'].median()/CR:,.0f} / "
          f"{d['spend_total'].min()/CR:,.0f} / {d['spend_total'].max()/CR:,.0f}"
          f"   spread {d['spend_total'].max()/d['spend_total'].min():.0f}x")
    print(f"pearson / spearman          "
          f"{d['complaints'].corr(d['spend_total']):.3f} / "
          f"{d['complaints'].corr(d['spend_total'], method='spearman'):.3f}")
    print(f"resolution median (p10-p90) "
          f"{d['resolution_rate'].median():.3f} "
          f"({d['resolution_rate'].quantile(.1):.3f}-"
          f"{d['resolution_rate'].quantile(.9):.3f})")
    growth = (d["complaints_2024"] / d["complaints_2020"]).median()
    print(f"median complaint growth     {growth:.2f}x (2020 -> 2024)")
    print("\nby theme:")
    for th, g in theme.dropna(subset=["complaints", "spend"]).groupby("theme"):
        g = g[g["complaints"] > 0]
        print(f"  {th:<18} complaints {int(g['complaints'].sum()):>7,}  "
              f"spend Rs {g['spend'].sum()/CR:>6,.0f} cr  "
              f"rho {g['complaints'].corr(g['spend'], method='spearman'):+.3f}")

    fig_untagged(untagged, ward_total, FIG / "fig1_untagged_spending.png")
    fig_mismatch(theme, set(d["ward_no"]), FIG / "fig2_category_mismatch.png")
    fig_scatter(d, FIG / "fig3_complaints_vs_spend.png")
    fig_resolution(d, FIG / "fig4_resolution_by_spend.png")
    print(f"\nfigures -> {FIG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
