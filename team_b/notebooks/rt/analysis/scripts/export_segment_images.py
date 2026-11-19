"""
Exports one stitched Nearmap image per (segment, date) row in the counting-team's
merged counts CSV, using the same tile endpoint and `until=<date>` mechanism already
proven working in the QGIS XYZ connections (qgis_xyz_connections_*.xml) -- just called
directly over HTTP instead of through QGIS, and stitched into one raster per segment
instead of viewed as live map tiles.

No new Nearmap product needed: this is the same Tile API already in use, scripted.

SECURITY: the API key is read from the NEARMAP_API_KEY environment variable only.
Never hardcode it here, never pass it as a CLI argument (shows up in shell history),
never commit an image cache that embeds it in a filename or log line. Set it once with
(Windows, permanent across terminals):
    setx NEARMAP_API_KEY "your-key-here"
then open a new terminal so the variable is picked up.

Usage:
    python export_segment_images.py --counts "C:\\Users\\erteo\\Downloads\\USIA_Merged_Parking_Counts_All_Pairs (1).csv"
"""
import argparse
import math
import os
import time
from io import BytesIO

import geopandas as gpd
import pandas as pd
import requests
from PIL import Image

GEOMETRY_PATH = (
    r"C:\Users\erteo\Desktop\26T2\SIT378 - Project B\260724 street spatial files"
    r"\streets_spatial.gpkg"
)
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "segment_images")
TILE_URL = "https://api.nearmap.com/tiles/v3/Vert/{z}/{x}/{y}.img"
ZOOM = 21  # matches the "Vert" scale seen for most surveys in data/coverage_cache/*.json
BUFFER_M = 15  # metres either side of the segment centerline, in EPSG:7899 (metric)
TILE_PX = 256


def lonlat_to_tile(lon: float, lat: float, zoom: int) -> tuple[int, int]:
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def tile_bounds_lonlat(x: int, y: int, zoom: int) -> tuple[float, float, float, float]:
    """Returns (west, north, east, south) lon/lat bounds of tile x,y at zoom."""
    n = 2 ** zoom
    west = x / n * 360.0 - 180.0
    east = (x + 1) / n * 360.0 - 180.0
    north = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    south = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return west, north, east, south


def load_segment_bbox_lonlat(segment_id: int, expected_street_name: str = None) -> tuple[float, float, float, float]:
    """Returns buffered (minx, miny, maxx, maxy) in EPSG:4326 for one segment.

    The join to streets_spatial.gpkg is by street_segment_id alone -- the street name
    is not part of the lookup. That ID column is a documented dtype trap elsewhere in
    this repo (construction_window.py), so as a cheap sanity check, when the caller
    supplies the street name from the counts CSV, cross-check it against the gpkg's
    street_name for the matched row (normalized for case and ST/STREET abbreviation,
    another documented gotcha here) rather than trusting the numeric ID blindly.
    """
    gdf = gpd.read_file(GEOMETRY_PATH)
    row = gdf[gdf["street_segment_id"] == segment_id]
    if row.empty:
        raise ValueError(f"segment_id {segment_id} not found in {GEOMETRY_PATH}")

    if expected_street_name:
        def normalize(name: str) -> str:
            return name.strip().upper().replace(" STREET", " ST").replace(" ROAD", " RD")

        gpkg_name = normalize(row.iloc[0]["street_name"])
        csv_name = normalize(expected_street_name)
        if gpkg_name != csv_name:
            raise ValueError(
                f"segment_id {segment_id}: gpkg street_name '{row.iloc[0]['street_name']}' "
                f"does not match counts CSV street_name '{expected_street_name}' -- "
                "likely an ID mix-up, not proceeding."
            )

    buffered = row.geometry.buffer(BUFFER_M)  # still EPSG:7899, metres -> correct buffer
    buffered_wgs84 = gpd.GeoSeries(buffered, crs=row.crs).to_crs(epsg=4326)
    return buffered_wgs84.total_bounds  # minx, miny, maxx, maxy = west, south, east, north


def fetch_tile(z: int, x: int, y: int, until_date: str, api_key: str) -> Image.Image:
    url = TILE_URL.format(z=z, x=x, y=y)
    resp = requests.get(url, params={"apikey": api_key, "until": until_date}, timeout=30)
    resp.raise_for_status()
    return Image.open(BytesIO(resp.content)).convert("RGB")


def stitch_segment_image(minx, miny, maxx, maxy, zoom, until_date, api_key) -> Image.Image:
    """minx/miny/maxx/maxy in EPSG:4326 (west, south, east, north)."""
    x0, y0 = lonlat_to_tile(minx, maxy, zoom)  # top-left (north-west)
    x1, y1 = lonlat_to_tile(maxx, miny, zoom)  # bottom-right (south-east)
    x_lo, x_hi = min(x0, x1), max(x0, x1)
    y_lo, y_hi = min(y0, y1), max(y0, y1)

    n_cols = x_hi - x_lo + 1
    n_rows = y_hi - y_lo + 1
    canvas = Image.new("RGB", (n_cols * TILE_PX, n_rows * TILE_PX))

    for row, ty in enumerate(range(y_lo, y_hi + 1)):
        for col, tx in enumerate(range(x_lo, x_hi + 1)):
            tile = fetch_tile(zoom, tx, ty, until_date, api_key)
            canvas.paste(tile, (col * TILE_PX, row * TILE_PX))
            time.sleep(0.1)  # be polite to the tile endpoint

    # Crop canvas down to the exact requested bbox using pixel-space interpolation
    west0, north0, east0, south0 = tile_bounds_lonlat(x_lo, y_lo, zoom)
    _, _, east1, south1 = tile_bounds_lonlat(x_hi, y_hi, zoom)
    canvas_w_lon = east1 - west0
    canvas_h_lat = north0 - south1

    px_per_lon = canvas.width / canvas_w_lon
    px_per_lat = canvas.height / canvas_h_lat

    left = int((minx - west0) * px_per_lon)
    right = int((maxx - west0) * px_per_lon)
    top = int((north0 - maxy) * px_per_lat)
    bottom = int((north0 - miny) * px_per_lat)

    return canvas.crop((left, top, right, bottom))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--counts", required=True, help="Path to USIA_Merged_Parking_Counts_All_Pairs CSV")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N rows (for a quick test)")
    args = parser.parse_args()

    api_key = os.environ.get("NEARMAP_API_KEY")
    if not api_key:
        raise SystemExit(
            "NEARMAP_API_KEY is not set. Run: setx NEARMAP_API_KEY \"your-key\" "
            "then open a NEW terminal (setx doesn't affect the current one)."
        )

    os.makedirs(OUT_DIR, exist_ok=True)

    counts = pd.read_csv(args.counts)
    counts["Date"] = pd.to_datetime(counts["Date"], dayfirst=True)
    rows = counts.drop_duplicates(subset=["Segment ID", "Date"])
    if args.limit:
        rows = rows.head(args.limit)

    geom_cache: dict[int, tuple[float, float, float, float]] = {}

    for _, row in rows.iterrows():
        segment_id = int(row["Segment ID"])
        date_str = row["Date"].strftime("%Y-%m-%d")
        out_path = os.path.join(OUT_DIR, f"{segment_id}_{date_str}.png")
        if os.path.exists(out_path):
            continue  # already exported

        if segment_id not in geom_cache:
            geom_cache[segment_id] = load_segment_bbox_lonlat(segment_id, row["Street Name"])
        minx, miny, maxx, maxy = geom_cache[segment_id]

        print(f"[*] Exporting segment {segment_id} @ {date_str}...")
        try:
            img = stitch_segment_image(minx, miny, maxx, maxy, ZOOM, date_str, api_key)
            img.save(out_path)
        except requests.HTTPError as e:
            print(f"[!] Failed for segment {segment_id} @ {date_str}: {e}")

    print(f"\nDone. Images in {OUT_DIR}")


if __name__ == "__main__":
    main()
