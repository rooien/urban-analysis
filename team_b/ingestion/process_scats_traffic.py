"""
Process SCATS Traffic Data Script

Simulates SCATS 15-minute traffic volumes for intersections across the baseline
and post years (2013-2014) if the raw dataset is missing, and loads the data
into the DuckDB analytical database.
"""

import sys
import os
import pandas as pd
import numpy as np
import duckdb

# Ensure project root is in PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import RAW_DIR, DB_PATH

SCATS_CSV_PATH = os.path.join(RAW_DIR, "scats_volume_data.csv")


def generate_simulated_scats() -> pd.DataFrame:
    """
    Generates simulated SCATS traffic volume data for EDA and demo purposes.
    """
    print("[*] Generating simulated SCATS traffic volume data...")
    # Generate 15-minute intervals for 2013 and 2014
    dates = pd.date_range(start="2013-01-01 00:00:00", end="2014-12-31 23:45:00", freq="15min")
    
    # Simple list of mock intersection IDs
    intersections = [1001, 1002, 1003, 1004, 1005]
    
    # We will simulate multiple intersections by creating records for each intersection
    dfs = []
    for int_id in intersections:
        np.random.seed(int_id)
        # Generate base volume with a daily peak pattern (morning & evening rush hours)
        hours = dates.hour
        base_volume = 100 + 400 * np.sin(np.pi * hours / 12.0) ** 4 + np.random.randint(-50, 50, size=len(dates))
        base_volume = np.clip(base_volume, 10, 1000).astype(int)
        
        # Degree of saturation correlates with volume
        deg_saturation = np.clip(base_volume / 1000.0 + np.random.uniform(-0.1, 0.1, size=len(dates)), 0.05, 0.98)
        
        df = pd.DataFrame({
            "timestamp": dates,
            "intersection_id": int_id,
            "traffic_volume": base_volume,
            "degree_of_saturation": deg_saturation
        })
        dfs.append(df)
        
    final_df = pd.concat(dfs).sort_values("timestamp").reset_index(drop=True)
    return final_df


def main() -> None:
    """
    Main execution function to load or simulate SCATS traffic data and populate DuckDB.
    """
    os.makedirs(RAW_DIR, exist_ok=True)
    
    if not os.path.exists(SCATS_CSV_PATH):
        print(f"[*] SCATS traffic volume file not found at {SCATS_CSV_PATH}.")
        df_scats = generate_simulated_scats()
        print(f"[*] Saving simulated SCATS data ({len(df_scats):,} rows) to {SCATS_CSV_PATH}...")
        df_scats.to_csv(SCATS_CSV_PATH, index=False)
    else:
        print(f"[+] Found existing SCATS traffic volume file at {SCATS_CSV_PATH}.")
        
    print(f"[*] Importing SCATS traffic data from {SCATS_CSV_PATH} into DuckDB...")
    
    # Connect to DuckDB database
    con = duckdb.connect(DB_PATH)
    
    try:
        # Create table
        con.execute("""
        CREATE TABLE IF NOT EXISTS traffic_volumes (
            timestamp TIMESTAMP,
            intersection_id INTEGER,
            traffic_volume INTEGER,
            degree_of_saturation DOUBLE
        )
        """)
        
        # Clear existing records
        con.execute("DELETE FROM traffic_volumes")
        
        # Import CSV using DuckDB's CSV reader
        con.execute(f"""
        INSERT INTO traffic_volumes
        SELECT 
            timestamp::TIMESTAMP,
            intersection_id::INTEGER,
            traffic_volume::INTEGER,
            degree_of_saturation::DOUBLE
        FROM read_csv_auto('{SCATS_CSV_PATH.replace(chr(92), "/")}')
        """)
        
        row_count = con.execute("SELECT count(*) FROM traffic_volumes").fetchone()[0]
        print(f"[+] Successfully loaded {row_count:,} SCATS traffic records into DuckDB table 'traffic_volumes'.")
        
    except Exception as e:
        print(f"[E] Error loading SCATS data: {e}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
