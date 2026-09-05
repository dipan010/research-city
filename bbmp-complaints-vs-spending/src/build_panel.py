"""Join BBMP citizen grievances to BBMP work-order spending, by ward.

Two BBMP publications, never previously joined:

  demand  - BBMP Grievances Data, 2020-2024, one row per complaint,
            carrying a ward NAME and a resolution status
  supply  - BBMP Work Orders Categorised 2018-2023, ward x category
            rupee totals, carrying a ward NUMBER

Grievance ward names are reconciled to ward numbers through the crosswalk
built by build_crosswalk.py. Work orders join on their own Ward No column.

Outputs
  data/interim/grievances_by_ward_year.csv   ward x year x category
  data/out/panel_ward.csv                    one row per ward, both sides
  data/out/panel_ward_category.csv           ward x themed category
"""
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW, INTERIM, OUT = (ROOT / "data" / d for d in ("raw", "interim", "out"))

YEARS = range(2020, 2025)

# Grievance categories -> the work-order spend categories they correspond to.
# Only these three map cleanly onto BBMP's own spend headings; everything else
# is kept in the ward totals but excluded from per-theme comparison.
THEME = {
    "Electrical": "Streetlighting",
    "Solid Waste (Garbage) Related": "Waste Management",
    "Road Maintenance(Engg)": "Roads and Drains",
}

SPEND_CATEGORIES = [
    "Buildings and Facilities", "Drainage", "Others", "Roads and Drains",
    "Roads and Infrastructure", "Streetlighting", "Surveillance",
    "Waste Management", "Water and Sanitation",
]

# A complaint counts as resolved only if BBMP closed it. "Non Relevant" is a
# rejection, not a resolution, and is excluded from the denominator entirely.
RESOLVED = {"Closed"}
NOT_A_COMPLAINT = {"Non Relevant"}


def load_crosswalk() -> dict[str, int]:
    cw = pd.read_csv(OUT / "ward_crosswalk.csv")
    cw = cw[cw["ward_no"].notna() & cw["sources"].str.contains("grievances")]
    return {str(r.observed_name).strip(): int(r.ward_no)
            for r in cw.itertuples()}


def load_grievances(mapping: dict[str, int]) -> pd.DataFrame:
    frames = []
    for year in YEARS:
        f = RAW / f"grievances_{year}.csv"
        if not f.exists():
            print(f"  !! missing {f.name}")
            continue
        g = pd.read_csv(f, dtype=str,
                        usecols=["Complaint ID", "Category", "Grievance Date",
                                 "Ward Name", "Grievance Status"])
        g["year"] = year
        g["ward_no"] = g["Ward Name"].str.strip().map(mapping)
        unmapped = g["ward_no"].isna().sum()
        print(f"  {year}: {len(g):>7,} complaints, "
              f"{unmapped:,} unmapped ward names")
        frames.append(g)
    gr = pd.concat(frames, ignore_index=True)
    gr = gr[gr["ward_no"].notna()].copy()
    gr["ward_no"] = gr["ward_no"].astype(int)
    gr["status"] = gr["Grievance Status"].str.strip()
    gr["is_complaint"] = ~gr["status"].isin(NOT_A_COMPLAINT)
    gr["is_resolved"] = gr["status"].isin(RESOLVED)
    return gr


def load_workorders() -> pd.DataFrame:
    wo = pd.read_csv(RAW / "workorders_ward_category_gross.csv", dtype=str)
    wo["ward_no"] = pd.to_numeric(wo["Ward No"], errors="coerce")
    untagged = pd.to_numeric(
        wo.loc[wo["Wards"].astype(str).str.contains("Untagged", case=False,
                                                    na=False), "Grand Total"],
        errors="coerce").sum()
    wo = wo[wo["ward_no"].notna()].copy()
    wo["ward_no"] = wo["ward_no"].astype(int)
    for c in SPEND_CATEGORIES + ["Grand Total"]:
        wo[c] = pd.to_numeric(wo[c], errors="coerce").fillna(0)
    wo = wo.rename(columns={"Grand Total": "spend_total",
                            "Wards": "wo_name_as_published"})
    wo.attrs["untagged"] = untagged
    return wo


def main() -> int:
    INTERIM.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    mapping = load_crosswalk()
    print(f"crosswalk: {len(mapping)} grievance ward names -> "
          f"{len(set(mapping.values()))} wards\n")

    print("loading grievances")
    gr = load_grievances(mapping)

    by_wyc = (gr.groupby(["ward_no", "year", "Category"], as_index=False)
                .agg(complaints=("is_complaint", "sum"),
                     resolved=("is_resolved", "sum"),
                     rows=("Complaint ID", "size")))
    by_wyc.to_csv(INTERIM / "grievances_by_ward_year.csv", index=False)
    print(f"\n  -> {INTERIM / 'grievances_by_ward_year.csv'}")

    print("\nloading work orders")
    wo = load_workorders()
    untagged = wo.attrs["untagged"]
    ward_total = wo["spend_total"].sum()
    print(f"  {len(wo)} wards, ward-attributed spend "
          f"Rs {ward_total/1e7:,.0f} cr")
    print(f"  untagged / multi-ward     Rs {untagged/1e7:,.0f} cr "
          f"({100*untagged/(ward_total+untagged):.1f}% of all spend)")

    # ---- ward-level panel -------------------------------------------------
    gw = (gr.groupby("ward_no", as_index=False)
            .agg(complaints=("is_complaint", "sum"),
                 resolved=("is_resolved", "sum")))
    gw["resolution_rate"] = gw["resolved"] / gw["complaints"]

    first, last = min(YEARS), max(YEARS)
    span = (gr[gr["year"].isin([first, last])]
            .groupby(["ward_no", "year"], as_index=False)
            .agg(n=("is_complaint", "sum"))
            .pivot(index="ward_no", columns="year", values="n")
            .rename(columns={first: f"complaints_{first}",
                             last: f"complaints_{last}"})
            .reset_index())

    panel = (wo[["ward_no", "wo_name_as_published", "spend_total"]
                + SPEND_CATEGORIES]
             .merge(gw, on="ward_no", how="outer")
             .merge(span, on="ward_no", how="left"))

    cw = pd.read_csv(OUT / "ward_crosswalk.csv")
    names = (cw[cw["ward_no"].notna()]
             .drop_duplicates("ward_no")[["ward_no", "canonical_name"]])
    names["ward_no"] = names["ward_no"].astype(int)
    panel = panel.merge(names, on="ward_no", how="left")

    panel["spend_per_complaint"] = panel["spend_total"] / panel["complaints"]
    panel = panel.sort_values("ward_no")
    cols = (["ward_no", "canonical_name", "wo_name_as_published",
             "complaints", "resolved", "resolution_rate",
             f"complaints_{first}", f"complaints_{last}",
             "spend_total", "spend_per_complaint"] + SPEND_CATEGORIES)
    panel[cols].to_csv(OUT / "panel_ward.csv", index=False)
    print(f"\n  -> {OUT / 'panel_ward.csv'}  ({len(panel)} wards)")

    # ---- ward x theme panel ----------------------------------------------
    th = by_wyc[by_wyc["Category"].isin(THEME)].copy()
    th["theme"] = th["Category"].map(THEME)
    th = (th.groupby(["ward_no", "theme"], as_index=False)
            .agg(complaints=("complaints", "sum"),
                 resolved=("resolved", "sum")))
    spend_long = wo.melt(id_vars="ward_no", value_vars=list(set(THEME.values())),
                         var_name="theme", value_name="spend")
    tp = th.merge(spend_long, on=["ward_no", "theme"], how="outer")
    tp["spend_per_complaint"] = tp["spend"] / tp["complaints"]
    tp = tp.sort_values(["theme", "ward_no"])
    tp.to_csv(OUT / "panel_ward_category.csv", index=False)
    print(f"  -> {OUT / 'panel_ward_category.csv'}  ({len(tp)} rows)")

    print("\n--- sanity ---")
    print(f"  total complaints kept : {int(gw['complaints'].sum()):,}")
    print(f"  overall resolution    : "
          f"{100*gw['resolved'].sum()/gw['complaints'].sum():.1f}%")
    print(f"  wards with both sides : "
          f"{int((panel['complaints'].notna() & panel['spend_total'].notna()).sum())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
