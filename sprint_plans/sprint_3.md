# Sprint 3 Task List — Stream B: Pipeline Hardening, EDA Transformations & Stakeholder Dashboard

## 1. Sprint 3 Objective & Priorities

In **Sprint 1**, the team completed exploratory data analysis (EDA) across bicycle networks, parking sensor logs, SCATS traffic volumes, and pop-up bike lane datasets.  
In **Sprint 2**, the team built the initial Python ingestion scripts to load spatial layers and parking sensor events into **DuckDB**, generate GeoJSON layers, and start the basic web app.

For **Sprint 3**, the focus is on finishing the Proof of Concept (POC) by making the ingestion scripts reliable, applying the key findings from our team's EDA notebooks into DuckDB tables, and determining the best way to visualize and deliver these insights to business stakeholders (evaluating Power BI, Tableau, and a custom web UI).

### Sprint 3 Priorities:
1. **Harden Ingestion Scripts:** Ensure `team_b/run_ingestion.py` runs smoothly from start to finish with clear error messages and support for site-specific time windows from `sites_db.csv`.
2. **Apply Team EDA Findings:** Calculate key metrics in DuckDB (overall parking capacity changes, occupancy rates, stay duration / turnover, pop-up bike lane retention rates, and corridor case studies).
3. **Investigate & Build Stakeholder Visualization Layer:** Evaluate the best visualization tool (Power BI vs. Tableau vs. Custom Web UI) to communicate findings to business owners and council stakeholders, and implement the stakeholder presentation views.

---

## 2. Tasks for Sprint 3

### Epic 1: Ingestion Pipeline Hardening

#### Task SB-301: Harden Ingestion Scripts & Error Handling
- **Priority:** High
- **Description:** Clean up and test all scripts in [`team_b/ingestion/`](../team_b/ingestion) to make sure they run reliably without crashing. Add simple checks for missing files and clear error messages so any team member can run the pipeline easily.
- **Acceptance Criteria:**
  - Running `python team_b/run_ingestion.py` executes all steps sequentially without manual steps.
  - If a raw file is missing, the script gives a clear and helpful error message.
  - Generates updated tables in `team_b/data/parking_analytics.duckdb`.

#### Task SB-302: Connect Site-Specific Intervention Windows
- **Priority:** High
- **Description:** Update [`src/ingestion/filter_parking_by_site_windows.py`](../src/ingestion/filter_parking_by_site_windows.py) to read intervention dates from [`data/raw/sites_db.csv`](../config.yaml) and filter sensor data around each site's specific construction window.
- **Acceptance Criteria:**
  - Reads site intervention dates from `sites_db.csv`.
  - Filters pre- and post-intervention sensor records based on the configured window (e.g. 2 months before/after).
  - Saves the filtered output into DuckDB.

---

### Epic 2: Apply Team EDA Findings & Transformations

#### Task SB-303: Transform & Store Key Parking Metrics in DuckDB
- **Priority:** High
- **Description:** Write a simple transformation script to calculate the key summary statistics discovered during EDA and store them in DuckDB:
  - Median capacity reduction for bike lanes (-8.1%) vs pedestrian malls (-100%).
  - Average occupancy before (6.77%) and after (6.60%) across monitored blocks.
  - Average parking stay duration (31.8 min before vs 31.9 min after).
  - Summary stats for the 4 corridor case studies: **Queensberry St**, **Bourke St**, **Macaulay Rd**, and **Adderley St**.
- **Acceptance Criteria:**
  - Creates a `stakeholder_metrics` table or view in `parking_analytics.duckdb`.
  - Accurately stores overall capacity change, occupancy averages, dwell times, and corridor metrics.

#### Task SB-304: Ingest & Summarize Pop-up Bike Lane Trial Data
- **Priority:** Medium
- **Description:** Ingest the pop-up bike lane dataset and summarize the trial retention findings from Lavan's EDA (354 total segments: 114 retained permanently, 240 decommissioned; 93% retention in Port Phillip).
- **Acceptance Criteria:**
  - Ingests pop-up bike lane segments and tags them with retention status (`Retained` vs `Decommissioned`).
  - Stores the summary counts in DuckDB and outputs a clean GeoJSON file for the map.

---

### Epic 3: Business Stakeholder Visualization Layer

#### Task SB-305: Investigate & Compare Visualization Options (Power BI vs Tableau vs Custom Web UI)
- **Priority:** High
- **Description:** Research and evaluate the best visualization tool for communicating our parking and traffic insights to business owners, council planners, and non-technical stakeholders. Compare three main options:
  1. **Power BI / Tableau:** Fast report building, interactive filters, easy sharing with government/council staff using exported CSV/Parquet data.
  2. **Custom Web UI (React + MapLibre + FastAPI):** Interactive street-level map with 20m buffer layers, direct DuckDB integration, custom stakeholder card components, and zero license costs.
  3. **Lightweight Python Web UI (Streamlit / Dash):** Fast prototyping directly in Python connected to DuckDB.
- **Acceptance Criteria:**
  - Create a short comparison summary weighing: ease of use for business stakeholders, interactive map capability (corridors and blocks), DuckDB/Parquet data connectivity, and deployment/sharing ease.
  - Recommend the primary visualization approach for the project POC and prototype a sample view.

#### Task SB-306: Add FastAPI Endpoints for Stakeholder Insights
- **Priority:** High
- **Description:** Add simple endpoints in [`src/api/main.py`](../src/api/main.py) to serve high-level metrics and corridor case studies to the frontend or external BI tools.
- **Acceptance Criteria:**
  - `GET /api/analytics/summary` returns overall stats (median bay reduction %, average occupancy before/after, surplus parking %).
  - `GET /api/corridors/case-studies` returns data for Queensberry St, Bourke St, Macaulay Rd, and Adderley St.
  - `GET /api/popups/summary` returns pop-up bike lane retention stats.

#### Task SB-307: Add Business Stakeholder View to Dashboard
- **Priority:** High
- **Description:** Update [`frontend/src/components/ImpactDashboard.jsx`](../frontend/src/components/ImpactDashboard.jsx) to include a simple stakeholder-friendly view that directly addresses business owner questions:
  - **Key Finding Cards:** Show that over 90% of parking spaces were retained, and over 93% of parking bays remained available during trading hours.
  - **Supply vs. Demand Explanation:** Visual card explaining that removing ~8 bays leaves plenty of surplus spaces for typical customer demand.
  - **Corridor Case Studies:** Clickable cards for Queensberry St, Bourke St, Macaulay Rd, and Adderley St to quickly inspect their outcomes.
- **Acceptance Criteria:**
  - Stakeholder view renders cleanly with clear numbers, friendly labels, and explanatory text.
  - Clicking a case study highlights the street data on the dashboard.

#### Task SB-308: Add Pop-up Bike Lane Map Layer
- **Priority:** Medium
- **Description:** Add a toggle in [`frontend/src/components/MapContainer.jsx`](../frontend/src/components/MapContainer.jsx) to show pop-up bike lane lines on the map colored by retention status (e.g. Green for permanent, Gray for decommissioned).
- **Acceptance Criteria:**
  - Users can toggle the Pop-up Bike Lanes layer on/off.
  - Clicking a segment displays a popup with street name, LGA, and retention status.

---

### Epic 4: Verification & Handover

#### Task SB-309: End-to-End Pipeline & Dashboard Verification
- **Priority:** High
- **Description:** Test the entire application from raw data ingestion to frontend display to ensure a working, polished POC.
- **Acceptance Criteria:**
  - `python team_b/run_ingestion.py` runs cleanly without errors.
  - `python run_app.py` boots backend (port 7000/8000) and frontend (port 5000/5173).
  - All new stakeholder cards, case studies, and charts render live data correctly.


