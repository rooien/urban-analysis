# Victoria Urban Planning - Project Roadmap & Task List

This file outlines the comprehensive, granular tasks required to build the Urban Streetscape Intervention Analysis platform (Stream 2: Traffic Volumes & Parking) from the ground up, including the full Exploratory Data Analysis (EDA) and proxy methodologies as outlined in DATA.md and README.md.

The roadmap is phased over three sprints, each culminating in a key milestone.

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

---

## Sprint 2: Application Serving (Backend API) & Core Spatial Frontend
**Objective:** Develop the backend REST API to serve geospatial and metrics data, and build the interactive mapping frontend to visualize the intervention corridors.
**Key Milestone 2:** A functional end-to-end prototype mapping bike lanes and dynamically displaying baseline Metrics overlays.

### 2.1 Backend API Development (FastAPI)
- [ ] As a Frontend Developer, I want an API endpoint that returns GeoJSON features of bike lanes, buffer zones, and intervention dates so that they can be rendered dynamically on the interactive map.
- [ ] As a Frontend Developer, I want an API endpoint that returns aggregated spatial metrics grouped by block or intersection so that Before/After overlays can be displayed on the map.
- [ ] As a Frontend Developer, I want an API endpoint that returns granular time-series metrics parameterized by intervention so that time-of-day graphs can be populated.

### 2.2 Frontend Application Foundation
- [ ] As an End User, I want a premium and modern user interface with smooth animations, high readability, and responsive styling so that the application is engaging and professional.
- [ ] As an Urban Planner, I want a high-performance geospatial rendering engine integrated into the dashboard so that dense spatial data layers can be viewed and interacted with smoothly.

### 2.3 Interactive Geospatial Dashboard
- [ ] As an End User, I want a top-level application header so that I can easily navigate the dashboard and understand its context.
- [ ] As an Urban Planner, I want to view intervention layers on a map with styling based on buffer type or volume metrics so that I can visually distinguish spatial impacts.
- [ ] As an Urban Planner, I want to click on an intervention zone and see a popup with summarized street-level metrics so that I can quickly inspect localized data.
- [ ] As an Urban Planner, I want to use reactive control panels to filter data by LGA, Year, or Category so that the map dynamically updates with relevant information.

---

## Sprint 3: Advanced Time-Series Dashboards, Proxy Integrations, & Performance Tuning
**Objective:** Build detailed temporal visualizations, integrate proxy data pipelines, and optimize frontend and backend performance.
**Key Milestone 3:** A production-ready, highly responsive Victoria Urban Planning Impact Dashboard providing decision-ready insights.

### 3.1 Advanced Analytics Visualizations
- [ ] As an Urban Planner, I want an advanced analytics dashboard with interactive charts integrated so that I can explore complex data trends beyond the map.
- [ ] As a Transport Analyst, I want Area and Line charts comparing baseline versus post-intervention hourly occupancy so that I can identify shifts in parking utilization patterns.
- [ ] As a Transport Analyst, I want dual-axis graphs comparing traffic and bicycle volumes so that I can visualize and validate explicit mode shifts.
- [ ] As an End User, I want charts to handle asynchronous loading and responsive resizing gracefully so that the interface remains seamless and readable across devices.

### 3.2 Proxy Integrations & Performance Tuning
- [ ] As a Data Scientist, I want to finalize the execution of the aerial imagery proxy pipeline and load results into the database so that non-sensor LGA data is available for the final analysis.
- [ ] As an End User, I want backend database queries optimized with indices and views so that the dashboard loads metrics and charts with minimal latency.
- [ ] As an End User, I want the geospatial rendering optimized using chunking or clustering strategies so that I can experience smooth 60 FPS interactions on dense data grids.

### 3.3 Polish, Accessibility, & Documentation
- [ ] As an End User, I want the application audited and optimized for WCAG accessibility, high contrast readability, and premium aesthetics so that it is inclusive and professional.
- [ ] As a Product Owner, I want a comprehensive final write-up summarizing research outcomes, hypothesis testing, and future recommendations so that I can deliver clear insights to government stakeholders.
