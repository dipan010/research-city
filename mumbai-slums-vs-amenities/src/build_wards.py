"""Ward denominators: population, households, and public-latrine dependence.

Three census products have to be reconciled here, and none of them is keyed by
BMC ward directly:

  census_wards.csv  census ward code -> BMC ward name + population
  pca_*.csv         census ward code -> households
  houselisting_*    census ward code -> % of households by latrine access

So the BMC ward label comes from exactly one place (census_wards.csv), and the
other two join to it by census ward code. Nothing is matched on name.

Table HH-14 reports percentages, not counts, so aggregating 97 census wards up
to 24 BMC wards is a household-weighted mean - not a plain average, which would
let a 4,000-household ward pull as hard as a 60,000-household one.
"""
import sys

import numpy as np
import pandas as pd

from mumbai import RAW, OUT, norm_ward

# Table HH-14 column indices (0-based), read off the header block in the file.
# The sheet has a four-row merged header that pandas cannot parse into names,
# so the columns are addressed positionally and verified below.
COL_WARD_NO = 7
COL_AREA_NAME = 8
COL_RURAL_URBAN = 9
COL_HAS_LATRINE = 90       # "having latrine facility within the premises"
COL_NO_LATRINE = 99        # "not having latrine facility within the premises"
COL_PUBLIC_LATRINE = 100   # "Alternative source: Public latrine"
COL_OPEN = 101             # "Alternative source: Open"


def load_census_wards():
    c = pd.read_csv(RAW / "census_wards.csv")
    c["ward"] = c["Ward Name"].map(norm_ward)
    bad = c[c["ward"].isna()]
    if len(bad):
        raise SystemExit(f"unmapped ward names: {sorted(set(bad['Ward Name']))}")
    c["code"] = c["Ward Code"].astype(int)
    return c[["code", "ward", "Total Population"]].rename(
        columns={"Total Population": "population"})


def load_households():
    """Households per census ward, from the two Primary Census Abstracts."""
    rows = []
    for f in ("pca_city.csv", "pca_suburban.csv"):
        p = pd.read_csv(RAW / f)
        w = p[p["Level"].astype(str).str.strip().str.upper() == "WARD"]
        w = w[w["TRU"].astype(str).str.strip() == "Urban"]
        rows.append(w[["Ward", "No_HH", "TOT_P"]].rename(
            columns={"Ward": "code", "No_HH": "households", "TOT_P": "pca_population"}))
    h = pd.concat(rows, ignore_index=True)
    h["code"] = h["code"].astype(int)
    return h


def load_hh14():
    """Latrine access by census ward, from houselisting table HH-14."""
    rows = []
    for f in ("houselisting_city.xlsx", "houselisting_suburban.xlsx"):
        df = pd.read_excel(RAW / f, sheet_name=0, header=None)

        # Verify the positional columns are the ones we think they are before
        # reading any number out of them - the header is merged across four
        # rows and a re-upload could shift it.
        hdr = " ".join(str(df.iloc[r, c]) for r in range(3, 7)
                       for c in (COL_NO_LATRINE, COL_PUBLIC_LATRINE))
        if "not having latrine" not in hdr or "Public latrine" not in hdr:
            raise SystemExit(f"HH-14 header moved in {f}; re-check column indices")

        d = df.iloc[7:]
        d = d[d[COL_RURAL_URBAN].astype(str).str.strip() == "Urban"]
        # Ward rows only - the file also carries district, sub-district and
        # town subtotals, which would double-count if summed alongside.
        d = d[d[COL_AREA_NAME].astype(str).str.contains("Ward No", na=False)]
        for _, r in d.iterrows():
            rows.append({
                "code": int(str(r[COL_WARD_NO]).strip()),
                "pct_latrine_in_premises": float(r[COL_HAS_LATRINE]),
                "pct_no_latrine_in_premises": float(r[COL_NO_LATRINE]),
                "pct_public_latrine": float(r[COL_PUBLIC_LATRINE]),
                "pct_open_defecation": float(r[COL_OPEN]),
            })
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cw = load_census_wards()
    hh = load_households()
    h14 = load_hh14()

    print(f"census wards      : {len(cw)}  ({cw['ward'].nunique()} BMC wards)")
    print(f"PCA household rows: {len(hh)}")
    print(f"HH-14 rows        : {len(h14)}")

    d = cw.merge(hh, on="code", how="outer", indicator="_hh")
    d = d.merge(h14, on="code", how="outer")

    # Report, rather than silently drop, any census ward that fails to join.
    orphan = d[d["ward"].isna()]
    if len(orphan):
        print(f"\n!! {len(orphan)} census ward code(s) with no BMC ward label: "
              f"{sorted(orphan['code'])}")
        print("   excluded from ward aggregates; counted in the reconciliation below")
    d = d.dropna(subset=["ward"])

    # Reconcile the two independent population counts before using either.
    gap = abs(d["population"].sum() - d["pca_population"].sum())
    print(f"\npopulation  census_wards.csv : {d['population'].sum():,}")
    print(f"            PCA               : {int(d['pca_population'].sum()):,}")
    print(f"            difference        : {int(gap):,}")

    # Census ward 1045 (H/E) carries no HH-14 row, and HH-14 carries a code
    # 3837 that appears in no other census product. It is a clean one-for-one
    # mismatch and pairing them is tempting, but the codes are not documented
    # as equivalent anywhere, so they are left unpaired - the latrine
    # percentages for H/E come from its remaining census wards, and the
    # household coverage that implies is recorded per ward. robustness.py
    # tests what pairing them would change.
    PCT = ["pct_latrine_in_premises", "pct_no_latrine_in_premises",
           "pct_public_latrine", "pct_open_defecation"]

    def agg(x):
        cov = x.dropna(subset=PCT + ["households"])
        out = {
            "population": x["population"].sum(),
            "households": x["households"].sum(),
            "census_wards": len(x),
            "hh14_households": cov["households"].sum(),
        }
        for c in PCT:
            out[c] = (np.average(cov[c], weights=cov["households"])
                      if len(cov) else np.nan)
        return pd.Series(out)

    w = d.groupby("ward").apply(agg, include_groups=False).reset_index()
    w["hh14_coverage"] = w["hh14_households"] / w["households"]

    lo = w.loc[w["hh14_coverage"] < 0.999]
    if len(lo):
        print("\nHH-14 household coverage below 100%:")
        for _, r in lo.iterrows():
            print(f"  {r['ward']:4s} {r['hh14_coverage']:6.1%} "
                  f"({int(r['households'] - r['hh14_households']):,} households "
                  f"in census wards with no HH-14 row)")

    cov = d.dropna(subset=PCT + ["households"])
    city_pub = np.average(cov["pct_public_latrine"], weights=cov["households"])
    city_open = np.average(cov["pct_open_defecation"], weights=cov["households"])
    print(f"\ncity-wide, household-weighted:")
    print(f"  depend on a public latrine : {city_pub:.1f}%")
    print(f"  no latrine, open           : {city_open:.1f}%")
    print(f"  ward range (public latrine): "
          f"{w['pct_public_latrine'].min():.1f}% ({w.loc[w['pct_public_latrine'].idxmin(),'ward']})"
          f" - {w['pct_public_latrine'].max():.1f}% ({w.loc[w['pct_public_latrine'].idxmax(),'ward']})")

    dest = OUT / "ward_census.csv"
    w.to_csv(dest, index=False)
    print(f"\n-> {dest}  ({len(w)} wards)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
