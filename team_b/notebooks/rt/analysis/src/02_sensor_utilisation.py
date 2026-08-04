"""
02 — City of Melbourne parking sensor EDA: baseline vs post-intervention utilisation.

Method
------
The archives are EVENT records, not occupancy snapshots: one row per vehicle
arrival/departure with a duration. Utilisation is not a row count — you must
convert events to occupied-minutes and divide by available-minutes.

    utilisation(bay, hour) = occupied_minutes / 60

Pipeline
    1. Load bay geometry, reproject WGS84 -> EPSG:7899.
    2. Spatially join bays to the 315 study segments (nearest within MAX_SNAP m).
    3. Stream each yearly archive in chunks, keep only rows whose StreetMarker
       falls on a study segment, explode each event into hourly occupied-minutes.
    4. Aggregate to segment x date x hour, then to pre/post windows around the
       intervention date from 01_build_intervention_dates.py.

Only ~11 of 96 treatment segments are usable for before/after here — see
docs/data_audit.md. Everything else is imagery-only.

Run:  python analysis/src/02_sensor_utilisation.py --years 2012 2013 2014
"""
import argparse
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as C

MAX_SNAP = 25          # m — bay centroid to street centreline
CHUNK = 2_000_000      # rows per read_csv chunk
MAX_EVENT_HOURS = 24   # discard implausible durations

# Column names drift slightly between years; normalise defensively.
COLMAP = {
    "streetmarker": "marker_id",
    "street_marker": "marker_id",
    "devideid": "device_id",
    "arrivaltime": "arrival",
    "departuretime": "departure",
    "in_time": "arrival",
    "out_time": "departure",
}


def build_bay_segment_lookup() -> pd.DataFrame:
    """marker_id -> street_segment_id, via nearest-centreline spatial join."""
    bays = gpd.read_file(C.RAW / "on-street-parking-bays.geojson")
    bays = bays.set_crs(C.CRS_WGS84, allow_override=True).to_crs(C.CRS_PROJECT)
    bays["geometry"] = bays.geometry.centroid

    mcol = next(c for c in bays.columns if c.lower() in ("marker_id", "kerbsideid", "bay_id"))
    bays = bays.rename(columns={mcol: "marker_id"})[["marker_id", "geometry"]].dropna()

    st = gpd.read_file(C.STREETS_GPKG, layer=C.STREETS_LAYER).to_crs(C.CRS_PROJECT)
    st["sid"] = pd.to_numeric(st["street_segment_id"], errors="coerce").astype("Int64").astype(str)
    st = st[["sid", "street_name", "geometry"]]

    joined = gpd.sjoin_nearest(bays, st, how="inner", max_distance=MAX_SNAP, distance_col="snap_m")
    joined["marker_id"] = joined["marker_id"].astype(str).str.strip().str.upper()
    lookup = joined.sort_values("snap_m").drop_duplicates("marker_id")
    lookup = lookup[["marker_id", "sid", "street_name", "snap_m"]]
    lookup.to_csv(C.INTERIM / "bay_segment_lookup.csv", index=False)
    print(f"bays matched to study segments: {len(lookup)} across {lookup.sid.nunique()} segments")
    return lookup


def explode_to_hours(df: pd.DataFrame) -> pd.DataFrame:
    """Event rows -> occupied minutes per (marker_id, hour)."""
    df = df.dropna(subset=["arrival", "departure"])
    df = df[df["departure"] > df["arrival"]]
    dur_h = (df["departure"] - df["arrival"]).dt.total_seconds() / 3600
    df = df[dur_h.between(0, MAX_EVENT_HOURS)]
    if df.empty:
        return pd.DataFrame(columns=["marker_id", "hour_ts", "occ_min"])

    rows = []
    for marker, a, d in zip(df["marker_id"], df["arrival"], df["departure"]):
        h = a.floor("h")
        while h < d:
            nxt = h + pd.Timedelta(hours=1)
            mins = (min(d, nxt) - max(a, h)).total_seconds() / 60
            rows.append((marker, h, mins))
            h = nxt
    out = pd.DataFrame(rows, columns=["marker_id", "hour_ts", "occ_min"])
    return out.groupby(["marker_id", "hour_ts"], as_index=False)["occ_min"].sum()


def process_year(year: int, lookup: pd.DataFrame) -> pd.DataFrame:
    zpath = C.RAW / f"parking_events_{year}.zip"
    if not zpath.exists():
        print(f"  missing {zpath.name} — run 00_download_com_data.py --years {year}")
        return pd.DataFrame()

    keep = set(lookup["marker_id"])
    parts = []
    with zipfile.ZipFile(zpath) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(name) as fh:
            for i, chunk in enumerate(pd.read_csv(fh, chunksize=CHUNK, low_memory=False)):
                chunk.columns = [COLMAP.get(c.lower().replace(" ", ""), c.lower()) for c in chunk.columns]
                if "marker_id" not in chunk:
                    raise KeyError(f"{year}: no marker column in {list(chunk.columns)[:12]}")
                chunk["marker_id"] = chunk["marker_id"].astype(str).str.strip().str.upper()
                chunk = chunk[chunk["marker_id"].isin(keep)]
                if chunk.empty:
                    continue
                for c in ("arrival", "departure"):
                    chunk[c] = pd.to_datetime(chunk[c], errors="coerce", dayfirst=False)
                parts.append(explode_to_hours(chunk))
                print(f"    chunk {i}: kept {len(chunk):,}")
    if not parts:
        return pd.DataFrame()
    hourly = pd.concat(parts).groupby(["marker_id", "hour_ts"], as_index=False)["occ_min"].sum()
    hourly.to_parquet(C.INTERIM / f"hourly_occupancy_{year}.parquet", index=False)
    return hourly


def summarise(hourly: pd.DataFrame, lookup: pd.DataFrame) -> pd.DataFrame:
    df = hourly.merge(lookup[["marker_id", "sid", "street_name"]], on="marker_id")
    df["occ_min"] = df["occ_min"].clip(0, 60)
    df["date"] = df["hour_ts"].dt.date
    df["hour"] = df["hour_ts"].dt.hour
    df["dow"] = df["hour_ts"].dt.dayofweek
    df["day_type"] = np.where(df["dow"] < 5, "weekday", "weekend")

    seg = (
        df.groupby(["sid", "street_name", "date", "hour", "day_type"], as_index=False)
        .agg(occ_min=("occ_min", "sum"), n_bays=("marker_id", "nunique"))
    )
    seg["utilisation"] = seg["occ_min"] / (seg["n_bays"] * 60)
    return seg


def pre_post(seg: pd.DataFrame) -> pd.DataFrame:
    """Compare mean weekday-daytime utilisation in the 12 months either side."""
    dates = pd.read_csv(C.PROCESSED / "intervention_dates.csv", dtype={"sid": str})
    dates = dates[dates["sensor_usable"] == True]  # noqa: E712
    dates["intervention_date"] = pd.to_datetime(dates["intervention_date"])

    seg = seg.copy()
    seg["date"] = pd.to_datetime(seg["date"])
    core = seg[(seg["day_type"] == "weekday") & seg["hour"].between(8, 18)]

    rows = []
    for _, r in dates.iterrows():
        s = core[core["sid"] == r["sid"]]
        d = r["intervention_date"]
        pre = s[s["date"].between(d - pd.DateOffset(years=1), d - pd.Timedelta(days=1))]
        post = s[s["date"].between(d + pd.Timedelta(days=30), d + pd.DateOffset(years=1))]
        rows.append({
            "sid": r["sid"],
            "street_name": r["street_name"],
            "intervention_date": d.date(),
            "pre_util": pre["utilisation"].mean(),
            "post_util": post["utilisation"].mean(),
            "pre_obs": len(pre),
            "post_obs": len(post),
            "pre_bays": pre["n_bays"].median(),
            "post_bays": post["n_bays"].median(),
        })
    out = pd.DataFrame(rows)
    out["util_change_pp"] = (out["post_util"] - out["pre_util"]) * 100
    out["bay_change"] = out["post_bays"] - out["pre_bays"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, required=True)
    a = ap.parse_args()

    lookup = build_bay_segment_lookup()

    frames = []
    for y in a.years:
        print(f"Processing {y}...")
        h = process_year(y, lookup)
        if not h.empty:
            frames.append(h)
    if not frames:
        print("No data processed.")
        return

    hourly = pd.concat(frames, ignore_index=True)
    seg = summarise(hourly, lookup)
    seg.to_parquet(C.PROCESSED / "segment_hourly_utilisation.parquet", index=False)

    res = pre_post(seg)
    res.to_csv(C.OUTPUTS / "sensor_pre_post_utilisation.csv", index=False)
    print("\n", res.to_string(index=False))
    print("\nwrote:", C.OUTPUTS / "sensor_pre_post_utilisation.csv")


if __name__ == "__main__":
    main()
