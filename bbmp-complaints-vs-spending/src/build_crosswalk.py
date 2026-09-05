"""Build a BBMP ward-name crosswalk.

BBMP's grievance extracts spell ward names differently from the ward master
("Bellandur" vs "Bellanduru", "Binnipet" vs "Binni Pete"), and carry no ward
number. Nothing joins until those variants are reconciled, and no public
crosswalk exists.

The work-order file needs no name matching - it carries a clean numeric
"Ward No" column covering all 198 wards. Its *names* are separately mangled
("Yelahanka Satellite Town" -> "YelahankSatellitTown"), so they are recorded
here for reference but never used as a join key.

This resolves every name seen in the grievance files to a canonical 198-ward
number, in three passes:

  1. exact match on a normalised key
  2. fuzzy match, accepted only when the best candidate is clearly better
     than the runner-up (guards against picking between near-identical names)
  3. a small hand-checked table for names fuzzy matching cannot reach

Output: data/out/ward_crosswalk.csv
"""
import difflib
import pathlib
import re
import sys
import unicodedata

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "out"

FUZZY_CUTOFF = 0.82
FUZZY_MARGIN = 0.04   # best must beat runner-up by this much to auto-accept

# Names no string metric resolves: BBMP's colloquial or renamed wards.
# Each verified by hand against the ward master and BBMP ward maps.
MANUAL = {
    # Verified against ward_master.csv by exact ward-name lookup, not guessed.
    "hoodi": 54,                      # Hudi
    "ulsoor": 90,                     # Halsoor
    "rajamahal": 64,                  # Raj Mahal Guttahalli
    "yadiyuru": 167,                  # Yediyur
    "hagadooru": 84,                  # Hagadur
    "gali anjaneya swamy temple": 157,  # Gali Anjenaya Temple Ward
    "h m t": 38,                      # "H.M.T" in grievances = HMT Ward
}


def norm(s: str) -> str:
    """Normalise a ward name to a comparison key."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = s.encode("ascii", "ignore").decode()
    s = s.lower()
    s = re.sub(r"\bwards?\b", " ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_master() -> pd.DataFrame:
    m = pd.read_csv(RAW / "ward_master.csv", dtype=str)
    m.columns = [c.strip() for c in m.columns]
    m = m.rename(columns={"Ward No": "ward_no", "Ward Name": "ward_name"})
    m["ward_no"] = m["ward_no"].astype(int)
    m["key"] = m["ward_name"].map(norm)
    return m


def observed_names() -> dict[str, set[str]]:
    """Every ward name string appearing in the source files, by origin."""
    seen: dict[str, set[str]] = {}
    for year in range(2020, 2025):
        f = RAW / f"grievances_{year}.csv"
        if not f.exists():
            continue
        col = pd.read_csv(f, usecols=["Ward Name"], dtype=str)["Ward Name"]
        for v in col.dropna().unique():
            seen.setdefault(str(v).strip(), set()).add(f"grievances_{year}")

    # Work-order names are recorded for reference only. That file joins on its
    # own numeric Ward No, so mangled names there never block the pipeline.
    wo = pd.read_csv(RAW / "workorders_ward_category_gross.csv", dtype=str)
    wo["wn"] = pd.to_numeric(wo["Ward No"], errors="coerce")
    for _, r in wo[wo["wn"].notna()].iterrows():
        if pd.notna(r["Wards"]):
            seen.setdefault(str(r["Wards"]).strip(), set()).add(
                "workorders_2018_2023")
    return seen


def resolve(key: str, master: pd.DataFrame) -> tuple[int | None, str, float]:
    """Return (ward_no, method, score) for a normalised name key."""
    exact = master.loc[master["key"] == key, "ward_no"]
    if len(exact):
        return int(exact.iloc[0]), "exact", 1.0

    if key in MANUAL:
        return MANUAL[key], "manual", 1.0

    keys = master["key"].tolist()
    scored = sorted(
        ((difflib.SequenceMatcher(None, key, k).ratio(), k) for k in keys),
        reverse=True,
    )
    if not scored:
        return None, "unresolved", 0.0
    best_score, best_key = scored[0]
    runner = scored[1][0] if len(scored) > 1 else 0.0
    if best_score >= FUZZY_CUTOFF and (best_score - runner) >= FUZZY_MARGIN:
        no = int(master.loc[master["key"] == best_key, "ward_no"].iloc[0])
        return no, "fuzzy", round(best_score, 3)
    if best_score >= FUZZY_CUTOFF:
        # too close to call between two wards - never guess silently
        return None, "ambiguous", round(best_score, 3)
    return None, "unresolved", round(best_score, 3)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    master = load_master()
    print(f"ward master: {len(master)} wards")

    seen = observed_names()
    print(f"distinct ward-name strings across sources: {len(seen)}")

    rows = []
    for raw_name, sources in sorted(seen.items()):
        key = norm(raw_name)
        ward_no, method, score = resolve(key, master)
        canon = None
        if ward_no is not None:
            canon = master.loc[master["ward_no"] == ward_no, "ward_name"].iloc[0]
        rows.append({
            "observed_name": raw_name,
            "normalised": key,
            "ward_no": ward_no,
            "canonical_name": canon,
            "match_method": method,
            "match_score": score,
            "sources": ";".join(sorted(sources)),
        })

    cw = pd.DataFrame(rows).sort_values(
        ["ward_no", "observed_name"], na_position="last")

    # attach the 198 -> 225/243 delimitation mapping where available
    try:
        x = pd.read_csv(RAW / "ward_crosswalk_old_new.csv", dtype=str)
        x.columns = [c.strip() for c in x.columns]
        x = x.rename(columns={"Old Ward Num": "ward_no",
                              "New Ward Num": "ward_no_225",
                              "New Ward Name": "ward_name_225"})
        x = x[["ward_no", "ward_no_225", "ward_name_225"]].dropna(subset=["ward_no"])
        x["ward_no"] = pd.to_numeric(x["ward_no"], errors="coerce")
        x = x.dropna(subset=["ward_no"]).drop_duplicates("ward_no")
        x["ward_no"] = x["ward_no"].astype(int)
        cw = cw.merge(x, on="ward_no", how="left")
    except Exception as exc:                      # noqa: BLE001
        print(f"  (delimitation mapping skipped: {exc})")

    dest = OUT / "ward_crosswalk.csv"
    cw.to_csv(dest, index=False)

    counts = cw["match_method"].value_counts()
    print("\nmatch method:")
    for k, v in counts.items():
        print(f"  {k:12s} {v:4d}")
    resolved = cw["ward_no"].notna().sum()
    print(f"\nresolved {resolved}/{len(cw)} "
          f"({100 * resolved / len(cw):.1f}%)")
    print(f"distinct wards covered: {cw['ward_no'].nunique()} / 198")

    # Only grievance-sourced names are join-critical.
    griev = cw["sources"].str.contains("grievances")
    gbad = cw[griev & cw["ward_no"].isna()]
    print(f"\ngrievance names: {griev.sum()} seen, "
          f"{(griev & cw['ward_no'].notna()).sum()} resolved, {len(gbad)} unresolved")
    if len(gbad):
        print("UNRESOLVED (join-critical) - add to MANUAL:")
        for _, r in gbad.iterrows():
            print(f"  {r['observed_name']!r:45s} best={r['match_score']} "
                  f"({r['match_method']}) [{r['sources']}]")
    else:
        print("  -> every grievance ward name resolves.")

    obad = cw[~griev & cw["ward_no"].isna()]
    if len(obad):
        print(f"\nunresolved work-order names ({len(obad)}) - reference only, "
              "not used as a join key:")
        print("  " + ", ".join(repr(x) for x in obad["observed_name"]))

    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
