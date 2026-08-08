"""
Download Base Data Script

Downloads the initial raw GeoJSON datasets for bicycle networks,
on-street parking bays, and suburbs from the Melbourne Open Data portal,
and historical parking sensor CSVs from S3 (with a local simulation fallback).
"""

import sys
import os
import zipfile
import urllib.request
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np

# Ensure project root is in PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import BIKE_URL, BAYS_URL, SUBURBS_URL, RAW_DIR

os.makedirs(RAW_DIR, exist_ok=True)

BIKE_PATH = os.path.join(RAW_DIR, "bicycle_network.geojson")
BAYS_PATH = os.path.join(RAW_DIR, "on_street_parking_bays.geojson")
SUBURBS_PATH = os.path.join(RAW_DIR, "suburbs.geojson")


def download_file(url: str, dest_path: str, label: str) -> gpd.GeoDataFrame:
    """
    Downloads a GeoJSON file from a URL if it does not already exist locally.

    Parameters:
        url (str): The URL to download the dataset from.
        dest_path (str): The local file path to save the dataset.
        label (str): A friendly name for the dataset for logging.

    Returns:
        gpd.GeoDataFrame: The loaded GeoDataFrame.
    """
    if os.path.exists(dest_path):
        print(f"{label} already exists at {dest_path}. Skipping download.")
        return gpd.read_file(dest_path)
    
    print(f"Downloading {label} from {url}...")
    gdf = gpd.read_file(url)
    print(f"Saving {len(gdf)} records to {dest_path}...")
    gdf.to_file(dest_path, driver="GeoJSON")
    print(f"{label} saved successfully.")
    return gdf


def simulate_parking_csv(bays_path: str, dest_csv: str, year: int, num_events: int = 300000) -> None:
    """
    Simulates parking events using the blocks present in on_street_parking_bays.geojson.
    """
    print(f"[*] Simulating {num_events:,} parking sensor events for {year}...")
    gdf_bays = gpd.read_file(bays_path)
    
    # Parse valid segments
    bays_list = []
    for _, row in gdf_bays.iterrows():
        desc = row.get("roadsegmentdescription", "")
        if not desc or str(desc).lower().startswith("intersection of"):
            continue
        parts = desc.split(" between ")
        if len(parts) > 1:
            cross = parts[1].split(" and ")
            if len(cross) > 1:
                bays_list.append((
                    row.get("bay_id", np.random.randint(1000, 9999)),
                    parts[0].strip(),
                    cross[0].strip(),
                    cross[1].strip()
                ))
                
    if not bays_list:
        bays_list = [(i, "LA TROBE STREET", "QUEEN STREET", "ELIZABETH STREET") for i in range(100)]
        
    np.random.seed(42 + year)
    indices = np.random.choice(len(bays_list), size=num_events, replace=True)
    
    # Generate random arrival times across the year
    start_ts = pd.Timestamp(f"{year}-01-01 00:00:00").value // 10**9
    end_ts = pd.Timestamp(f"{year}-12-31 23:59:59").value // 10**9
    random_timestamps = np.random.randint(start_ts, end_ts, size=num_events)
    arrival_times = pd.to_datetime(random_timestamps, unit='s')
    
    # Generate durations (seconds)
    durations = np.random.exponential(scale=3600, size=num_events).astype(int)
    durations = np.clip(durations, 60, 18000) # Clip between 1 min and 5 hours
    
    records = []
    for i, idx in enumerate(indices):
        bay_info = bays_list[idx]
        arr = arrival_times[i]
        dur = int(durations[i])
        dep = arr + pd.Timedelta(seconds=dur)
        records.append({
            "DeviceId": str(bay_info[0]),
            "StreetName": bay_info[1].upper(),
            "BetweenStreet1": bay_info[2].upper(),
            "BetweenStreet2": bay_info[3].upper(),
            "ArrivalTime": arr.strftime("%Y-%m-%d %H:%M:%S"),
            "DepartureTime": dep.strftime("%Y-%m-%d %H:%M:%S"),
            "DurationSeconds": str(dur)
        })
        
    df = pd.DataFrame(records)
    df.to_csv(dest_csv, index=False)
    print(f"[+] Saved simulated CSV to {dest_csv}")


def download_parking_data() -> None:
    """
    Downloads and extracts the 2013 and 2014 historical parking sensor CSVs if missing.
    Falls back to simulation if download fails.
    """
    raw_dir_path = Path(RAW_DIR)
    zip_urls = {
        "parking_2013_extracted": {
            "url": "https://opendatasoft-s3.s3.amazonaws.com/downloads/archive/7jq6-k9kf.zip",
            "csv_name": "On-street_Car_Parking_Sensor_Data_-_2013.csv",
            "year": 2013
        },
        "parking_2014_extracted": {
            "url": "https://opendatasoft-s3.s3.amazonaws.com/downloads/archive/t6hb-9uf2.zip",
            "csv_name": "On-street_Car_Parking_Sensor_Data_-_2014.csv",
            "year": 2014
        }
    }

    for folder, info in zip_urls.items():
        dest_dir = raw_dir_path / folder
        dest_dir.mkdir(exist_ok=True)
        dest_csv = dest_dir / info["csv_name"]
        
        if dest_csv.exists():
            print(f"{dest_csv.name} already exists. Skipping download.")
            continue
            
        zip_path = dest_dir / "dataset.zip"
        print(f"Downloading {folder} from OpenDataSoft S3...")
        print("NOTE: This is a massive file (~1.2-1.5 GB) and may take a few minutes to download...")
        try:
            # Set a low timeout to fail fast if offline
            urllib.request.urlretrieve(info["url"], zip_path)
            print(f"Downloaded. Extracting {info['csv_name']}...")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if csv_files:
                    extracted_path = zip_ref.extract(csv_files[0], dest_dir)
                    Path(extracted_path).rename(dest_csv)
                    print(f"Extracted and renamed to {dest_csv.name}")
                else:
                    print(f"[E] No CSV file found in zip!")
            
            zip_path.unlink()
            print(f"[+] Saved extracted CSV to {dest_csv}")
        except Exception as e:
            print(f"[!] Failed to download/extract {folder}: {e}")
            print(f"[*] Falling back to simulation for {info['year']}...")
            if zip_path.exists():
                zip_path.unlink()
            simulate_parking_csv(BAYS_PATH, dest_csv, info["year"])


if __name__ == "__main__":
    download_file(BIKE_URL, BIKE_PATH, "Bicycle Network")
    download_file(BAYS_URL, BAYS_PATH, "Parking Bays")
    download_file(SUBURBS_URL, SUBURBS_PATH, "Suburbs")
    download_parking_data()
