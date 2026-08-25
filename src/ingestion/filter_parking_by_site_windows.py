#!/usr/bin/env python3
"""
Filter Parking Events by Site-Specific Baseline and Post Windows

Builds baseline/post date windows from sites_db.csv for each intervention site,
then filters City of Melbourne historical parking sensor CSVs down to events that
fall inside those windows on matching streets.

Outputs:
    data/processed/parking_baseline.parquet
    data/processed/parking_post.parquet
    data/processed/site_parking_windows.parquet
"""

from __future__ import annotations

import os
import re
import sys
import time
from typing import Iterable

import duckdb
import pandas as pd

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import (  # noqa: E402
    PARKING_YEARS,
    PROCESSED_DIR,
    RAW_DIR,
    SITE_WINDOW_MONTHS,
    SITES_DB_PATH,
)


def normalize_street_name(name: str | float | None) -> str:
    """
    Normalizes street names for joining sites_db to parking sensor rows.

    Parameters:
        name (str | float | None): Raw street name value.

    Returns:
        str: Uppercased, trimmed street name with common abbreviations aligned.
    """
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return ""
    value = str(name).upper().strip()
    value = re.sub(r"\s+", " ", value)
    value = value.replace("LITTLE ", "LT ")
    value = value.replace("SAINT ", "ST ")
    value = re.sub(r"\bSTREET\b", "ST", value)
    value = re.sub(r"\bROAD\b", "RD", value)
    value = re.sub(r"\bAVENUE\b", "AVE", value)
    value = re.sub(r"\bPARADE\b", "PDE", value)
    return value


def parse_yyyymmdd(series: pd.Series) -> pd.Series:
    """
    Parses YYYYMMDD numeric/string dates into pandas timestamps.

    Parameters:
        series (pd.Series): Raw date column from sites_db.

    Returns:
        pd.Series: Datetime values (NaT where parsing fails).
    """
    cleaned = (
        series.astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )
    return pd.to_datetime(cleaned, format="%Y%m%d", errors="coerce")


def load_sites_db(path: str) -> pd.DataFrame:
    """
    Loads the intervention sites database with a Windows-safe encoding fallback.

    Parameters:
        path (str): Relative or absolute path to sites_db.csv.

    Returns:
        pd.DataFrame: Raw sites table.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"sites_db not found at {path}. Place sites_db.csv under data/raw/."
        )
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(
        "utf-8",
        b"",
        0,
        1,
        f"Unable to decode sites_db at {path} with utf-8/cp1252/latin-1.",
    )


def build_site_windows(
    sites: pd.DataFrame,
    window_months: int,
) -> pd.DataFrame:
    """
    Builds per-site baseline and post date windows from intervention dates.

    Baseline uses DisruptionStartDate when available, otherwise
    DateOfIntervention/InitialCapture. Post uses DisruptionEndDate when
    available, otherwise the same intervention capture date.

    Parameters:
        sites (pd.DataFrame): Loaded sites_db rows.
        window_months (int): Half-window size in months.

    Returns:
        pd.DataFrame: One row per SiteID/street with window bounds.
    """
    required = [
        "SiteID",
        "StreetInScope",
        "SiteType",
        "DateOfIntervention/InitialCapture",
        "DisruptionStartDate",
        "DisruptionEndDate",
    ]
    missing = [col for col in required if col not in sites.columns]
    if missing:
        raise KeyError(f"sites_db is missing required columns: {missing}")

    frame = sites[required].copy()
    frame["intervention_date"] = parse_yyyymmdd(
        frame["DateOfIntervention/InitialCapture"]
    )
    frame["disruption_start"] = parse_yyyymmdd(frame["DisruptionStartDate"])
    frame["disruption_end"] = parse_yyyymmdd(frame["DisruptionEndDate"])

    frame["baseline_anchor"] = frame["disruption_start"].fillna(
        frame["intervention_date"]
    )
    frame["post_anchor"] = frame["disruption_end"].fillna(frame["intervention_date"])

    frame = frame.dropna(subset=["baseline_anchor", "post_anchor", "StreetInScope"])
    frame["street_normalized"] = frame["StreetInScope"].map(normalize_street_name)
    frame = frame[frame["street_normalized"] != ""]

    # Keep one window row per SiteID + street (first non-null anchors).
    frame = (
        frame.sort_values(["SiteID", "StreetInScope", "baseline_anchor"])
        .drop_duplicates(subset=["SiteID", "street_normalized"], keep="first")
        .copy()
    )

    frame["baseline_start"] = frame["baseline_anchor"] - pd.DateOffset(
        months=window_months
    )
    frame["baseline_end"] = frame["baseline_anchor"]
    frame["post_start"] = frame["post_anchor"]
    frame["post_end"] = frame["post_anchor"] + pd.DateOffset(months=window_months)

    return frame[
        [
            "SiteID",
            "SiteType",
            "StreetInScope",
            "street_normalized",
            "baseline_start",
            "baseline_end",
            "post_start",
            "post_end",
        ]
    ].reset_index(drop=True)


def parking_csv_path(year: int) -> str:
    """
    Resolves the expected raw parking CSV path for a calendar year.

    Parameters:
        year (int): Parking sensor year (e.g. 2013).

    Returns:
        str: Absolute path to the yearly CSV.
    """
    filename = f"On-street_Car_Parking_Sensor_Data_-_{year}.csv"
    return os.path.join(RAW_DIR, f"parking_{year}_extracted", filename)


def filter_parking_year(
    con: duckdb.DuckDBPyConnection,
    csv_path: str,
    year: int,
) -> tuple[int, int]:
    """
    Filters one yearly parking CSV into baseline and post period tables.

    Parameters:
        con (duckdb.DuckDBPyConnection): Open DuckDB connection with site windows
            already registered as site_windows.
        csv_path (str): Path to the yearly parking sensor CSV.
        year (int): Calendar year being filtered.

    Returns:
        tuple[int, int]: Counts of baseline and post rows retained for the year.
    """
    if not os.path.exists(csv_path):
        print(f"[!] Skipping missing parking CSV: {csv_path}")
        return 0, 0

    print(f"[*] Filtering parking events for {year} from {csv_path} ...")
    # Street normalization mirrors normalize_street_name() using DuckDB SQL.
    query = f"""
    INSERT INTO filtered_parking
    WITH raw AS (
        SELECT
            DeviceId,
            StreetName,
            BetweenStreet1,
            BetweenStreet2,
            ArrivalTime,
            DepartureTime,
            TRY_CAST(DurationSeconds AS INTEGER) AS DurationSeconds,
            regexp_replace(
                regexp_replace(
                    regexp_replace(
                        regexp_replace(
                            regexp_replace(
                                regexp_replace(
                                    upper(trim(StreetName)),
                                    '\\s+',
                                    ' ',
                                    'g'
                                ),
                                'LITTLE ',
                                'LT ',
                                'g'
                            ),
                            'SAINT ',
                            'ST ',
                            'g'
                        ),
                        '\\bSTREET\\b',
                        'ST',
                        'g'
                    ),
                    '\\bROAD\\b',
                    'RD',
                    'g'
                ),
                '\\bAVENUE\\b',
                'AVE',
                'g'
            ) AS street_normalized_tmp
        FROM read_csv_auto('{csv_path.replace(chr(92), "/")}', ignore_errors=true)
        WHERE ArrivalTime IS NOT NULL
          AND DepartureTime IS NOT NULL
          AND TRY_CAST(DurationSeconds AS INTEGER) > 0
    ),
    raw_norm AS (
        SELECT
            *,
            regexp_replace(street_normalized_tmp, '\\bPARADE\\b', 'PDE', 'g')
                AS street_normalized
        FROM raw
    )
    SELECT
        r.DeviceId,
        r.StreetName,
        r.BetweenStreet1,
        r.BetweenStreet2,
        r.ArrivalTime,
        r.DepartureTime,
        r.DurationSeconds,
        w.SiteID,
        w.SiteType,
        w.StreetInScope,
        CASE
            WHEN r.ArrivalTime >= w.baseline_start
             AND r.ArrivalTime <  w.baseline_end THEN 'baseline'
            WHEN r.ArrivalTime >  w.post_start
             AND r.ArrivalTime <= w.post_end THEN 'post'
        END AS period,
        {year} AS source_year
    FROM raw_norm r
    INNER JOIN site_windows w
        ON r.street_normalized = w.street_normalized
    WHERE (
        (r.ArrivalTime >= w.baseline_start AND r.ArrivalTime < w.baseline_end)
        OR
        (r.ArrivalTime > w.post_start AND r.ArrivalTime <= w.post_end)
    )
    """
    con.execute(query)

    baseline_count = con.execute(
        f"""
        SELECT count(*)
        FROM filtered_parking
        WHERE source_year = {year} AND period = 'baseline'
        """
    ).fetchone()[0]
    post_count = con.execute(
        f"""
        SELECT count(*)
        FROM filtered_parking
        WHERE source_year = {year} AND period = 'post'
        """
    ).fetchone()[0]
    print(
        f"[+] {year}: retained {baseline_count:,} baseline and "
        f"{post_count:,} post events."
    )
    return int(baseline_count), int(post_count)


def write_outputs(con: duckdb.DuckDBPyConnection, windows: pd.DataFrame) -> None:
    """
    Writes filtered parking parquet files and the site window lookup table.

    Parameters:
        con (duckdb.DuckDBPyConnection): Connection containing filtered_parking.
        windows (pd.DataFrame): Site window definitions to persist.
    """
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    windows_path = os.path.join(PROCESSED_DIR, "site_parking_windows.parquet")
    baseline_path = os.path.join(PROCESSED_DIR, "parking_baseline.parquet")
    post_path = os.path.join(PROCESSED_DIR, "parking_post.parquet")

    # Persist via DuckDB so parquet writing does not require pyarrow.
    con.register("site_windows_out", windows)
    con.execute(
        f"""
        COPY (SELECT * FROM site_windows_out)
        TO '{windows_path.replace(chr(92), "/")}' (FORMAT PARQUET)
        """
    )
    con.execute(
        f"""
        COPY (
            SELECT *
            FROM filtered_parking
            WHERE period = 'baseline'
        ) TO '{baseline_path.replace(chr(92), "/")}' (FORMAT PARQUET)
        """
    )
    con.execute(
        f"""
        COPY (
            SELECT *
            FROM filtered_parking
            WHERE period = 'post'
        ) TO '{post_path.replace(chr(92), "/")}' (FORMAT PARQUET)
        """
    )
    print(f"[+] Wrote {windows_path}")
    print(f"[+] Wrote {baseline_path}")
    print(f"[+] Wrote {post_path}")


def print_coverage_summary(con: duckdb.DuckDBPyConnection, windows: pd.DataFrame) -> None:
    """
    Prints site coverage statistics for the filtered parking outputs.

    Parameters:
        con (duckdb.DuckDBPyConnection): Connection containing filtered_parking.
        windows (pd.DataFrame): Site window definitions.
    """
    matched_sites = con.execute(
        """
        SELECT
            period,
            count(DISTINCT SiteID) AS n_sites,
            count(*) AS n_events
        FROM filtered_parking
        GROUP BY period
        ORDER BY period
        """
    ).df()
    print("\nCoverage by period:")
    print(matched_sites.to_string(index=False))

    matched_ids = set(
        con.execute("SELECT DISTINCT SiteID FROM filtered_parking").df()["SiteID"]
    )
    total_sites = windows["SiteID"].nunique()
    uncovered = total_sites - len(matched_ids)
    print(
        f"\nSites with parking overlap in configured years: "
        f"{len(matched_ids)} / {total_sites}"
    )
    print(
        f"Sites with zero overlap (often outside CoM 2013-2014 coverage): "
        f"{uncovered}"
    )


def run_pipeline(
    years: Iterable[int] | None = None,
    window_months: int | None = None,
) -> None:
    """
    Runs the full site-window parking filter pipeline.

    Parameters:
        years (Iterable[int] | None): Parking CSV years to process. Defaults to
            config parking_years.
        window_months (int | None): Months before/after anchors. Defaults to
            config site_windows.window_months.
    """
    years = list(years) if years is not None else list(PARKING_YEARS)
    window_months = (
        SITE_WINDOW_MONTHS if window_months is None else int(window_months)
    )

    print("=" * 60)
    print("  Filter Parking by Site Baseline / Post Windows")
    print("=" * 60)
    print(f"Window months: {window_months}")
    print(f"Parking years: {years}")
    print(f"Sites DB: {SITES_DB_PATH}")

    started = time.time()
    sites = load_sites_db(SITES_DB_PATH)
    windows = build_site_windows(sites, window_months=window_months)
    print(f"[+] Built {len(windows):,} site/street windows "
          f"across {windows['SiteID'].nunique():,} sites.")

    con = duckdb.connect()
    try:
        con.register("site_windows", windows)
        con.execute(
            """
            CREATE TABLE filtered_parking AS
            SELECT
                CAST(NULL AS VARCHAR) AS DeviceId,
                CAST(NULL AS VARCHAR) AS StreetName,
                CAST(NULL AS VARCHAR) AS BetweenStreet1,
                CAST(NULL AS VARCHAR) AS BetweenStreet2,
                CAST(NULL AS TIMESTAMP) AS ArrivalTime,
                CAST(NULL AS TIMESTAMP) AS DepartureTime,
                CAST(NULL AS INTEGER) AS DurationSeconds,
                CAST(NULL AS VARCHAR) AS SiteID,
                CAST(NULL AS VARCHAR) AS SiteType,
                CAST(NULL AS VARCHAR) AS StreetInScope,
                CAST(NULL AS VARCHAR) AS period,
                CAST(NULL AS INTEGER) AS source_year
            WHERE FALSE
            """
        )

        total_baseline = 0
        total_post = 0
        for year in years:
            baseline_count, post_count = filter_parking_year(
                con,
                parking_csv_path(int(year)),
                int(year),
            )
            total_baseline += baseline_count
            total_post += post_count

        write_outputs(con, windows)
        print_coverage_summary(con, windows)
        elapsed = time.time() - started
        print(
            f"\nSUCCESS: retained {total_baseline:,} baseline and "
            f"{total_post:,} post parking events in {elapsed:.1f}s."
        )
    finally:
        con.close()


def main() -> None:
    """
    CLI entrypoint for the site-window parking filter.
    """
    run_pipeline()


if __name__ == "__main__":
    main()
