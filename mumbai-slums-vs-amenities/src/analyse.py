"""Findings and figures for Mumbai slum clusters vs amenity access.

Reads the tables built by build_wards.py and build_access.py, prints every
number quoted in the write-up, and renders the figures into figures/.

Note on inference: Mumbai has 24 wards. At n=24 a Spearman coefficient needs
~0.41 to clear the 5% level, so ward-level correlations are not reported as
findings - the ward tables describe 24 named units and nothing more. The
statistics live at cluster level (n=2,541) and grid-cell level (n=47,450).

Grid cells 100 m apart are heavily spatially autocorrelated, so a p-value
computed as if they were independent is meaningless however small it comes out.
No p-values are reported. The evidence for the proximity result is the
within-ward count - 21 of 21 wards - which does not assume independence.
"""
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT, FIG = ROOT / "data" / "out", ROOT / "figures"
INTERIM = ROOT / "data" / "interim"

# Same validated categorical slots as the sibling BBMP project, so the two
# read as one series. Checked with the dataviz validator (light, all pairs).
C_SLUM, C_CITY, C_THIRD = "#2a78d6", "#eb6834", "#1baf7a"
FLAG = "#c1362f"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8880"
SURFACE, GRID = "#fcfcfb", "#e5e4df"

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

# Service categories in reporting order, with display labels.
CATS = [
    ("toilet", "Public toilet"),
    ("bus", "BEST bus stop"),
    ("school", "School (any)"),
    ("school_municipal", "Municipal school"),
    ("park", "Park or garden"),
    ("health", "Health centre"),
    ("funeral", "Funeral site"),
    ("police", "Police station"),
    ("rail", "Suburban station"),
    ("fire", "Fire station"),
]


def style(ax, title=None, sub=None, xlab=None, ylab=None):
    if title:
        ax.set_title(title, loc="left", fontsize=13, fontweight="bold",
                     color=INK, pad=20 if sub else 10)
    if sub:
        ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9.5,
                color=MUTED, va="bottom")
    ax.set_xlabel(xlab or "", fontsize=9.5)
    ax.set_ylabel(ylab or "", fontsize=9.5)
    ax.tick_params(length=0, labelsize=9)
    return ax


# --------------------------------------------------------------------------
def baseline_table(grid):
    """Median distance for slum land against two baselines.

    `all` is every non-slum cell; `inhabited` restricts it to cells near a bus
    stop or a school, which is what makes the comparison fair - the unrestricted
    baseline is dragged outward by the national park, mangroves and salt pans.
    Each service is scored against a proxy it does not itself define.
    """
    slum, base = grid[grid["slum"]], grid[~grid["slum"]]
    rows = []
    for key, lab in CATS:
        if key == "bus":
            mask = base["near_school"]          # bus defines near_bus
        elif key in ("school", "school_municipal"):
            mask = base["near_bus"]             # schools define near_school
        else:
            mask = base["inhabited"]
        s = slum[f"d_{key}"].median()
        a = base[f"d_{key}"].median()
        i = base[mask][f"d_{key}"].median()
        rows.append({"key": key, "label": lab, "slum": s, "all": a,
                     "inhabited": i, "ratio_all": s / a, "ratio_inh": s / i})
    return pd.DataFrame(rows)


def fig_distance(grid, path):
    """Slum vs inhabited-city distance ratio, per service."""
    t = baseline_table(grid).sort_values("ratio_inh")
    y = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(9.6, 5.6))
    ax.axvline(1.0, color=INK2, lw=1.3, zorder=2)
    for i, (_, r) in enumerate(t.iterrows()):
        ax.plot([r["ratio_all"], r["ratio_inh"]], [i, i], color=GRID, lw=2.4,
                zorder=1, solid_capstyle="round")
    ax.scatter(t["ratio_all"], y, s=70, color=C_CITY, zorder=3,
               label="vs all non-slum land", edgecolor=SURFACE, linewidth=2)
    ax.scatter(t["ratio_inh"], y, s=78, color=C_SLUM, zorder=4,
               label="vs inhabited land only", edgecolor=SURFACE, linewidth=2)
    for i, (_, r) in enumerate(t.iterrows()):
        ax.text(r["ratio_inh"] + .035, i, f"{r['ratio_inh']:.2f}", va="center",
                fontsize=8.6, color=C_SLUM, fontweight="bold")
    ax.set_yticks(y, t["label"])
    ax.set_xlim(0.12, 1.52)
    ax.set_ylim(len(t) - .4, -1.15)
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, loc="upper right", fontsize=9.3)
    # Plain words, not arrow glyphs - the sans fallback has no arrow coverage
    # and renders them as tofu.
    ax.text(1.03, -.72, "slum land further", fontsize=8.6, color=MUTED,
            ha="left", va="center")
    ax.text(0.97, -.72, "slum land closer", fontsize=8.6, color=MUTED,
            ha="right", va="center")
    style(ax, "Only sanitation and schools survive a fair baseline",
          "Ratio of median distance: slum land / rest of the city. Below 1 means "
          "slum land is closer.", "ratio (1.0 = parity)")
    fig.savefig(path)
    plt.close(fig)


def fig_load(w, path):
    """Households per public-latrine seat, by ward. One series -> no legend."""
    d = w.sort_values("hh_per_seat", ascending=False)
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    bars = ax.bar(d["ward"], d["hh_per_seat"], color=C_SLUM, width=.66)
    city = w["hh_public_latrine"].sum() / w["toilet_seats"].sum()
    ax.axhline(city, color=FLAG, lw=1.6, ls=(0, (4, 3)), zorder=4)
    ax.text(len(d) - .4, city + .7, f"city average {city:.1f}", ha="right",
            fontsize=9, color=FLAG, fontweight="bold")
    for b, v in zip(bars, d["hh_per_seat"]):
        ax.text(b.get_x() + b.get_width() / 2, v + .5, f"{v:.0f}",
                ha="center", fontsize=8.2, color=INK2)
    ax.set_ylim(0, d["hh_per_seat"].max() * 1.16)
    ax.grid(axis="x", visible=False)
    style(ax, "How many households share one public toilet seat",
          "Census 2011 households depending on a public latrine, per seat on BMC's toilet layer",
          None, "households per seat")
    fig.savefig(path)
    plt.close(fig)


def fig_inside(cluster, path):
    """Share of clusters containing each service, plus distance distribution."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.4, 4.9),
                                 gridspec_kw={"width_ratios": [1, 1.12]})
    rows = [(lab, (cluster[f"n_{k}"] > 0).mean()) for k, lab in CATS]
    rows.sort(key=lambda r: r[1])
    a1.barh([r[0] for r in rows], [r[1] * 100 for r in rows],
            color=C_SLUM, height=.62)
    for i, (lab, v) in enumerate(rows):
        a1.text(v * 100 + .8, i, f"{v:.1%}", va="center", fontsize=8.6,
                color=INK2)
    a1.set_xlim(0, 40)
    a1.grid(axis="y", visible=False)
    style(a1, "Services inside the cluster",
          "Share of 2,541 slum clusters containing at least one", "% of clusters")

    d = cluster["d_toilet"]
    a2.hist(d.clip(upper=600), bins=40, color=C_SLUM)
    a2.axvline(d.median(), color=FLAG, lw=1.6, ls=(0, (4, 3)))
    a2.text(d.median() + 14, a2.get_ylim()[1] * .92,
            f"median {d.median():.0f} m", fontsize=9, color=FLAG,
            fontweight="bold")
    a2.grid(axis="x", visible=False)
    style(a2, "Distance to the nearest public toilet",
          "Per slum cluster, metres (clipped at 600 m)", "metres", "clusters")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_gender(w, path):
    """Female share of toilet seats, by ward, against parity and Praja."""
    d = w.sort_values("female_share")
    fig, ax = plt.subplots(figsize=(10.4, 5.0))
    x = np.arange(len(d))
    ax.bar(x, d["female_share"] * 100, color=C_SLUM, width=.66)
    # Both reference lines are labelled in a right-hand gutter - every bar
    # crosses the 25% line, so a label placed over the plot is unreadable.
    edge = len(d) - .55
    ax.plot([-.7, edge], [50, 50], color=MUTED, lw=1.4, zorder=5)
    ax.text(edge + .3, 50, "parity", ha="left", va="center",
            fontsize=9, color=MUTED)
    ax.plot([-.7, edge], [25, 25], color=FLAG, lw=1.6, ls=(0, (4, 3)), zorder=5)
    ax.text(edge + .3, 25.0,
            "25% - BMC's public toilets\nonly, via RTI to Praja\nFoundation, Dec 2024",
            ha="left", va="center", fontsize=8.8, color=FLAG,
            fontweight="bold", linespacing=1.45)
    ax.set_xticks(x, d["ward"])
    ax.set_xlim(-.7, len(d) + 3.6)
    ax.set_ylim(0, 62)
    ax.grid(axis="x", visible=False)
    style(ax, "Female share of toilet seats on BMC's published map layer",
          "The layer pools public and community toilets; BMC's public-toilet-only "
          "figures sit at 25%.", None, "% of seats for women")
    fig.savefig(path)
    plt.close(fig)


def fig_denominator(w, path):
    """The same two columns, three denominators, three different answers."""
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.3))
    specs = [
        ("toilet_seats", "Seats, raw count", "seats"),
        ("seats_per_km2", "Seats per km2 of ward", "seats / km2"),
        ("hh_per_seat", "Households per seat", "households / seat"),
    ]
    for ax, (col, title, lab) in zip(axes, specs):
        d = w.sort_values(col, ascending=False).head(8)
        ax.barh(d["ward"], d[col], color=C_SLUM, height=.62)
        ax.invert_yaxis()
        ax.grid(axis="y", visible=False)
        style(ax, title, None, lab)
    fig.tight_layout(rect=[0, 0, 1, 0.86])
    fig.text(0.008, 0.975,
             "Top eight wards, by three readings of the same toilet layer",
             ha="left", va="top", fontsize=13, fontweight="bold", color=INK)
    fig.text(0.008, 0.912,
             "Ranked by supply, by density of supply, and by supply against "
             "measured need - almost no ward survives all three.",
             fontsize=9.5, color=MUTED, ha="left", va="top")
    fig.savefig(path)
    plt.close(fig)


# --------------------------------------------------------------------------
def main():
    FIG.mkdir(parents=True, exist_ok=True)
    w = pd.read_csv(OUT / "ward_amenities.csv")
    cluster = pd.read_csv(OUT / "cluster_access.csv")
    grid = pd.read_csv(INTERIM / "grid_access.csv")

    w["hh_per_seat"] = w["hh_public_latrine"] / w["toilet_seats"]
    w["seats_per_km2"] = w["toilet_seats"] / w["area_km2"]
    w["female_share"] = w["toilet_seats_f"] / w["toilet_seats"]
    w["persons_per_seat"] = (w["population"] * w["pct_public_latrine"] / 100
                             / w["toilet_seats"])

    print("=" * 72)
    print("1. THE CITY")
    print("=" * 72)
    print(f"  wards                       : {len(w)}")
    print(f"  ward area                   : {w['area_km2'].sum():.1f} km2")
    print(f"  population (Census 2011)    : {int(w['population'].sum()):,}")
    print(f"  slum clusters               : {len(cluster):,}")
    print(f"  slum area                   : {cluster['area_m2'].sum()/1e6:.1f} km2"
          f"  ({cluster['area_m2'].sum()/1e6/w['area_km2'].sum():.1%} of the city's land)")
    print(f"  public toilet points        : {int(w['n_toilet'].sum()):,}")
    print(f"  toilet seats                : {int(w['toilet_seats'].sum()):,}")

    print("\n" + "=" * 72)
    print("2. PROXIMITY - and what happens under a fair baseline")
    print("=" * 72)
    t = baseline_table(grid)
    print(f"  {'service':18s} {'slum':>7s} {'all':>7s} {'ratio':>6s}"
          f" | {'inhab':>7s} {'ratio':>6s}")
    for _, r in t.iterrows():
        print(f"  {r['label']:18s} {r['slum']:7.0f} {r['all']:7.0f}"
              f" {r['ratio_all']:6.2f} | {r['inhabited']:7.0f} {r['ratio_inh']:6.2f}")
    base = grid[~grid["slum"]]
    print(f"\n  grid cells: {grid['slum'].sum():,} slum, {len(base):,} non-slum,"
          f" of which {base['inhabited'].sum():,} inhabited "
          f"({base['inhabited'].mean():.0%})")
    print("  No p-values: 100 m cells are spatially autocorrelated, so a test")
    print("  treating them as independent would report significance it has not")
    print("  earned. The within-ward counts below are the evidence instead.")

    closer = t[t["ratio_inh"] < .9]["label"].tolist()
    par = t[(t["ratio_inh"] >= .9) & (t["ratio_inh"] <= 1.1)]["label"].tolist()
    further = t[t["ratio_inh"] > 1.1]["label"].tolist()
    print(f"\n  against inhabited land, slum land is:")
    print(f"    closer  : {', '.join(closer) if closer else '-'}")
    print(f"    at parity: {', '.join(par) if par else '-'}")
    print(f"    further : {', '.join(further) if further else '-'}")

    # Within-ward control - the comparison that rules out land composition.
    print("\n  within-ward control (median slum minus median non-slum, metres):")
    for key, lab in CATS[:6]:
        gaps = []
        for wd, x in grid.groupby("ward"):
            s_, n_ = x[x["slum"]], x[~x["slum"]]
            if len(s_) >= 20 and len(n_) >= 20:
                gaps.append(s_[f"d_{key}"].median() - n_[f"d_{key}"].median())
        gaps = np.array(gaps)
        print(f"    {lab:18s} closer in {(gaps < 0).sum():2d} of {len(gaps)} wards,"
              f"  median gap {np.median(gaps):+7.0f} m")

    print("\n" + "=" * 72)
    print("3. CLUSTERS - what is actually inside them")
    print("=" * 72)
    for key, lab in CATS:
        print(f"  {lab:18s} inside {(cluster[f'n_{key}']>0).mean():6.1%}"
              f"   median {cluster[f'd_{key}'].median():6.0f} m"
              f"   p90 {cluster[f'd_{key}'].quantile(.9):6.0f} m")
    seats_in = cluster["toilet_seats"].sum()
    print(f"\n  toilet seats inside slum clusters: {int(seats_in):,} "
          f"({seats_in/w['toilet_seats'].sum():.1%} of the city's seats, "
          f"on {cluster['area_m2'].sum()/1e6/w['area_km2'].sum():.1%} of its land)")

    print("\n" + "=" * 72)
    print("4. LOAD - the measure that does show a deficit")
    print("=" * 72)
    dep_hh = w["hh_public_latrine"].sum()
    print(f"  households depending on a public latrine : {int(dep_hh):,}"
          f"  ({dep_hh/w['households'].sum():.1%} of all households)")
    print(f"  toilet seats                             : {int(w['toilet_seats'].sum()):,}")
    print(f"  households per seat, city                : "
          f"{dep_hh/w['toilet_seats'].sum():.1f}")
    print(f"  persons per seat, city (at least)        : "
          f"{(w['population']*w['pct_public_latrine']/100).sum()/w['toilet_seats'].sum():.0f}")
    print("\n  ward range:")
    d = w.sort_values("hh_per_seat", ascending=False)
    for _, r in d.iterrows():
        print(f"    {r['ward']:4s} {r['hh_per_seat']:6.1f} hh/seat"
              f"   {int(r['toilet_seats']):6,} seats"
              f"   {r['pct_public_latrine']:5.1f}% depend"
              f"   {r['slum_area_share']:6.1%} slum land")

    print("\n" + "=" * 72)
    print("5. WHAT THE TOILET LAYER ACTUALLY COUNTS")
    print("=" * 72)
    fs = w["toilet_seats_f"].sum() / w["toilet_seats"].sum()
    print(f"  female share of seats, published layer : {fs:.1%}")
    print(f"  female share inside slum clusters      : "
          f"{cluster['toilet_seats_f'].sum()/cluster['toilet_seats'].sum():.1%}")
    print(f"  BMC public toilets only, via RTI       : 25.0%"
          f"  (846 blocks / 12,517 seats, Dec 2024)")
    print(f"  this layer                             : "
          f"{int(w['n_toilet'].sum()):,} blocks / {int(w['toilet_seats'].sum()):,} seats")
    print(f"  Praja community toilets (Dec 2023)     : ~6,676 blocks, near parity")
    print(f"  -> 846 + 6,676 = 7,522 vs this layer's 8,411, and the blended")
    print(f"     gender share lands near 48.6%. The layer pools both types.")
    print("\n  worst wards on the published layer:")
    for _, r in w.sort_values("female_share").head(5).iterrows():
        ratio = (1 - r["female_share"]) / r["female_share"]
        print(f"    {r['ward']:4s} {r['female_share']:6.1%} female"
              f"   = {ratio:.1f}:1 male:female"
              f"   ({int(r['toilet_seats']):,} seats)")
    print("  Praja reports C 6:1, B 4:1, A 3:1 for public toilets alone.")
    print("  C ward does not reconcile: Praja gives it 416 public seats against")
    print("  this layer's 207, and C has zero community toilets. Left open.")

    print("\n" + "=" * 72)
    print("6. THE DENOMINATOR DECIDES THE ANSWER")
    print("=" * 72)
    for col, lab in [("toilet_seats", "raw seats"),
                     ("seats_per_km2", "seats per km2"),
                     ("hh_per_seat", "households per seat")]:
        top = w.sort_values(col, ascending=False).head(5)["ward"].tolist()
        print(f"  top 5 by {lab:22s}: {', '.join(top)}")
    print("  Three orderings of one column. The ward that looks best-served on")
    print("  raw count is not the one that looks best-served against need.")

    # ---- figures -------------------------------------------------------
    fig_distance(grid, FIG / "fig1_distance_slum_vs_city.png")
    fig_load(w, FIG / "fig2_households_per_seat.png")
    fig_inside(cluster, FIG / "fig3_inside_clusters.png")
    fig_gender(w, FIG / "fig4_gender_gap.png")
    fig_denominator(w, FIG / "fig5_denominators.png")
    print(f"\nfigures -> {FIG}")

    w.to_csv(OUT / "ward_panel.csv", index=False)
    print(f"-> {OUT/'ward_panel.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
