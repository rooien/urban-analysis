"""
Aggregate Occupancy Script

Aggregates the filtered event-level data into hourly occupancy rates per block,
computing the occupied minutes against the monthly bay capacity for baseline
and post-intervention years, across all supported streets and suburbs.
Cleans sensor duration anomalies (<0s or >24h) and computes turnover and duration metrics.
"""

import sys
import os
import duckdb
import geopandas as gpd
import pandas as pd
import re
import time

# Ensure project root is in PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import (
    PROCESSED_DIR, DB_PATH, 
    BASELINE_YEAR, POST_YEAR
)


def normalize(name: str) -> str:
    """
    Normalizes street names for matching with CSV data.
    """
    if not name:
        return ""
    name = str(name).upper().strip()
    name = re.sub(r'\s+', ' ', name)
    name = name.replace("LITTLE ", "LT ")
    name = name.replace("SAINT ", "ST ")
    return name


def get_block_key(desc: str) -> str:
    """
    Extracts a standardized block key (cross streets) from roadsegmentdescription.
    """
    if not desc:
        return ""
    desc = desc.strip()
    parts = desc.split(" between ")
    if len(parts) > 1:
        cross = parts[1].split(" and ")
        if len(cross) > 1:
            st1 = normalize(cross[0])
            st2 = normalize(cross[1])
            st_sorted = sorted([st1, st2])
            return f"BETWEEN {st_sorted[0]} AND {st_sorted[1]}"
    parts = desc.split(" from ")
    if len(parts) > 1:
        return f"FROM {normalize(parts[0])}"
    return ""


def aggregate_year(con_db: duckdb.DuckDBPyConnection, mapping_df: pd.DataFrame, year: int) -> None:
    """
    Aggregates hourly occupancy for a specific year and inserts it into the database.
    Applies data quality cleansing (duration bounds 0 to 86400s) and calculates turnover metrics.
    """
    parquet_path = os.path.join(PROCESSED_DIR, f"matched_events_{year}.parquet")
    if not os.path.exists(parquet_path):
        print(f"Parquet not found for {year}: {parquet_path}")
        return

    print(f"Aggregating hourly occupancy and turnover for {year}...")
    start_date = f"{year}-01-01 00:00:00"
    end_date = f"{year}-12-31 23:00:00"

    # Register the mapping DataFrame in an in-memory DuckDB connection to prepare the mapping
    con_mem = duckdb.connect()
    con_mem.register("mapping_df", mapping_df)

    print("Building block mapping and filtering sensor anomalies in Parquet data...")
    temp_parquet = os.path.join(PROCESSED_DIR, f"temp_mapped_events_{year}.parquet")
    
    norm_st = "REGEXP_REPLACE(REPLACE(REPLACE(UPPER(TRIM(StreetName)), 'LITTLE ', 'LT '), 'SAINT ', 'ST '), '\\\\s+', ' ', 'g')"
    norm_b1 = "REGEXP_REPLACE(REPLACE(REPLACE(UPPER(TRIM(BetweenStreet1)), 'LITTLE ', 'LT '), 'SAINT ', 'ST '), '\\\\s+', ' ', 'g')"
    norm_b2 = "REGEXP_REPLACE(REPLACE(REPLACE(UPPER(TRIM(BetweenStreet2)), 'LITTLE ', 'LT '), 'SAINT ', 'ST '), '\\\\s+', ' ', 'g')"

    # Filter durations: drop < 0 (sensor logging reversal) and > 86400 (midnight backfill anomaly)
    query_map = f"""
    COPY (
        WITH events AS (
            SELECT 
                DeviceId,
                StreetName,
                BetweenStreet1,
                BetweenStreet2,
                ArrivalTime::TIMESTAMP AS ArrivalTime,
                DepartureTime::TIMESTAMP AS DepartureTime,
                TRY_CAST(DurationSeconds AS BIGINT) AS DurationSeconds,
                {norm_st} AS norm_street,
                CASE 
                    WHEN BetweenStreet2 IS NOT NULL AND TRIM(BetweenStreet2) != '' AND TRIM(UPPER(BetweenStreet2)) != 'DEAD END'
                    THEN 'BETWEEN ' || 
                         CASE WHEN {norm_b1} < {norm_b2} 
                               THEN {norm_b1} || ' AND ' || {norm_b2} 
                               ELSE {norm_b2} || ' AND ' || {norm_b1} 
                         END
                    ELSE 'FROM ' || {norm_b1}
                END AS block_key
            FROM read_parquet('{parquet_path}')
            WHERE DepartureTime > ArrivalTime
              AND TRY_CAST(DurationSeconds AS BIGINT) > 0
              AND TRY_CAST(DurationSeconds AS BIGINT) <= 86400
        )
        SELECT 
            e.DeviceId,
            e.ArrivalTime,
            e.DepartureTime,
            e.DurationSeconds,
            m.suburb,
            m.street_name,
            m.roadsegmentdescription AS block_desc
        FROM events e
        JOIN mapping_df m 
          ON e.norm_street = m.norm_street 
         AND e.block_key = m.block_key
    ) TO '{temp_parquet}' (FORMAT PARQUET);
    """
    start = time.time()
    con_mem.execute(query_map)
    print(f"Mapping blocks took {time.time() - start:.2f} seconds.")
    con_mem.close()

    # Run hourly aggregation with turnover count and average stay duration
    query_agg = f"""
    INSERT INTO hourly_occupancy
    WITH events AS (
        SELECT * FROM read_parquet('{temp_parquet}')
    ),
    monthly_blocks AS (
        SELECT 
            month(ArrivalTime) AS m,
            suburb,
            street_name,
            block_desc,
            COUNT(DISTINCT DeviceId) AS bay_count
        FROM events
        GROUP BY 1, 2, 3, 4
    ),
    hours AS (
        SELECT generate_series AS hr, month(generate_series) AS m
        FROM generate_series('{start_date}'::TIMESTAMP, '{end_date}'::TIMESTAMP, interval '1 hour')
    ),
    occupancy_calc AS (
        SELECT 
            e.suburb,
            e.street_name,
            e.block_desc,
            h.hr,
            h.m,
            SUM(
                epoch(LEAST(e.DepartureTime, h.hr + interval '1 hour') - GREATEST(e.ArrivalTime, h.hr)) / 60.0
            ) AS occupied_minutes,
            COUNT(DISTINCT e.DeviceId || '_' || e.ArrivalTime) AS events_count,
            AVG(e.DurationSeconds / 60.0) AS avg_duration_min
        FROM hours h
        JOIN events e 
          ON e.ArrivalTime < h.hr + interval '1 hour' 
         AND e.DepartureTime > h.hr
        GROUP BY 1, 2, 3, 4, 5
    )
    SELECT 
        {year} AS year,
        o.suburb,
        o.street_name,
        o.block_desc,
        o.hr,
        o.occupied_minutes,
        (b.bay_count * 60.0) AS total_minutes,
        LEAST(1.0, o.occupied_minutes / (b.bay_count * 60.0)) AS occupancy_rate,
        b.bay_count,
        COALESCE(o.events_count, 0) AS events_count,
        ROUND(COALESCE(o.events_count, 0) * 1.0 / GREATEST(1, b.bay_count), 3) AS turnover_rate,
        ROUND(COALESCE(o.avg_duration_min, 0.0), 1) AS avg_duration_min
    FROM occupancy_calc o
    JOIN monthly_blocks b 
      ON o.block_desc = b.block_desc 
     AND o.m = b.m
    """
    
    print("Running hourly occupancy and turnover aggregation query...")
    start = time.time()
    con_db.execute(query_agg)
    print(f"Aggregation took {time.time() - start:.2f} seconds.")
    
    # Clean up temporary Parquet
    if os.path.exists(temp_parquet):
        os.remove(temp_parquet)

    print(f"Successfully aggregated {year}.")


def main() -> None:
    """
    Main execution function to build mapping and run aggregation for all years.
    """
    bays_path = os.path.join(PROCESSED_DIR, "matched_parking_bays.geojson")
    if not os.path.exists(bays_path):
        print(f"Matched bays not found at {bays_path}. Run match_bike_lanes.py first.")
        return

    print("Loading matched bays to build block mapping...")
    gdf_bays = gpd.read_file(bays_path)
    
    # Extract distinct blocks and their suburbs
    gdf_bays["norm_street"] = gdf_bays["street_name"].apply(normalize)
    gdf_bays["block_key"] = gdf_bays["roadsegmentdescription"].apply(get_block_key)
    
    # Keep only valid blocks
    gdf_bays = gdf_bays[gdf_bays["block_key"] != ""].copy()
    
    mapping_df = gdf_bays[["suburb", "street_name", "norm_street", "block_key", "roadsegmentdescription"]].drop_duplicates(subset=["norm_street", "block_key"])
    print(f"Built mapping for {len(mapping_df)} unique blocks across all supported streets.")

    con = duckdb.connect(DB_PATH)
    
    # Create tables with enhanced metrics
    con.execute("""
    CREATE OR REPLACE TABLE hourly_occupancy (
        year INTEGER,
        suburb VARCHAR,
        street_name VARCHAR,
        block_desc VARCHAR,
        hr TIMESTAMP,
        occupied_minutes DOUBLE,
        total_minutes DOUBLE,
        occupancy_rate DOUBLE,
        bay_count INTEGER,
        events_count INTEGER,
        turnover_rate DOUBLE,
        avg_duration_min DOUBLE
    )
    """)
    
    con.execute("DELETE FROM hourly_occupancy")

    aggregate_year(con, mapping_df, BASELINE_YEAR)
    aggregate_year(con, mapping_df, POST_YEAR)

    res = con.execute("SELECT year, count(*), count(distinct street_name), avg(occupancy_rate), avg(turnover_rate), avg(avg_duration_min) FROM hourly_occupancy GROUP BY 1").fetchall()
    print("\nAggregation Summary (Year, Rows, Distinct Streets, Avg Occ, Avg Turnover, Avg Duration Min):")
    for row in res:
        print(f"  Year {row[0]}: {row[1]:,} rows across {row[2]} streets | Mean Occ: {row[3]*100:.1f}%, Mean Turnover: {row[4]:.2f} events/bay/hr, Mean Stay: {row[5]:.1f} min")

    con.close()
    print(f"Database saved to {DB_PATH}")


if __name__ == "__main__":
    main()
