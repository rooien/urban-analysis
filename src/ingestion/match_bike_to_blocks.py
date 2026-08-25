"""
Match Bike to Blocks Script

Assigns street block descriptions, suburbs, and street names to bike segments and
aggregates geometries to create unified block-level features. Builds summary tables
for baseline and post-intervention bay capacity and occupancy across all supported streets.
"""

import sys
import os
import json
import duckdb
import geopandas as gpd

# Ensure project root is in PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import (
    PROCESSED_DIR, DB_PATH,
    EPSG_PROJECTED, EPSG_WGS84, BUFFER_BIKE_LANES,
    BASELINE_YEAR, BASELINE_MONTHS, POST_YEAR, POST_MONTHS
)


def main() -> None:
    """
    Main execution function to map blocks to bike segments and generate summaries.
    """
    bike_path = os.path.join(PROCESSED_DIR, "matched_bike_segments.geojson")
    bays_path = os.path.join(PROCESSED_DIR, "matched_parking_bays.geojson")

    if not os.path.exists(bike_path) or not os.path.exists(bays_path):
        print("Required processed GeoJSONs not found. Run match_bike_lanes.py first.")
        return

    print("Loading data...")
    gdf_bike = gpd.read_file(bike_path)
    gdf_bays = gpd.read_file(bays_path)

    # Clean bike columns, keeping core attributes
    orig_cols = ['objectid', 'roadclass', 'geometry']
    gdf_bike = gdf_bike[[c for c in orig_cols if c in gdf_bike.columns]]

    # Project to localized CRS
    print(f"Projecting to EPSG:{EPSG_PROJECTED}...")
    gdf_bike_proj = gdf_bike.to_crs(epsg=EPSG_PROJECTED)
    bays_proj = gdf_bays.to_crs(epsg=EPSG_PROJECTED)

    # Buffer bike segments by configured meters
    print(f"Buffering bike segments by {BUFFER_BIKE_LANES} meters...")
    gdf_bike_proj["geometry_buffered"] = gdf_bike_proj.geometry.buffer(BUFFER_BIKE_LANES)
    gdf_bike_buffer = gdf_bike_proj.set_geometry("geometry_buffered")

    # Spatial Join: Points inside Buffered Lines
    print("Performing spatial join to map blocks to bike segments...")
    matched = gpd.sjoin(bays_proj, gdf_bike_buffer, how="inner", predicate="intersects")

    def most_frequent(x):
        return x.value_counts().index[0] if not x.empty else None

    print("Mapping primary suburb, street, and block to bike segments...")
    block_map = matched.groupby("objectid").agg(
        suburb=("suburb", most_frequent),
        street_name=("street_name", most_frequent),
        block_desc=("roadsegmentdescription", most_frequent)
    ).reset_index()

    # Merge back to original bike segments
    gdf_bike_mapped = gdf_bike.merge(block_map, on="objectid", how="inner")

    print(f"Mapped {len(gdf_bike_mapped)} bike segments to blocks.")

    # Dissolve by suburb, street, and block_desc to get a single unified geometry per block
    print("Dissolving geometries by block...")
    blocks_geom = gdf_bike_mapped.dissolve(by=["suburb", "street_name", "block_desc"]).reset_index()

    # Project to WGS84 for GeoJSON
    blocks_geom = blocks_geom.to_crs(epsg=EPSG_WGS84)

    # Save to DuckDB
    print("Saving geometries to DuckDB...")
    con = duckdb.connect(DB_PATH)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS block_geometries (
        suburb VARCHAR,
        street_name VARCHAR,
        block_desc VARCHAR,
        geom_json VARCHAR
    )
    """)
    con.execute("DELETE FROM block_geometries")

    # Convert geometry to GeoJSON string for easy frontend consumption
    for _, row in blocks_geom.iterrows():
        geom_json = json.dumps(row.geometry.__geo_interface__)
        con.execute(
            "INSERT INTO block_geometries VALUES (?, ?, ?, ?)", 
            (row.suburb, row.street_name, row.block_desc, geom_json)
        )

    # Format month lists as SQL tuples
    base_months_str = str(tuple(BASELINE_MONTHS))
    post_months_str = str(tuple(POST_MONTHS))

    print("Building blocks_summary table...")
    # Create the summary table
    con.execute(f"""
    CREATE OR REPLACE TABLE blocks_summary AS
    WITH baseline AS (
        SELECT street_name, block_desc, MAX(bay_count) as baseline_bays
        FROM hourly_occupancy
        WHERE year = {BASELINE_YEAR} AND month(hr) IN {base_months_str}
        GROUP BY 1, 2
    ),
    final AS (
        SELECT street_name, block_desc, MAX(bay_count) as final_bays
        FROM hourly_occupancy
        WHERE year = {POST_YEAR} AND month(hr) IN {post_months_str}
        GROUP BY 1, 2
    ),
    occupancy_stats AS (
        SELECT 
            street_name,
            block_desc,
            year,
            AVG(occupancy_rate) as avg_occupancy
        FROM hourly_occupancy
        WHERE (year = {BASELINE_YEAR} AND month(hr) IN {base_months_str}) 
           OR (year = {POST_YEAR} AND month(hr) IN {post_months_str})
        GROUP BY 1, 2, 3
    )
    SELECT 
        g.suburb,
        g.street_name,
        g.block_desc,
        g.geom_json,
        COALESCE(b.baseline_bays, 0) as baseline_bays,
        COALESCE(f.final_bays, 0) as final_bays,
        (COALESCE(b.baseline_bays, 0) - COALESCE(f.final_bays, 0)) as bays_removed,
        MAX(CASE WHEN s.year = {BASELINE_YEAR} THEN s.avg_occupancy ELSE NULL END) as pre_occupancy,
        MAX(CASE WHEN s.year = {POST_YEAR} THEN s.avg_occupancy ELSE NULL END) as post_occupancy
    FROM block_geometries g
    LEFT JOIN baseline b ON g.street_name = b.street_name AND g.block_desc = b.block_desc
    LEFT JOIN final f ON g.street_name = f.street_name AND g.block_desc = f.block_desc
    LEFT JOIN occupancy_stats s ON g.street_name = s.street_name AND g.block_desc = s.block_desc
    GROUP BY 1, 2, 3, 4, 5, 6, 7
    """)

    print("Blocks summary table created!")
    
    # Print a quick summary of distinct streets that actually got matched with historical data
    res = con.execute("""
        SELECT suburb, count(distinct street_name) as streets_with_data, count(*) as total_blocks 
        FROM blocks_summary 
        WHERE baseline_bays > 0 OR final_bays > 0 
        GROUP BY 1 
        ORDER BY 2 DESC
    """).df()
    
    print("\nSummary of streets with actual historical data support:")
    print(res)

    con.close()


if __name__ == "__main__":
    main()
