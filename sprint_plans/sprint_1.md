# Sprint 1 Task List — Stream B: Traffic Volumes & Parking

This file outlines the comprehensive, granular tasks required to build the Urban Streetscape Intervention Analysis platform (Stream 2: Traffic Volumes & Parking) from the ground up, including the full Exploratory Data Analysis (EDA) and proxy methodologies as outlined in [data_inventory.md](../knowledge_base/data_inventory.md) and [README.md](../README.md).

---

## Sprint 1: Data Acquisition, Multi-Stream EDA, and Core Spatial ETL
**Objective:** Ingest all relevant public datasets, perform rigorous Exploratory Data Analysis (EDA) to validate proxy methodologies, resolve CRS discrepancies, and build the foundational spatial database schema.
**Key Milestone 1:** A fully populated, query-optimized DuckDB database and a complete suite of EDA notebooks validating Before/After metrics.

### 1.1 Data Acquisition & Preparation
- [ ] As a Data Analyst, I want to automatically download and store raw datasets (Bicycle Networks, SCATS Volumes, and Parking Records) so that I have a reliable and standardized local data source for analysis.
- [ ] As a Data Analyst, I want to establish a proxy data acquisition workflow using Remote Sensing and economic indicators so that I can evaluate impacts in LGAs lacking direct sensor infrastructure.

### 1.2 Multi-Stream Exploratory Data Analysis (EDA)
**Task 1.2.1 - Spatial & Intervention Temporal Analysis**
- [ ] As a Transport Planner, I want to conduct an EDA on bike lane network datasets to map infrastructure and extract exact construction dates across all target LGAs so that I can establish a precise intervention timeline.
- [ ] As a Transport Planner, I want to analyze and document spatial overlaps between bike lanes and parking infrastructure using buffer analysis so that I can identify zones with potential parking impacts.

**Task 1.2.2 - Traffic & Active Transport Trends**
- [ ] As a Transport Engineer, I want to conduct an EDA on SCATS interval data and historical AADT so that I can understand baseline traffic volumes and turning movements.
- [ ] As a Transport Engineer, I want to aggregate traffic and turning movements by hour and day so that I can establish baseline congestion profiles for comparisons.

**Task 1.2.3 - Parking Proxies & Sensor Evaluation**
- [ ] As a Data Analyst, I want to conduct an EDA on historical parking sensor records to evaluate baseline and post-intervention parking utilization in the City of Melbourne.
- [ ] As a Data Analyst, I want to prototype an aerial imagery object detection or sampling methodology to count parked cars in buffer zones for LGAs lacking sensor infrastructure.

**Task 1.2.4 - Economic Proxies & CRS Resolution**
- [ ] As an Urban Planner, I want to conduct an EDA on VISTA survey data and proxy metrics to explore broader economic and social impacts of the streetscape interventions.
- [ ] As a GIS Specialist, I want to identify and resolve all Coordinate Reference System mismatches so that all datasets align perfectly for accurate buffer analysis.

### 1.3 Spatial ETL Pipeline Implementation
- [ ] As a Data Engineer, I want to build a spatial pipeline that joins bike infrastructure with street networks and suburbs using buffer logic so that analytical zones are precisely defined.
- [ ] As a Data Engineer, I want to build a pipeline to filter time-series parking and SCATS records strictly by baseline and post-intervention bounds so that processing volume is optimized and relevant.
- [ ] As a Data Engineer, I want to build a pipeline that aggregates event streams into hourly average occupancy rates and traffic volumes so that data is summarized for performant serving.
- [ ] As a Data Engineer, I want to build a pipeline that maps aggregated blocks and intersections back to specific bike lane corridors so that the final Before/After summary matrices are produced.
- [ ] As a Data Engineer, I want to implement an optimized relational and spatial database schema so that analytical queries over millions of rows execute efficiently.
- [ ] As a Data Engineer, I want an automated ETL orchestrator that executes the full data pipeline sequentially and logs execution so that the ingestion process is reproducible and monitored.
