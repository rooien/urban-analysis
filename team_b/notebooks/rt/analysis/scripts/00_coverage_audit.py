"""
Stage 00 - coverage audit. For every treatment segment outside the 4
sensor-covered CBD streets, checks real Nearmap survey coverage at both
segment endpoints and classifies each survey as before/during
construction/after. This is the gate for everything downstream: a
segment with no usable before+after coverage can't go into the imagery
pipeline at all, and this is how we find out which those are before
sinking manual-counting effort into them.

Requires NEARMAP_API_KEY set as an environment variable -- never read
from a file, never logged, never committed. Run it yourself:

    $env:NEARMAP_API_KEY = "your-key-here"
    python 00_coverage_audit.py

Reuses construction_window.get_construction_window() and
survey_date_lookup.build_lookup() rather than reimplementing the
transition-detection or classification logic.

Caches each endpoint's raw coverage-API response to disk as it goes, so
an interruption (rate limit, crash, closed laptop) doesn't mean
re-fetching everything -- re-running the script picks up where it left
off.
"""
import json
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(__file__))
from construction_window import get_construction_window
from survey_date_lookup import build_lookup

GPKG_PATH = r"C:\Users\erteo\Desktop\26T2\SIT378 - Project B\260724 street spatial files\streets_spatial.gpkg"
SENSOR_STREETS = {"WILLIAM STREET", "LA TROBE STREET", "PEEL STREET", "EXHIBITION STREET"}

SCRIPT_DIR = Path(__file__).parent
CACHE_DIR = SCRIPT_DIR.parent / "data" / "coverage_cache"
OUT_CSV = SCRIPT_DIR.parent / "docs" / "capture_matrix.csv"
OUT_XML = SCRIPT_DIR / "qgis_xyz_connections_full.xml"

REQUEST_DELAY_SECONDS = 0.3
MAX_RETRIES = 3
WINDOW_DAYS = 365  # 12 months either side of construction, matching the pilot's convention


def load_treatment_segments() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(GPKG_PATH)
    gdf = gdf[gdf["treatment_or_control"] == "treatment"]
    gdf = gdf[~gdf["street_name"].isin(SENSOR_STREETS)]
    return gdf.to_crs(epsg=4326)


def fetch_coverage(lon: float, lat: float, api_key: str, cache_key: str) -> list[dict]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())["surveys"]

    url = f"https://api.nearmap.com/coverage/v2/point/{lon},{lat}"
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params={"apikey": api_key, "limit": 200}, timeout=30)
            if resp.status_code == 429:
                wait = 5 * attempt
                print(f"    rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            cache_file.write_text(json.dumps(data))
            time.sleep(REQUEST_DELAY_SECONDS)
            return data["surveys"]
        except requests.RequestException as e:
            last_error = e
            time.sleep(2 * attempt)
    print(f"    FAILED after {MAX_RETRIES} attempts: {last_error}")
    return []


def main():
    api_key = os.environ.get("NEARMAP_API_KEY")
    if not api_key:
        sys.exit("NEARMAP_API_KEY not set. Run: $env:NEARMAP_API_KEY = \"your-key-here\"")

    segments = load_treatment_segments()
    print(f"{len(segments)} treatment segments to audit (outside sensor-covered streets)\n")

    all_rows = []
    skipped_no_window = []
    skipped_no_coverage = []

    for i, seg in enumerate(segments.itertuples(), 1):
        seg_id = int(seg.street_segment_id)  # gpkg stores this as float64
        street_name = seg.street_name
        print(f"[{i}/{len(segments)}] {seg_id} {street_name}")

        window = get_construction_window(seg_id)
        if window is None:
            print("    skipped: no clean single construction transition")
            skipped_no_window.append(seg_id)
            continue
        construction_start, construction_end = window

        coords = list(seg.geometry.coords)
        lon_a, lat_a = coords[0]
        lon_b, lat_b = coords[-1]

        surveys_a = fetch_coverage(lon_a, lat_a, api_key, f"{seg_id}_A")
        surveys_b = fetch_coverage(lon_b, lat_b, api_key, f"{seg_id}_B")

        # Bound to 12 months either side of construction -- without this, segments
        # with long Nearmap histories (e.g. 100+ surveys) pull in years of
        # irrelevant dates that were never going to be counted anyway.
        window_start = (construction_start - timedelta(days=WINDOW_DAYS)).isoformat()
        window_end = (construction_end + timedelta(days=WINDOW_DAYS)).isoformat()
        dates_a = [s["captureDate"] for s in surveys_a if window_start <= s["captureDate"] <= window_end]
        dates_b = [s["captureDate"] for s in surveys_b if window_start <= s["captureDate"] <= window_end]

        if not dates_a and not dates_b:
            print("    skipped: no coverage at either endpoint")
            skipped_no_coverage.append(seg_id)
            continue

        lookup = build_lookup(seg_id, street_name, dates_a, dates_b, construction_start, construction_end)
        all_rows.append(lookup)

    if not all_rows:
        sys.exit("No segments produced usable coverage data -- nothing to write.")

    matrix = pd.concat(all_rows, ignore_index=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(OUT_CSV, index=False)

    print(f"\nWrote {len(matrix)} rows across {matrix['street_segment_id'].nunique()} segments to {OUT_CSV}")
    print(f"Skipped (no construction window): {len(skipped_no_window)} -> {skipped_no_window}")
    print(f"Skipped (no coverage at all): {len(skipped_no_coverage)} -> {skipped_no_coverage}")

    write_xyz_xml(matrix)


def write_xyz_xml(matrix: pd.DataFrame):
    usable = matrix[matrix["period"].isin(["before", "after"]) & (matrix["coverage"] == "both ends")]
    feasible_segments = set(
        usable[usable["period"] == "before"]["street_segment_id"]
    ) & set(
        usable[usable["period"] == "after"]["street_segment_id"]
    )
    feasible = usable[usable["street_segment_id"].isin(feasible_segments)]

    entries = []
    for row in feasible.itertuples():
        safe_name = "".join(c if c.isalnum() else "_" for c in row.street_name.title())
        name = f"{row.street_segment_id}_{safe_name}_{row.period}_{row.captureDate}"
        url = (
            f"https://api.nearmap.com/tiles/v3/Vert/%7Bz%7D/%7Bx%7D/%7By%7D.img"
            f"?apikey=YOUR_API_KEY&amp;until={row.captureDate}"
        )
        entries.append(
            f'<xyztiles url="{url}" password="" name="{name}" referer="" '
            f'zmax="21" authcfg="" username="" zmin="0"/>'
        )

    xml = (
        "<!--\n"
        "Bulk XYZ connection list for every feasible treatment segment (both-ends\n"
        "coverage, at least one before + one after date). Find & Replace\n"
        '"YOUR_API_KEY" with your real key before importing into QGIS.\n'
        "-->\n"
        '<qgsXYZTilesConnections version="1.0">\n'
        + "\n".join(entries)
        + "\n</qgsXYZTilesConnections>\n"
    )
    OUT_XML.write_text(xml)
    print(f"\nWrote {len(entries)} XYZ connections ({len(feasible_segments)} feasible segments) to {OUT_XML}")


if __name__ == "__main__":
    main()
