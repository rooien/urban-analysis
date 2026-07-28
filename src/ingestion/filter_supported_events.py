"""
Filter Supported Events Script

Filters the massive yearly historical sensor CSV files down to just the parking events
occurring on streets that have supported bike lanes, saving them as optimized Parquet files.
"""

import sys
import os
import duckdb
import geopandas as gpd
import pandas as pd
import re

# Ensure project root is in PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import PROCESSED_DIR, RAW_DIR

os.makedirs(PROCESSED_DIR, exist_ok=True)

BAYS_MATCHED_PATH = os.path.join(PROCESSED_DIR, "matched_parking_bays.geojson")


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


def main() -> None:
    """
    Main execution function to filter historical sensor data by supported streets.
    """
    if len(sys.argv) < 2:
        print("Usage: python3 filter_supported_events.py <year>")
        return

    year = sys.argv[1]
    csv_filename = f"On-street_Car_Parking_Sensor_Data_-_2013.csv" if year == "2013" else f"On-street_Car_Parking_Sensor_Data_-_2014.csv"
    csv_path = os.path.join(RAW_DIR, f"parking_{year}_extracted", csv_filename)
    
    if not os.path.exists(csv_path):
        print(f"CSV not found at {csv_path}. Please unzip the downloaded zip first.")
        return

    if not os.path.exists(BAYS_MATCHED_PATH):
        print(f"Matched bays not found at {BAYS_MATCHED_PATH}. Run match_bike_lanes.py first.")
        return

    out_parquet = os.path.join(PROCESSED_DIR, f"matched_events_{year}.parquet")
    print(f"Filtering {csv_filename} for supported streets using DuckDB...")

    # Load matched bays and get distinct normalized street names
    print("Loading matched bays and building street filter...")
    gdf_bays = gpd.read_file(BAYS_MATCHED_PATH)
    distinct_streets = gdf_bays["street_name"].apply(normalize).unique()
    
    df_supp = pd.DataFrame({"normalized": distinct_streets})
    print(f"Matching against {len(df_supp)} distinct normalized streets.")

    # Connect to DuckDB (in-memory)
    con = duckdb.connect()

    # Register the pandas DataFrame as a virtual table in DuckDB
    con.register("supported_streets_tbl", df_supp)

    query = f"""
    COPY (
        WITH raw AS (
            SELECT 
                DeviceId, 
                StreetName,
                BetweenStreet1,
                BetweenStreet2,
                ArrivalTime,
                DepartureTime,
                TRY_CAST(DurationSeconds AS INTEGER) AS DurationSeconds,
                UPPER(REGEXP_REPLACE(REPLACE(REPLACE(TRIM(StreetName), 'LITTLE ', 'LT '), 'SAINT ', 'ST '), '\\s+', ' ', 'g')) AS normalized
            FROM read_csv_auto('{csv_path}', ignore_errors=true)
            WHERE ArrivalTime IS NOT NULL
              AND DepartureTime IS NOT NULL
              AND TRY_CAST(DurationSeconds AS INTEGER) > 0
        )
        SELECT 
            r.DeviceId, 
            r.StreetName, 
            r.BetweenStreet1, 
            r.BetweenStreet2, 
            r.ArrivalTime, 
            r.DepartureTime, 
            r.DurationSeconds
        FROM raw r
        JOIN supported_streets_tbl s 
          ON r.normalized = s.normalized
    ) TO '{out_parquet}' (FORMAT PARQUET);
    """
    
    try:
        import time
        start = time.time()
        con.execute(query)
        print(f"Successfully filtered and saved to {out_parquet} in {time.time() - start:.2f} seconds.")
        
        # Count the results
        res = con.execute(f"SELECT count(*) FROM read_parquet('{out_parquet}')").fetchone()[0]
        print(f"Found {res} valid parking events for {year} across supported streets.")
        
        # Print unique streets actually found in the events
        actual_streets = con.execute(f"SELECT DISTINCT StreetName FROM read_parquet('{out_parquet}')").df()
        print(f"Actually matched {len(actual_streets)} unique streets in the CSV data.")
        
    except Exception as e:
        print(f"Error executing DuckDB query: {e}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
