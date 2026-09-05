"""Download the BBMP source files this project depends on.

Resource URLs are resolved from the CKAN API by dataset title + resource name,
so the script keeps working if OpenCity re-uploads a file under a new UUID.
"""
import json
import pathlib
import sys
import time

import requests

API = "https://data.opencity.in/api/3/action/package_search"
RAW = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (bbmp-complaints-vs-spending research script)"}

# (dataset title, resource-name substring, local filename)
WANTED = [
    ("BBMP Ward Information", "BBMP Ward Information", "ward_master.csv"),
    ("BBMP Ward Information", "Constituencies to Wards Mapping for Old and New Wards",
     "ward_crosswalk_old_new.csv"),
    ("BBMP Work Orders Categorised (2018-2023)", "Ward Wise Work Orders Gross",
     "workorders_ward_category_gross.csv"),
    ("BBMP Work Orders Categorised (2018-2023)", "Ward Wise Work Orders Net",
     "workorders_ward_category_net.csv"),
    # 198-ward boundaries - the only BBMP ward KML matching this ward regime.
    ("BBMP Ward Information", "BBMP Ward Map - 2015", "bbmp_ward_map_2015.kml"),
    # Ward population, for the per-resident denominator.
    ("Bengaluru Data - Census 2011", "Bengaluru Ward-wise Census Data - 2011",
     "ward_population_2011.csv"),
] + [
    ("BBMP Grievances Data", f"BBMP Grievances {y}", f"grievances_{y}.csv")
    for y in range(2020, 2025)
]


def catalogue():
    """Pull every dataset record once, so we can look resources up locally."""
    out = []
    for start in (0, 1000):
        r = requests.get(API, params={"rows": 1000, "start": start},
                         headers=UA, timeout=120)
        r.raise_for_status()
        out += r.json()["result"]["results"]
    return out


def resolve(datasets, title, res_substr):
    for d in datasets:
        if d["title"] != title:
            continue
        for res in d.get("resources", []):
            if res_substr.lower() in (res.get("name") or "").lower():
                return res["url"], res.get("name")
    return None, None


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    print("fetching CKAN catalogue ...")
    datasets = catalogue()
    print(f"  {len(datasets)} datasets\n")

    manifest = {}
    for title, substr, fname in WANTED:
        dest = RAW / fname
        url, resname = resolve(datasets, title, substr)
        if url is None:
            print(f"!! could not resolve: {title} :: {substr}")
            continue
        manifest[fname] = {"dataset": title, "resource": resname, "url": url}
        if dest.exists() and dest.stat().st_size > 0:
            print(f"  cached  {fname}")
            continue
        for attempt in (1, 2, 3):
            try:
                resp = requests.get(url, headers=UA, timeout=300)
                resp.raise_for_status()
                dest.write_bytes(resp.content)
                print(f"  got     {fname}  ({len(resp.content):,} bytes)")
                break
            except Exception as exc:              # noqa: BLE001
                print(f"  retry {attempt} {fname}: {exc}")
                time.sleep(2 * attempt)
        else:
            print(f"!! failed {fname}")

    (RAW / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nmanifest -> {RAW / 'manifest.json'}")


if __name__ == "__main__":
    sys.exit(main())
