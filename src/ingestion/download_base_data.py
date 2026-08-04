"""
Download Base Data Script

Downloads the initial raw GeoJSON datasets for bicycle networks,
on-street parking bays, and suburbs from the Melbourne Open Data portal.
"""

import sys
import os
import geopandas as gpd

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


if __name__ == "__main__":
    download_file(BIKE_URL, BIKE_PATH, "Bicycle Network")
    download_file(BAYS_URL, BAYS_PATH, "Parking Bays")
    download_file(SUBURBS_URL, SUBURBS_PATH, "Suburbs")
