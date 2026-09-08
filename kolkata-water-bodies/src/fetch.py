"""Download the Kolkata source files this project depends on.

Resource URLs are resolved from the CKAN API by dataset title + resource name,
so the script keeps working if OpenCity re-uploads a file under a new UUID.

Two notes on what is and is not pulled here:

  * `KMC Pay-and-use Toilets (2018)` is downloaded even though nothing uses it.
    It is a byte-identical duplicate of `KMC Schools`, and `verify_duplicate()`
    proves that rather than asserting it, because "Kolkata publishes no public
    toilet data" is a claim the page makes and it needs evidence in the repo.
  * The ward KML is pulled under the neutral name `wards.kml`. Its resource is
    called "Kolkata Wards Map 2022" but it holds the pre-2015, 141-ward
    boundary set; the manifest records the resource name so the mismatch stays
    visible.
"""
import hashlib
import json
import pathlib
import sys
import time

import requests

API = "https://data.opencity.in/api/3/action/package_search"
RAW = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (kolkata-water-bodies research script)"}

# (dataset title, resource-name substring, local filename)
WANTED = [
    # --- the analysis proper ------------------------------------------
    ("Kolkata Water Bodies Census Data", "Water Census Map", "water_bodies.kml"),
    ("Kolkata Wards Information", "Wards Map", "wards.kml"),

    # --- denominators and crosswalks ----------------------------------
    # Registered electors per ward: the only complete per-ward denominator
    # KMC publishes that is not sourced from the (smaller) Kolkata district.
    ("Kolkata KMC Elections Data", "Election Results 2015", "election_2015.csv"),
    ("Kolkata KMC Elections Data", "Election Results 2010", "election_2010.csv"),
    # Borough -> ward lookup, and the only published one.
    ("Kolkata Municipal Corporation Offices", "Borough Committees",
     "boroughs.csv"),

    # --- context and data-quality evidence ----------------------------
    ("Kolkata Microwatersheds Map", "Microwatersheds", "microwatersheds.geojson"),
    ("Kolkata Schools", "KMC Schools", "schools.csv"),
    ("Kolkata Civic Amenities", "Pay-and-use Toilets", "toilets.csv"),
    ("Kolkata Civic Amenities", "Parks and Gardens", "parks.csv"),
    ("Kolkata Health Services", "Dispensaries", "dispensaries.csv"),
    ("Kolkata Public Service Centres", "Drainage Pumping Stations",
     "pumping_stations.csv"),
]

# Files whose byte-identity is a finding in its own right.
DUPLICATE_CLAIM = ("toilets.csv", "schools.csv")


def catalogue():
    """Every Kolkata dataset record, so resources resolve locally.

    Paged at 25. The portal returns 502 on large `rows` values, so this is
    deliberately small and retried rather than fetched in one call.
    """
    out, start = [], 0
    while True:
        j = _get({"q": "Kolkata", "rows": 25, "start": start})
        results = j["result"]["results"]
        out += results
        start += 25
        if start >= j["result"]["count"] or not results:
            break
        time.sleep(1)
    return out


def _get(params, tries=5):
    for i in range(tries):
        try:
            r = requests.get(API, params=params, headers=UA, timeout=120)
            if r.status_code == 200:
                return r.json()
            print(f"  HTTP {r.status_code} on {params}", file=sys.stderr)
        except requests.RequestException as e:
            print(f"  {e}", file=sys.stderr)
        time.sleep(2 * (i + 1))
    raise SystemExit(f"catalogue request failed: {params}")


def resolve(datasets, title, res_substr):
    for d in datasets:
        if d.get("title") != title:
            continue
        for res in d.get("resources", []):
            if res_substr.lower() in (res.get("name") or "").lower():
                return res
    return None


def download(url, dest):
    r = requests.get(url, headers=UA, timeout=300, allow_redirects=True)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return len(r.content)


def verify_duplicate(manifest):
    """Prove the toilets resource is the schools file, or say it changed.

    Recorded as a manifest entry rather than an assertion: if OpenCity fixes
    the upload this should surface as a corrected finding, not a crash.
    """
    a, b = (RAW / DUPLICATE_CLAIM[0]), (RAW / DUPLICATE_CLAIM[1])
    if not (a.exists() and b.exists()):
        return None
    da, db = hashlib.md5(a.read_bytes()).hexdigest(), hashlib.md5(b.read_bytes()).hexdigest()
    same = da == db
    manifest["toilets_is_schools"] = {
        "toilets_md5": da, "schools_md5": db, "identical": same,
    }
    print(f"\n  pay-and-use toilets == schools: {same}  ({da})")
    if not same:
        print("  NOTE: the duplicate has been fixed upstream. The page claims "
              "Kolkata publishes no toilet data - re-check before publishing.")
    return same


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    print("fetching catalogue ...")
    datasets = catalogue()
    print(f"  {len(datasets)} Kolkata datasets\n")

    manifest, missing = {"resources": {}}, []
    for title, substr, fname in WANTED:
        res = resolve(datasets, title, substr)
        if res is None:
            print(f"  MISSING  {title} :: {substr}")
            missing.append(f"{title} :: {substr}")
            continue
        dest = RAW / fname
        size = download(res["url"], dest)
        manifest["resources"][fname] = {
            "dataset": title,
            "resource": res.get("name"),
            "format": res.get("format"),
            "url": res["url"],
            "bytes": size,
        }
        print(f"  {fname:26s} {size/1024:8.0f} KB  <- {res.get('name')}")

    verify_duplicate(manifest)

    if missing:
        raise SystemExit("\nunresolved resources:\n  " + "\n  ".join(missing))
    (RAW / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nmanifest -> {RAW / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
