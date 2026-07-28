# Victoria Urban Planning - Project Roadmap & Task List

This file outlines the comprehensive, granular tasks required to build the Urban Streetscape Intervention Analysis platform (Stream 2: Traffic Volumes & Parking) from the ground up, including the full Exploratory Data Analysis (EDA) and proxy methodologies as outlined in DATA.md and README.md.

The roadmap is phased over three sprints, each culminating in a key milestone.

---

## Sprint 1: Data Acquisition, Multi-Stream EDA, and Core Spatial ETL
**Objective:** Ingest all relevant public datasets, perform rigorous Exploratory Data Analysis (EDA) to validate proxy methodologies, resolve CRS discrepancies, and build the foundational spatial database schema.
**Key Milestone 1:** A fully populated, query-optimized DuckDB database and a complete suite of EDA notebooks validating Before/After metrics.

### 1.1 Project Bootstrapping & Environment Setup
- [ ] Initialize the Git repository, configure the comprehensive `.gitignore`, and establish the standardized directory structure (`data/raw/`, `data/processed/`, `notebooks/`, `src/ingestion/`, `src/api/`, `frontend/`).
- [ ] Define the Python virtual environment and list exact dependencies in requirements.txt (FastAPI, DuckDB, GeoPandas, Shapely, PyYAML, etc.).
- [ ] Create the central config.yaml to manage shared parameters (ports, buffer distances, historical years, and CRS strings).
- [ ] Implement src/config.py to expose YAML configurations as strongly-typed, module-level Python constants.

### 1.2 Data Acquisition & Preparation
- [ ] Implement src/ingestion/download_base_data.py to automatically fetch and store raw datasets (Bicycle Infrastructure Network, Pop-up Bike Lanes, Suburbs GeoJSON, SCATS Volumes, and Parking Sensor historical records) into `data/raw/`.
- [ ] Formulate a proxy data acquisition workflow for Remote Sensing data (Vicmap Aerial Imagery or Google Earth Historical imagery) and local council pedestrian/spend portals as outlined in DATA.md.

### 1.3 Multi-Stream Exploratory Data Analysis (EDA)
- [ ] **Task 1.3.1 - Spatial & Intervention Temporal Analysis**
  - Create notebooks/01_bike_lanes_eda.ipynb to map bike lane networks and extract exact construction dates ($T_c$) across all target LGAs.
  - Document spatial overlaps with existing on-street parking infrastructure using Buffer analysis.
- [ ] **Task 1.3.2 - Traffic & Active Transport Trends**
  - Create notebooks/02_traffic_volumes_eda.ipynb to parse SCATS 15-minute interval data and historical AADT.
  - Aggregate traffic and intersection turning movements by hour/day to establish baseline congestion profiles.
- [ ] **Task 1.3.3 - Parking Proxies & Sensor Evaluation**
  - Create notebooks/03_parking_and_aerial_imagery_eda.ipynb to evaluate City of Melbourne (CoM) historical parking sensor records.
  - Prototype the Remote Sensing approach: use a pre-trained Object Detection model (e.g., YOLO) or manual sampling on aerial imagery to count parked cars in buffers ($T_c \pm 6$ months) for non-sensor LGAs.
- [ ] **Task 1.3.4 - Economic Proxies & CRS Resolution**
  - Create notebooks/04_economic_social_eda.ipynb to explore VISTA survey data and map footfall metrics.
  - Identify all CRS mismatches (e.g., GDA2020/VICGRID94 vs Web Mercator) and document the precise mathematical reprojection strategy.

### 1.4 Spatial ETL Pipeline Implementation
- [ ] Implement src/ingestion/match_bike_lanes.py to spatially join bike infrastructure segments with raw street networks and suburbs, applying explicit GeoPandas buffer logic.
- [ ] Implement src/ingestion/filter_supported_events.py to filter massive time-series parking sensor and SCATS records strictly by the historical baseline and post-intervention bounds.
- [ ] Implement src/ingestion/aggregate_occupancy.py to aggregate raw block-level and intersection-level event streams into hourly average occupancy rates and traffic volumes.
- [ ] Implement src/ingestion/match_bike_to_blocks.py to map the aggregated spatial blocks and intersections back to specific bike lane corridors, preparing the Before/After summary matrices.
- [ ] Initialize the DuckDB relational and spatial database schema (`data/parking_analytics.duckdb`) to optimize analytical queries over millions of rows.
- [ ] Write the pipeline orchestrator run_ingestion.py to execute the full ETL sequence sequentially and log execution durations.

---

## Sprint 2: Application Serving (Backend API) & Core Spatial Frontend
**Objective:** Develop the backend REST API to serve geospatial and metrics data, and build the interactive mapping frontend to visualize the intervention corridors.
**Key Milestone 2:** A functional end-to-end prototype mapping bike lanes and dynamically displaying baseline Metrics overlays.

### 2.1 Backend API Development (FastAPI)
- [ ] Initialize the FastAPI application in src/api/main.py with OpenAPI documentation and Pydantic schema validation.
- [ ] Configure Cross-Origin Resource Sharing (CORS) middleware to allow seamless asynchronous requests from the frontend development server.
- [ ] Implement thread-safe connection pooling to the read-only DuckDB instance.
- [ ] Develop `GET /api/v1/interventions`: An endpoint returning GeoJSON features representing the bike lanes, buffer zones, and high-level intervention dates.
- [ ] Develop `GET /api/v1/metrics/spatial`: An endpoint returning aggregated Before/After parking utilization and traffic volume metrics grouped by block or intersection.
- [ ] Develop `GET /api/v1/metrics/temporal`: An endpoint parameterized by `intervention_id`, returning granular time-series data for time-of-day graphs.

### 2.2 Frontend Application Foundation
- [ ] Scaffold the React application using Vite in `frontend/`.
- [ ] Configure the styling foundation (CSS or Tailwind CSS) applying premium design principles, smooth micro-animations, and modern typography tokens.
- [ ] Integrate MapLibre GL (`maplibre-gl` and `react-map-gl`) to handle high-performance, vector-tile geospatial rendering.

### 2.3 Interactive Geospatial Dashboard
- [ ] Build the frontend/src/components/Header.jsx component to handle top-level application navigation and branding.
- [ ] Build the frontend/src/components/MapContainer.jsx component to render the intervention GeoJSON layers, styling colors by buffer type or volume metric.
- [ ] Implement interactive popup tooltips that display summarized street-level metrics when a user clicks on an intervention zone.
- [ ] Implement reactive control panels (filtering by LGA, Year, or Intervention Category) that dynamically trigger API refetches and update the map layers.

---

## Sprint 3: Advanced Time-Series Dashboards, Polish, & Orchestration
**Objective:** Build detailed temporal visualizations, integrate proxy data pipelines, optimize performance, and create seamless pipeline orchestration scripts.
**Key Milestone 3:** A production-ready, highly responsive Victoria Urban Planning Impact Dashboard providing decision-ready insights.

### 3.1 Advanced Analytics Visualizations
- [ ] Integrate Recharts (`recharts`) to build the frontend/src/components/ImpactDashboard.jsx component.
- [ ] Implement Area and Line charts comparing Average Hourly Occupancy (e.g., Baseline vs. Post-Intervention).
- [ ] Create dual-axis graphs displaying SCATS traffic volumes alongside Bicycle counter volumes to visualize explicit mode shifts.
- [ ] Ensure all Recharts components gracefully handle asynchronous loading states and responsive resizing.

### 3.2 System Orchestration & Environment Automation
- [ ] Implement run_app.py to fully automate the local deployment lifecycle:
  - Initialize and activate the Python virtual environment.
  - Install backend dependencies and frontend dependencies.
  - Automatically generate the frontend `.env` file dynamically injecting ports and variables from config.yaml.
  - Spin up both the FastAPI Uvicorn server and the Vite development server concurrently with stdout streaming.
- [ ] Implement stop_app.py to accurately locate and gracefully terminate running background processes to free up active ports.

### 3.3 Proxy Integrations & Performance Tuning
- [ ] Finalize the production execution of the computer-vision or sampling-based Aerial Imagery data proxy pipeline for non-CoM LGAs, loading the proxy results into DuckDB.
- [ ] Optimize DuckDB analytical queries by creating composite indices and materialized views for time-series aggregate routes.
- [ ] Optimize MapLibre GL rendering using source data chunking or cluster strategies to ensure 60 FPS interactions on dense data grids.

### 3.4 Polish, Accessibility, & Documentation
- [ ] Perform UI/UX audits to ensure WCAG accessibility standards, high contrast readability, and a flawless premium aesthetic.
- [ ] Verify that all existing comments and docstrings are perfectly preserved, adhering to strict Coding Standards outlined in CODING_STANDARDS.md.
- [ ] Compile the final write_up.md summarizing the research outcomes, hypothesis testing (Null Hypothesis: No change in parking capacity), and future recommendations.
