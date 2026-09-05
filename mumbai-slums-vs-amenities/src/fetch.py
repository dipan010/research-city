"""Download the Mumbai source layers this project depends on.

Resource URLs are resolved from the CKAN API by dataset title + resource name,
so the script keeps working if OpenCity re-uploads a file under a new UUID.
Every Mumbai geospatial layer on the platform is pulled here, including the
ones the analysis only uses as context, so the manifest records the whole set.
"""
import json
import pathlib
import sys
import time

import requests

API = "https://data.opencity.in/api/3/action/package_search"
RAW = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (mumbai-slums-vs-amenities research script)"}

# (dataset title, resource-name substring, local filename)
WANTED = [
    # --- base geography -------------------------------------------------
    ("Mumbai Wards Map", "Mumbai Wards Map", "wards.kml"),
    ("Mumbai - Slum Cluster Map", "Slum Clusters Map", "slums.kml"),

    # --- amenity layers -------------------------------------------------
    ("Mumbai Public Toilets", "Map of Public Toilets", "toilets.kml"),
    ("Mumbai City Public Health Centres", "Dispensaries", "health_dispensaries.kml"),
    ("Mumbai City Public Health Centres", "UPHCs", "health_uphc.kml"),
    ("Mumbai City Public Health Centres", "Public Hospitals", "health_hospitals.kml"),
    ("Mumbai City Public Health Centres", "Maternity", "health_maternity.kml"),
    ("Mumbai Schools Locations", "Municipal Primary and Secondary", "schools_municipal.kml"),
    ("Mumbai Schools Locations", "Aided Schools", "schools_aided.kml"),
    ("Mumbai Schools Locations", "Unaided Schools", "schools_unaided.kml"),
    ("Mumbai - Public Gardens, Parks and Zoos", "Parks, Gardens and Zoos", "parks.kml"),
    ("Mumbai Fire Stations", "Fire Stations Map", "fire_stations.kml"),
    ("Police Station Locations in Mumbai", "Police Stations Location", "police_stations.kml"),
    ("Mumbai BEST Bus Stops and Depots Data", "BEST Stops and Depots", "best_stops.kml"),
    ("Mumbai Funeral and Cremation Sites", "Funeral and Cremation Sites", "funeral_sites.kml"),
    ("Mumbai Parking", "Parking Lots", "parking.kml"),
    ("Mumbai Suburban Network 2025", "Suburban Line Stations", "rail_stations.kml"),

    # --- denominators ---------------------------------------------------
    # Ward-level population, and the census-ward -> BMC-ward lookup.
    ("Mumbai - Ward wise Census Data", "Mumbai - Census Data 2011", "census_wards.csv"),
    # Households per census ward, for weighting the HH-14 percentages.
    ("Mumbai - Ward wise Census Data", "Mumbai City Primary Census Abstract", "pca_city.csv"),
    ("Mumbai - Ward wise Census Data", "Mumbai Suburban District Primary Census", "pca_suburban.csv"),
    # Houselisting table HH-14 - latrine access by ward. The demand side.
    ("Mumbai - Ward wise Census Data", "Mumbai City Houselisting", "houselisting_city.xlsx"),
    ("Mumbai - Ward wise Census Data", "Mumbai Suburban Houselisting", "houselisting_suburban.xlsx"),
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
                return res, d
    return None, None


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    print("fetching CKAN catalogue ...")
    datasets = catalogue()
    print(f"  {len(datasets)} datasets\n")

    manifest = {}
    for title, substr, fname in WANTED:
        dest = RAW / fname
        res, pkg = resolve(datasets, title, substr)
        if res is None:
            print(f"!! could not resolve: {title} :: {substr}")
            continue
        # Vintages differ across these layers (slums are 2015, census 2011, the
        # amenity layers are undated BMC extracts). Record whatever dates CKAN
        # carries so the spread is auditable rather than assumed.
        manifest[fname] = {
            "dataset": title,
            "resource": res.get("name"),
            "url": res["url"],
            "format": res.get("format"),
            "resource_created": res.get("created"),
            "resource_modified": res.get("last_modified") or res.get("metadata_modified"),
            "dataset_modified": pkg.get("metadata_modified"),
        }
        if dest.exists() and dest.stat().st_size > 0:
            print(f"  cached  {fname}")
            continue
        for attempt in (1, 2, 3):
            try:
                resp = requests.get(res["url"], headers=UA, timeout=300)
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
    print(f"\nmanifest -> {RAW / 'manifest.json'}  ({len(manifest)} resources)")


if __name__ == "__main__":
    sys.exit(main())
