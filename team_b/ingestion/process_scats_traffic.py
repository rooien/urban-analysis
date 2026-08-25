"""
Process SCATS Traffic Data Script

Simulates / ingests SCATS 15-minute traffic volumes for intersections across the baseline
and post years (2013-2014), cleans sentinel fault codes (-1 detector alarms), and loads the data
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
    Generates simulated SCATS traffic volume data for EDA and demo purposes,
    including vehicle classification estimates and detector alarm flags.
    """
    print("[*] Generating simulated SCATS traffic volume data...")
    # Generate 15-minute intervals for 2013 and 2014
    dates = pd.date_range(start="2013-01-01 00:00:00", end="2014-12-31 23:45:00", freq="15min")
    
    # List of inner-Melbourne SCATS intersection IDs
    intersections = [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008]
    
    dfs = []
    for int_id in intersections:
        np.random.seed(int_id)
        # Generate base volume with a daily peak pattern (morning & evening rush hours)
        hours = dates.hour
        # Diurnal pattern with morning (08:00) and evening (16:00-17:00) peaks
        base_volume = 100 + 400 * np.sin(np.pi * hours / 12.0) ** 4 + np.random.randint(-50, 50, size=len(dates))
        base_volume = np.clip(base_volume, 10, 1200).astype(int)
        
        # Inject ~0.5% detector fault / alarm sentinel values (-1) to simulate real SCATS hardware anomalies
        fault_mask = np.random.rand(len(dates)) < 0.005
        base_volume = np.where(fault_mask, -1, base_volume)
        
        # Degree of saturation correlates with volume (0.0 to 1.0)
        deg_saturation = np.where(
            base_volume >= 0,
            np.clip(base_volume / 1000.0 + np.random.uniform(-0.08, 0.08, size=len(dates)), 0.05, 0.98),
            0.0
        )
        
        # Vehicle classification estimates based on TIRTL classification distributions:
        # Class 1 (Light vehicles/cars): ~85.8%
        # Class 3 (Rigid trucks/commercial): ~10.1%
        # Class 9 (Heavy articulated vehicles): ~1.7%
        # Other classes: ~2.4%
        vol_clean = np.maximum(0, base_volume)
        vol_class_1 = (vol_clean * 0.858).round().astype(int)
        vol_class_3 = (vol_clean * 0.101).round().astype(int)
        vol_class_9 = (vol_clean * 0.017).round().astype(int)
        
        df = pd.DataFrame({
            "timestamp": dates,
            "intersection_id": int_id,
            "traffic_volume": base_volume,
            "degree_of_saturation": np.round(deg_saturation, 3),
            "vol_class_1_light": vol_class_1,
            "vol_class_3_truck": vol_class_3,
            "vol_class_9_heavy": vol_class_9,
            "fault_flag": fault_mask.astype(int)
        })
        dfs.append(df)
        
    final_df = pd.concat(dfs).sort_values("timestamp").reset_index(drop=True)
    return final_df


def main() -> None:
    """
    Main execution function to load or simulate SCATS traffic data,
    clean sentinel faults (< 0), and populate DuckDB.
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
        # Create table with traffic volumes and vehicle classification metrics
        con.execute("""
        CREATE OR REPLACE TABLE traffic_volumes (
            timestamp TIMESTAMP,
            intersection_id INTEGER,
            traffic_volume INTEGER,
            degree_of_saturation DOUBLE,
            vol_class_1_light INTEGER,
            vol_class_3_truck INTEGER,
            vol_class_9_heavy INTEGER,
            fault_flag INTEGER
        )
        """)
        
        # Clear existing records
        con.execute("DELETE FROM traffic_volumes")
        
        # Import CSV using DuckDB's CSV reader, filtering negative sentinel fault codes
        con.execute(f"""
        INSERT INTO traffic_volumes
        SELECT 
            timestamp::TIMESTAMP,
            intersection_id::INTEGER,
            CASE WHEN traffic_volume < 0 THEN 0 ELSE traffic_volume::INTEGER END AS traffic_volume,
            degree_of_saturation::DOUBLE,
            ROUND(CASE WHEN traffic_volume < 0 THEN 0 ELSE traffic_volume END * 0.858)::INTEGER AS vol_class_1_light,
            ROUND(CASE WHEN traffic_volume < 0 THEN 0 ELSE traffic_volume END * 0.101)::INTEGER AS vol_class_3_truck,
            ROUND(CASE WHEN traffic_volume < 0 THEN 0 ELSE traffic_volume END * 0.017)::INTEGER AS vol_class_9_heavy,
            CASE WHEN traffic_volume < 0 THEN 1 ELSE 0 END AS fault_flag
        FROM read_csv_auto('{SCATS_CSV_PATH.replace(chr(92), "/")}')
        """)
        
        row_count = con.execute("SELECT count(*) FROM traffic_volumes").fetchone()[0]
        cleaned_faults = con.execute("SELECT count(*) FROM traffic_volumes WHERE fault_flag = 1").fetchone()[0]
        mean_vol = con.execute("SELECT avg(traffic_volume) FROM traffic_volumes WHERE fault_flag = 0").fetchone()[0]
        
        print(f"[+] Successfully loaded {row_count:,} SCATS traffic records into DuckDB table 'traffic_volumes'.")
        print(f"    Cleaned/Flagged Detector Faults: {cleaned_faults:,} records (Negative Sentinels)")
        print(f"    Mean 15-min Traffic Volume: {mean_vol:.1f} vehicles/interval")
        
    except Exception as e:
        print(f"[E] Error loading SCATS data: {e}")
        sys.exit(1)
    finally:
        con.close()


if __name__ == "__main__":
    main()
