"""
Match Bike Lanes Script

Spatially joins suburbs, bike segments, and parking bays to identify all streets
with bike infrastructure running along on-street parking bays.
"""

import sys
import os
import geopandas as gpd

# Ensure project root is in PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import (
    PROCESSED_DIR, RAW_DIR,
    EPSG_PROJECTED, EPSG_WGS84, BUFFER_PARKING_BAYS
)

os.makedirs(PROCESSED_DIR, exist_ok=True)

BIKE_PATH = os.path.join(RAW_DIR, "bicycle_network.geojson")
BAYS_PATH = os.path.join(RAW_DIR, "on_street_parking_bays.geojson")
SUBURBS_PATH = os.path.join(RAW_DIR, "suburbs.geojson")


def extract_street(desc: str) -> str:
    """
    Extracts the main street name from a road segment description.
    """
    if not desc:
        return ""
    desc = desc.strip()
    if desc.lower().startswith("intersection of"):
        return ""  # Ignore intersections
    parts = desc.split(" between ")
    if len(parts) > 1:
        return parts[0].strip()
    parts = desc.split(" from ")
    if len(parts) > 1:
        return parts[0].strip()
    return desc


def main() -> None:
    """
    Main execution function to perform spatial joins and filter supported streets.
    """
    if not os.path.exists(BIKE_PATH) or not os.path.exists(BAYS_PATH) or not os.path.exists(SUBURBS_PATH):
        print("Raw GeoJSONs not found. Please run download_base_data.py first.")
        return

    print("Loading data...")
    gdf_bike = gpd.read_file(BIKE_PATH)
    gdf_bays = gpd.read_file(BAYS_PATH)
    gdf_suburbs = gpd.read_file(SUBURBS_PATH)

    print(f"Loaded {len(gdf_bike)} bike segments, {len(gdf_bays)} bays, {len(gdf_suburbs)} suburbs.")

    # Filter out virtual connectors (e.g., Centroid connectors) and non-line geometries
    keywords = ['bike', 'lane', 'path', 'separated', 'segregated', 'sharrow', 'chevron', 'shared']
    gdf_bike = gdf_bike[gdf_bike['description'].str.contains('|'.join(keywords), case=False, na=False)].copy()
    gdf_bike = gdf_bike[gdf_bike.geometry.geom_type.isin(['LineString', 'MultiLineString'])].copy()
    print(f"Filtered to {len(gdf_bike)} valid bicycle infrastructure line segments.")

    # Assign a unique bay_id since the dataset doesn't have one
    gdf_bays["bay_id"] = range(len(gdf_bays))

    # 1. Extract street name and filter out intersections
    gdf_bays["street_name"] = gdf_bays["roadsegmentdescription"].apply(extract_street)
    gdf_bays = gdf_bays[gdf_bays["street_name"] != ""].copy()
    print(f"Bays after dropping intersections: {len(gdf_bays)}")

    # 2. Spatial join bays with suburbs to get suburb name
    print("Spatial join bays with suburbs...")
    gdf_bays = gdf_bays.to_crs(epsg=EPSG_WGS84)
    gdf_suburbs = gdf_suburbs.to_crs(epsg=EPSG_WGS84)
    
    bays_with_suburb = gpd.sjoin(
        gdf_bays, 
        gdf_suburbs[["featurenam", "geometry"]], 
        how="inner", 
        predicate="within"
    )
    bays_with_suburb = bays_with_suburb.rename(columns={"featurenam": "suburb"})
    
    if "index_right" in bays_with_suburb.columns:
        bays_with_suburb = bays_with_suburb.drop(columns=["index_right"])

    print(f"Bays after suburb join: {len(bays_with_suburb)}")

    # 3. Project to localized CRS
    print(f"Projecting to EPSG:{EPSG_PROJECTED}...")
    bays_proj = bays_with_suburb.to_crs(epsg=EPSG_PROJECTED)
    bike_proj = gdf_bike.to_crs(epsg=EPSG_PROJECTED)

    # 4. Buffer bays and perform Spatial Join with bike segments
    print(f"Buffering parking bays by {BUFFER_PARKING_BAYS} meters...")
    bays_proj["geometry_buffered"] = bays_proj.geometry.buffer(BUFFER_PARKING_BAYS)
    bays_buffer = bays_proj.set_geometry("geometry_buffered")

    print("Performing spatial join between bike segments and buffered bays...")
    matched = gpd.sjoin(
        bike_proj, 
        bays_buffer, 
        how="inner", 
        predicate="intersects"
    )

    # Filter streets that have at least 10 bays adjacent to bike lanes
    street_counts = matched.groupby(["suburb", "street_name"])["bay_id"].nunique().reset_index()
    supported_streets = street_counts[street_counts["bay_id"] >= 10][["suburb", "street_name"]]
    
    print(f"Found {len(supported_streets)} supported street-suburb combinations with >= 10 bays.")

    # Keep only rows in matched belonging to supported streets
    matched = matched.merge(supported_streets, on=["suburb", "street_name"], how="inner")

    # 5. Extract unique bike segments and unique bays
    def most_frequent(x):
        return x.value_counts().index[0] if not x.empty else None

    print("Mapping primary suburb and street to bike segments...")
    bike_mapping = matched.groupby("objectid").agg(
        suburb=("suburb", most_frequent),
        street_name=("street_name", most_frequent)
    ).reset_index()

    bike_matched = gdf_bike.merge(bike_mapping, on="objectid", how="inner")
    
    bays_matched = bays_with_suburb.merge(supported_streets, on=["suburb", "street_name"], how="inner")

    print(f"Final matched bike segments: {len(bike_matched)}")
    print(f"Final bays on supported streets: {len(bays_matched)}")

    # 6. Project back to WGS84 and Save
    print("Projecting back to WGS84...")
    bike_out = bike_matched.to_crs(epsg=EPSG_WGS84)
    bays_out = bays_matched.to_crs(epsg=EPSG_WGS84)

    out_bike = os.path.join(PROCESSED_DIR, "matched_bike_segments.geojson")
    out_bays = os.path.join(PROCESSED_DIR, "matched_parking_bays.geojson")

    bike_out.to_file(out_bike, driver="GeoJSON")
    bays_out.to_file(out_bays, driver="GeoJSON")

    print(f"Saved matched layers to {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
