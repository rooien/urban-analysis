# Data Curation & Transformation Pipeline

This document details the complete end-to-end data curation, geospatial processing, and cleanup pipeline implemented to build the Urban Impact Dashboard. The pipeline transforms raw spatial layers and massive transactional sensor events into a high-performance DuckDB database supporting interactive analytical queries.

## Pipeline Architecture & Execution Order

The ingestion pipeline is orchestrated sequentially via `run_ingestion.py` in the following steps:

1. **`download_base_data.py`**: Fetches raw spatial GeoJSON datasets.
2. **`match_bike_lanes.py`**: Pre-processes layers, performs spatial joins, and filters supported streets.
3. **`filter_supported_events.py`**: Extracts relevant parking transactions from 80M+ row CSVs into columnar Parquet files.
4. **`aggregate_occupancy.py`**: Calculates hourly occupancy rates per block, handling time-overlaps and cross-street normalization.
5. **`match_bike_to_blocks.py`**: Dissolves geometries into unified blocks and builds the final dashboard summary tables.

---

## 1. Geospatial Normalization & Projections

* **Coordinate System Alignment**: Raw datasets are provided in WGS 84 (EPSG:4326) degrees. Since precise planar distances are required for spatial joins (e.g., matching lanes to bays), all vector layers are dynamically reprojected to the localized GDA2020 / VicGrid system (EPSG:7899) before processing, and back to WGS 84 before saving to disk.
* **Network Graph Cleanup**: The raw Bicycle Infrastructure Network (BIN) includes virtual connectors (e.g., straight lines to properties or train station entrances) that create visual artifacts. These are filtered out using strict keyword matching (keeping segments with "lane", "path", "segregated", etc.) and enforcing `LineString` or `MultiLineString` geometry types.
* **Intersection Suppression**: Parking records tagged as `Intersection of ...` in their road segment descriptions are dropped to avoid breaking linear street aggregation blocks.

## 2. Spatial Joins & Street Constraints

* **Suburb Boundary Enforcement**: Individual parking bays are intersected with official CLUE neighborhood boundaries to accurately assign suburbs.
* **Proximity Buffering**: Bike lanes are buffered by 20 meters. A spatial intersecting join maps which physical parking bays run adjacent to newly constructed cycling infrastructure.
* **Statistical Significance Threshold**: To avoid analyzing isolated parking spots or experimental lane segments, streets are completely excluded from the dataset unless they contain at least 10 on-street parking bays directly intersecting the bike lane buffer.

## 3. High-Volume Transactional Filtering (DuckDB)

The raw City of Melbourne historical parking sensor dataset contains over 80 million rows per year. 
* **Optimized I/O**: Instead of loading these into Pandas memory, the pipeline leverages DuckDB's streaming `read_csv_auto` capabilities with columnar filtering.
* **Invalid Event Dropping**: Records are strictly dropped if `ArrivalTime` or `DepartureTime` is missing, or if `DurationSeconds` is $\leq 0$.
* **Pushdown Street Filtering**: Events are immediately filtered down to only the exact subset of street names that survived the spatial join steps.

## 4. Normalization & Matching Bugs Resolved

To ensure the events accurately map to the geographic blocks, precise cross-street matching is applied:

### A. The `Lt` vs `LITTLE` Abbreviation Bug
* **Issue**: The spatial bays dataset spelled out cross-streets fully (e.g., `Little Lonsdale Street`), whereas the historical sensor CSVs frequently abbreviated them (e.g., `Lt LONSDALE STREET`). Because of this string mismatch, 24 major CBD blocks were originally failing to join and dropping from the pipeline.
* **Cleanup Strategy**: Implemented symmetrical string cleaning across both Python and DuckDB SQL. Regular expressions strip excess whitespace, uppercase the strings, and explicitly replace `LITTLE ` with `LT ` and `SAINT ` with `ST ` before generating block keys.

### B. The Boundary Street Suburb Collision Bug
* **Issue**: Streets that form the geographic border between two suburbs (e.g., Spring Street, Victoria Street, La Trobe Street) dissolved into separate geometry blocks per suburb. However, the raw sensor CSV arbitrarily tagged the street with only one primary suburb. As a result, one side of the street would correctly show data, while the other side showed 0 bays in the dashboard.
* **Cleanup Strategy**: Removed the redundant `suburb` parameter from the relational join clauses in both the aggregation step and the backend API. Since the combination of `street_name` and `block_desc` is globally unique within the spatial network, the pipeline now maps the single correct occupancy profile uniformly across the dissolved boundary blocks regardless of which side-of-the-street attribute they carry.

## 5. Metric Calculation & Aggregation

* **Time Interval Intersection**: Occupied minutes for every hour bucket (0-23) are calculated precisely by determining the overlap between the event interval and the 60-minute hour window using: 
  `SUM(LEAST(DepartureTime, hr_end) - GREATEST(ArrivalTime, hr_start))`.
* **Dynamic Capacity Baseline**: Rather than relying on a static bay count (which fluctuates daily due to construction closures or sensor faults), total block capacity is dynamically computed per month as the maximum distinct number of active devices seen broadcasting on that block within the month. 
* **Capping Noise**: Real-world sensor noise or slight time overlaps occasionally push the raw occupied minutes above the mathematical maximum. Occupancy rates are strictly capped at `1.0` (100%) in the final table using `LEAST(1.0, occupancy_rate)`.
* **Geometry Dissolution**: Individual adjacent vector line segments sharing the same suburb, street, and block description are dissolved into a single unified geometry string (`geom_json`) during pipeline finalization. This compresses the final GeoJSON output sent to the frontend by roughly 80%, dramatically improving the vector rendering performance of the Maplibre GL canvas.
