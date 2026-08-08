# Urban Mobility Impact Dashboard: Data Architecture & Transformation Report

This document details the datasets utilized in the Urban Mobility Impact Dashboard, the spatial and temporal constraints dictated by data availability, and the ETL pipeline required to transform raw sources into decision-ready metrics.

## 1. Data Uses in the Application

The application leverages four primary datasets (detailed with citations in [Section 4](#4-specific-data-sources-and-citations)) to drive its spatial visualizations, analytical metrics, and hourly occupancy charts. 

The On-Street Parking Bays dataset from the City of Melbourne provides vector geometries and primary keys for individual parking bays. The application uses this layer to identify parking locations, dynamically calculate spatial capacities, and extract descriptive block boundaries—such as "La Trobe Street between King Street and Spencer Street"—which are used to segment the dashboard. 

To support the before-and-after comparison of parking utilization, a massive transactional dataset of Historical On-Street Parking Sensor Events from 2013 and 2014 captures individual vehicle arrival and departure timestamps recorded by in-ground sensors. This data is used to compute time-series occupancy rates across a 24-hour cycle.

For the cycling infrastructure, the Bicycle Infrastructure Network provides linear geometries representing cycling routes. Once heavily filtered, this dataset drives the blue vector lines on the map, allowing users to visually correlate the location of physical bike lanes with adjacent parking blocks.

Finally, the Small Areas for Census of Land Use and Employment (CLUE) Suburbs dataset provides boundary polygons for City of Melbourne neighborhoods. The application uses this layer to spatially partition the data, allowing users to filter the dashboard by recognized suburb cohorts such as the Melbourne CBD, Carlton, and Docklands.

## 2. Constraints Based on Available Data

The scope, granularity, and geographical limits of the dashboard are strictly constrained by the underlying data characteristics. Although statewide and regional bike lanes are documented, granular historical parking utilization metrics depend heavily on in-ground sensor infrastructure. Since high-resolution sensors are almost exclusively deployed by the City of Melbourne, the analytical boundaries of the application are strictly constrained to the City of Melbourne municipality.

Evaluating the impact of bike lane interventions requires comparing specific years before and after construction, while avoiding the massive behavioral shifts caused by the COVID-19 pandemic. Consequently, the application relies on hardcoded historical snapshots of 2013 versus 2014, which prevents continuous or real-time trend analysis. 

To ensure statistical significance and avoid analyzing isolated parking spots or edge cases, the pipeline enforces a constraint where a street must contain at least 10 on-street parking bays intersecting the bike lane buffer to be included in the application. Furthermore, temporary construction closures, sensor faults, or streetscape modifications cause the daily active bay count on a given block to fluctuate. To prevent this statistical noise, the block capacity is calculated using the maximum recorded monthly bay count rather than a daily average. 

Finally, sensor events and bays directly tied to street intersections, such as the intersection of La Trobe Street and King Street, are entirely excluded from the analysis. These points do not map cleanly to linear street blocks, and including them would introduce ambiguity and potential double-counting in block-level aggregates.

## 3. Data Transformations Required

Transforming raw geospatial and transactional data into an optimized, low-latency format for the React and FastAPI application requires a multi-stage Python and DuckDB ingestion pipeline located in the `src/ingestion/` directory. 

### Geospatial Reprojection and Normalization

Raw datasets are initially ingested in global coordinates using WGS84. Because degrees are unsuitable for precise distance metrics, geometries are projected into a local planar coordinate system, specifically GDA2020 / VicGrid (EPSG:7899), to execute accurate 20-meter spatial buffers. After processing, the coordinates are reprojected back to WGS84 to ensure compatibility with GeoJSON and the Maplibre frontend viewer. Additionally, street names in the sensor datasets often contain inconsistent formatting, such as variations between "LITTLE" and "LT" or extra spacing. Strict regex normalizations are applied to both the spatial layers and the event tables to ensure exact string matching during tabular joins.

### Semantic Filtering of Transportation Networks

The raw Bicycle Infrastructure Network dataset is structured as a multimodal routing model, containing tens of thousands of "Centroid connectors" and "Entrance connectors" which are virtual straight lines drawn between properties and roads. These connectors are semantically filtered out using keyword string matching on the description field to prevent severe visual artifacts and spikes on the map. Furthermore, a topological cleanup strips out non-linear geometries, such as Point features representing network nodes, guaranteeing that only clean LineString and MultiLineString elements are passed to the frontend rendering engine.

### Spatial Joins and Buffer Intersections

To establish spatial relationships, parking bays are buffered by 20 meters and intersected with CLUE boundaries, assigning a definitive suburb attribute to each individual bay. Validated bike infrastructure lines are similarly buffered by 20 meters and spatially intersected with the parking bays layer. A spatial grouping operation then determines the primary block description for each bike segment, effectively mapping which bike lanes correspond to which parking blocks.

### Geometry Dissolution

To optimize frontend rendering performance, individual adjacent bike segment vectors are grouped by suburb, street name, and block description. A dissolve operation using a unary union merges them into unified, continuous block features, which drastically reduces the final GeoJSON payload size sent to the client.

### High-Volume Time-Series Aggregation

Processing over 80 million raw event rows entirely in memory is inefficient. To handle this volume, the raw CSVs are partitioned, filtered by the supported streets, and exported into compressed, columnar Apache Parquet files using DuckDB. Finally, using DuckDB window functions, overlapping arrival and departure intervals are computed across 24 hourly buckets. The total occupied minutes for each hour are divided by the total available block capacity for that month—calculated as the bay count multiplied by 60 minutes—to derive precise hourly occupancy rates for the dashboard charts.

## 4. Specific Data Sources and Citations

The four primary datasets utilized in this application are publicly available via the City of Melbourne Open Data portal and Transport Victoria. 

The On-Street Parking Bays dataset provides the vector geometries and primary keys for individual parking bays, and can be accessed at [https://data.melbourne.vic.gov.au/explore/dataset/on-street-parking-bays/information/](https://data.melbourne.vic.gov.au/explore/dataset/on-street-parking-bays/information/).

The historical transactional datasets capturing vehicle arrival and departure timestamps recorded by in-ground sensors are split by year. The 2013 Historical On-Street Parking Sensor Events are available at [https://data.melbourne.vic.gov.au/explore/dataset/on-street-car-parking-sensor-data-2013/information/](https://data.melbourne.vic.gov.au/explore/dataset/on-street-car-parking-sensor-data-2013/information/), and the 2014 dataset is available at [https://data.melbourne.vic.gov.au/explore/dataset/on-street-car-parking-sensor-data-2014/information/](https://data.melbourne.vic.gov.au/explore/dataset/on-street-car-parking-sensor-data-2014/information/).

The Bicycle Infrastructure Network dataset, representing linear geometries of cycling routes, is published by the City of Melbourne with data sourced from Transport Victoria, and is accessible at [https://data.melbourne.vic.gov.au/explore/dataset/bicycle-network/information/](https://data.melbourne.vic.gov.au/explore/dataset/bicycle-network/information/).

Finally, the Small Areas for Census of Land Use and Employment dataset, which provides the boundary polygons for the neighborhoods and suburbs used to partition the data, can be found at [https://data.melbourne.vic.gov.au/explore/dataset/small-areas-for-census-of-land-use-and-employment-clue/information/](https://data.melbourne.vic.gov.au/explore/dataset/small-areas-for-census-of-land-use-and-employment-clue/information/).

Additionally, the basemap tiles used in the frontend viewer are served via MapLibre GL using the Carto Dark Matter style, available at [https://carto.com/](https://carto.com/).
