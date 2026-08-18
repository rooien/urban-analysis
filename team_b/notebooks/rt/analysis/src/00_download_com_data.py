"""
00 — Download City of Melbourne open parking data.

Two kinds of file:

1. Reference layers (small, API export)
   - on-street-parking-bays          bay polygons + marker_id
   - on-street-parking-bay-sensors   live sensor points (CURRENT snapshot only)
   - on-street-car-park-bay-restrictions

2. Historical event archives (large, static S3 zips), one per calendar year.
   Each row = one parking event (arrival -> departure) for one bay.
   Total ~9 GB compressed / ~300 M rows for 2011-2020. Download selectively.

Join keys:  sensors <-> bays via marker_id ;  sensors <-> restrictions via bay_id.
The historical event files carry StreetMarker, which is the same id as marker_id.

Run:
    python analysis/src/00_download_com_data.py --reference
    python analysis/src/00_download_com_data.py --years 2016 2017 2018 2019
"""
import argparse
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as C

PORTAL = "https://data.melbourne.vic.gov.au"

REFERENCE = {
    "on-street-parking-bays": "geojson",
    "on-street-parking-bay-sensors": "geojson",
    "on-street-car-park-bay-restrictions": "csv",
}

# All ten archives verified against the portal, 4 Aug 2026.
# year: (socrata id, compressed size, row count)
ARCHIVES = {
    2011: ("vkxi-k7ps", "592.8 MB", 21_800_000),
    2012: ("vbe9-m4tk", "1.51 GB", 52_500_000),
    2013: ("7jq6-k9kf", "1.24 GB", 43_200_000),
    2014: ("t6hb-9uf2", "1.56 GB", 51_500_000),
    2015: ("apua-t2tb", "1.17 GB", 37_500_000),
    2016: ("dj7e-rdx9", "1.07 GB", 34_100_000),
    2017: ("u9sa-j86i", "1.13 GB", 35_900_000),
    2018: ("5532-ig9r", "504 MB", 30_200_000),
    2019: ("7pgd-bdf2", "717.1 MB", 42_700_000),
    2020: ("4n3a-s6rn", "258.5 MB", 14_200_000),   # Jan-May only
}
ARCHIVE_IDS = {y: v[0] for y, v in ARCHIVES.items()}
ALL_YEARS = sorted(ARCHIVES)

DATASET_SLUG = {y: f"on-street-car-parking-sensor-data-{y}" for y in range(2011, 2020)}
DATASET_SLUG[2020] = "on-street-car-parking-sensor-data-2020-jan-may"


def resolve_archive_url(year: int) -> str:
    if year in ARCHIVE_IDS:
        return f"https://opendatasoft-s3.s3.amazonaws.com/downloads/archive/{ARCHIVE_IDS[year]}.zip"
    slug = DATASET_SLUG[year]
    page = f"{PORTAL}/explore/dataset/{slug}/information/"
    html = urllib.request.urlopen(page, timeout=60).read().decode("utf-8", "ignore")
    m = re.search(r"https://opendatasoft-s3\.s3\.amazonaws\.com/downloads/archive/[\w-]+\.zip", html)
    if not m:
        raise RuntimeError(f"No archive link found on {page} — download manually.")
    return m.group(0)


def fetch(url: str, dest: Path):
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  skip (exists): {dest.name}")
        return
    print(f"  -> {dest.name}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.rename(dest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", action="store_true")
    ap.add_argument("--years", nargs="*", type=int, default=[])
    ap.add_argument("--all", action="store_true", help="all ten archives, 2011 - 2020 May (~9.8 GB)")
    a = ap.parse_args()
    if a.all:
        a.years = ALL_YEARS
        a.reference = True
        total = sum(v[2] for v in ARCHIVES.values())
        print(f"Full archive: {len(ALL_YEARS)} files, ~9.8 GB compressed, {total/1e6:.0f} M rows\n")

    if a.reference:
        print("Reference layers:")
        for slug, fmt in REFERENCE.items():
            url = (
                f"{PORTAL}/api/explore/v2.1/catalog/datasets/{slug}"
                f"/exports/{fmt}?lang=en&timezone=Australia%2FMelbourne"
            )
            fetch(url, C.RAW / f"{slug}.{fmt}")

    for y in a.years:
        sz, rows = ARCHIVES[y][1], ARCHIVES[y][2]
        print(f"Sensor archive {y}  ({sz}, {rows/1e6:.1f} M rows):")
        fetch(resolve_archive_url(y), C.RAW / f"parking_events_{y}.zip")

    if not a.reference and not a.years:
        ap.print_help()


if __name__ == "__main__":
    main()
