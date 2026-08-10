# Victoria Urban Planning - Urban Streetscape Intervention Analysis

This repository is for the SIT Capstone "Chameleon Project" in partnership with Infrastructure Victoria.

## Table of Contents
1. Project Overview
2. Business Problem & Research Question
3. Stream Structure
4. Tech Stack
5. Architecture & Key Components
6. Data Sources & CRS Warning
7. Directory Structure
8. Installation, Setup & Execution
9. Git Workflow & Collaboration Guide
10. Coding Standards

## Project Overview
Infrastructure Victoria is an independent advisory body providing evidence-based research to the Victorian Government. This project evaluates the real-world impacts of streetscape interventions (like new bike lanes, road reallocations, and pedestrian upgrades) on transport efficiency, sustainability, and livability. 

The goal is to develop a repeatable analytical framework to deliver clear, decision-ready insights for future infrastructure investments.

**Team & Roles:**
- **Product Owners:** Matthew Raisbeck & Danielle Rebbechi (Infrastructure Victoria)
- **Mentor:** Scott West

## Business Problem & Research Question
Understanding the impacts on businesses, parking utilization, and movement patterns when road space is reallocated is complex. We are leveraging public datasets to provide data-driven evidence of these impacts, accounting for challenges like COVID-19 behavioral shifts.

**Research Question:**
> How does parking use change with bike lanes constructed?

- **Null Hypothesis:** There has been no change in parking capacity or utilization.
- **Scope:** Metropolitan Melbourne and Regional Victoria, prioritizing protected bike lanes datasets.
- **Objective:** Understand how many people are using parking spaces before and after bike lane interventions, and the economic/social impacts of those changes.

## Stream Structure
The project is divided into four stakeholder-focused streams:
1. Cycling and public transport mode shift
2. Traffic volumes and parking (Stream B)
3. Pedestrian counts
4. Temporal patterns

**Note:** All streams must share the same foundational tech stack and methodology to avoid sprawl and ensure the final insights are cohesive.

## Tech Stack
- **Backend:** Python (FastAPI, DuckDB, pandas, geopandas, shapely, uvicorn)
- **Frontend:** React, Vite, MapLibre GL, Recharts
- **Languages:** Python, JavaScript
- **Visualization:** Custom React Dashboard
- **GIS Tools:** QGIS or ArcGIS
- **Notebooks:** JupyterLab (for data exploration)

## Architecture & Key Components

The diagram below illustrates the end-to-end architecture and key building blocks of the application, showcasing the ingestion pipeline, data storage, application serving, and orchestration layers.

```mermaid
flowchart TD
    %% Subgraphs for layering
    subgraph Client ["Client and Browser"]
        B["React Dashboard on Port 5173"]
        MC["MapContainer with MapLibre GL"]
        ID["ImpactDashboard with Recharts"]
        B --> MC
        B --> ID
    end

    subgraph AppServers ["Application Serving"]
        direction LR
        FE["Vite Dev Server"] -->|Serves Application| B
        BE["FastAPI Backend on Port 8000"] -->|REST API for GeoJSON and Metrics| MC
        BE -->|REST API for Hourly Occupancy| ID
    end

    subgraph Storage ["Data Storage"]
        DB[(DuckDB Database)]
        BE -->|Queries| DB
    end

    subgraph Orchestration ["Orchestration and Control"]
        RUN["run_app.py"] -->|Starts concurrently| FE
        RUN -->|Starts concurrently| BE
        STOP["stop_app.py"] -->|Gracefully terminates| FE
        STOP -->|Gracefully terminates| BE
        CFG{"config.yaml"} -.->|Provides Ports and Paths| RUN
        CFG -.->|Provides Ports and Paths| STOP
        CFG -.->|Provides Shared Constants| BE
        CFG -.->|Generates dotenv file| FE
    end

    subgraph DataPipeline ["Data Ingestion Pipeline (Team B)"]
        RAW[/Raw Data GeoJSON and CSV/] -->|Extracted and Transformed| ING["Python Scripts in team_b/ingestion"]
        ING -->|Loads Aggregated Data| DB
        CFG -.->|Provides Spatial Buffers and Years| ING
    end
```

## Data Sources & CRS Warning
We are using public datasets from:
- Data.vic.gov.au
- Open Data Transport Victoria (opendata.transport.vic.gov.au)
- VicRoads datasets
- Public Transport Victoria (PTV) data
- Google Maps / Street View / aerial imagery

**Important CRS Warning:**
Datasets from different sources (e.g., VicRoads vs. PTV) are unlikely to share the same spatial coordinate systems (CRS). You must define and document CRS reprojections in your notebooks/scripts. Do not assume all datasets share the same ground truth.

## Data Ingestion, Cleaning & Transformations (Stream B)
The project includes a robust, end-to-end data pipeline to ingest, clean, and transform spatial layers and transactional sensor logs into an analytical DuckDB database. Key transformations include:
- **Spatial Reprojection**: Normalizing all layers to a metric-based grid projection (`EPSG:7899`) for accurate 20m spatial buffering, then reprojecting back to `EPSG:4326` for web rendering.
- **Topology Filtering**: Stripping virtual centroid connector links from the bicycle network layer to remove visual mapping spikes.
- **Intersection Suppression**: Excluding parking bays located directly at intersections (e.g., descriptions starting with "Intersection of") to ensure block consistency.
- **Street & Block Normalization**: Unified uppercase normalization, whitespace trimming, and alphabetical sorting of cross-streets (e.g. `BETWEEN QUEEN AND ELIZABETH` unifies `BETWEEN ELIZABETH AND QUEEN`) to allow clean joins between spatial layers and sensor logs.
- **Dynamic Capacity Engine**: Calculating parking bay capacities monthly based on maximum unique broadcasting devices to avoid static count discrepancies.
- **SCATS Traffic Simulation**: Simulating 15-minute traffic flows at intersection sensors to establish baseline volumes under sandboxed execution constraints.

For a detailed breakdown of the pipelines and transformations, see the [`team_b/DATA_INGESTION.md`](file:///Users/szanevra/repositories/Victoria-Urban-Planning/team_b/DATA_INGESTION.md) documentation.

## Directory Structure

```
Victoria-Urban-Planning/
├── .github/            # GitHub configuration
├── team_a/             # Stream 1 & 3 research and notebooks
├── team_b/             # Stream 2: Traffic volumes and parking
│   ├── data/           # Data folder (gitignored)
│   │   ├── raw/        # Raw input datasets
│   │   ├── processed/  # Intermediate geojsons/parquets
│   │   └── parking_analytics.duckdb # DuckDB analytical database
│   ├── ingestion/      # Data processing and ingestion scripts
│   ├── notebooks/      # Stream 2 research and EDA notebooks
│   └── run_ingestion.py # Ingestion Orchestrator CLI runner
├── team_c/             # Stream 4 research and notebooks
├── frontend/           # React + Vite dashboard application
│   ├── src/
│   ├── package.json
│   └── ...
├── src/
│   ├── api/            # FastAPI backend application
│   └── config.py       # Centralized config loader
├── CODING_STANDARDS.md # Shared coding guidelines
├── DATA.md             # Detailed dataset inventory
├── README.md           # Project documentation and setup guide
├── config.yaml         # Configuration file for data paths and sources
├── requirements.txt    # Python baseline dependencies
├── run_app.py          # App orchestrator bootstrapper
└── stop_app.py         # App termination script
```

## Installation, Setup & Execution

### Automated Orchestration (Recommended)

The `run_app.py` script automatically bootstraps the entire application. It creates and activates the Python virtual environment, installs backend and frontend dependencies, generates the frontend `.env` file from `config.yaml`, and starts both services concurrently.

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Chameleon-company/Victoria-Urban-Planning.git
   cd Victoria-Urban-Planning
   ```

2. **Run the Orchestrator:**
   ```bash
   python run_app.py
   ```
   *Note: Ensure you have Python 3 and Node.js/npm installed locally.*

3. **Run the Data Ingestion Pipeline (First Time Only):**
   If the database file is not present, build and populate it by executing the orchestrator:
   ```bash
   python team_b/run_ingestion.py
   ```

4. **Stopping the Application:**
   To gracefully terminate both background services and free up the ports, run:
   ```bash
   python stop_app.py
   ```

---

### Manual Setup (For Development)

If you prefer to manage the services independently or execute data exploration notebooks, follow these manual steps:

#### 1. Backend Setup & Execution
```bash
# Create the Virtual Environment
python3 -m venv .venv

# Activate the Virtual Environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt

# Run Ingestion Pipeline
python team_b/run_ingestion.py

# Start the Backend API
uvicorn src.api.main:app --reload
```
The API will be running at `http://localhost:8000`. You can view the interactive documentation at `http://localhost:8000/docs`.

#### 2. Frontend Setup & Execution
```bash
cd frontend
npm install
npm run dev
```
The dashboard will be running at `http://localhost:5173`. 

*Note: Make sure to copy the `ports` and `historical` values from `config.yaml` into a `frontend/.env` file if running manually.*

#### 3. Launch JupyterLab
If you want to run the data exploration notebooks, activate your virtual environment and run:
```bash
source .venv/bin/activate
jupyter lab
```

## Git Workflow & Collaboration Guide

### Rules
1. Never commit directly to the `main` branch.
2. Use the Branch Naming Convention.
3. PRs with merge conflicts will not be approved or merged. You are responsible for resolving conflicts locally.

### Branch Naming Convention
Branches must use the following format:
- `feature/<your-initials>/<description>`
- `bugfix/<your-initials>/<description>`

Examples:
- `feature/sz/add-traffic-pipeline`
- `bugfix/sz/fix-crs-reprojection`

### Step-by-Step Workflow

**1. Start Fresh**
Always create your branch from the latest `main`:
```bash
git checkout main
git pull origin main
git checkout -b feature/<your-initials>/<description>
```

**2. Work and Commit**
Make your changes, then add and commit with a clear message:
```bash
git add .
git commit -m "Add traffic volume parsing for Metro Melbourne"
```

**3. Rebase Against `main`**
Before pushing, you must rebase on top of the latest `main` to pull in changes and resolve conflicts locally:
```bash
git fetch origin
git rebase origin/main
```
If there are merge conflicts, Git will pause. Open the files, fix the issues, and run:
```bash
git add <fixed-files>
git rebase --continue
```

**4. Push and Open a PR**
Push your branch and open a PR on GitHub:
```bash
git push -u origin <your-branch-name>
```
*(If you already pushed before rebasing, use `git push --force-with-lease origin <your-branch-name>`)*

**5. Review and Merge**
Assign reviewers from your stream. Once approved, the PR can be merged.

## Coding Standards
All contributors are expected to follow our shared coding standards covering PEP 8, Tidyverse, docstrings, and security. Please read the full [Coding Standards & Best Practices Guide](CODING_STANDARDS.md) before writing code.
