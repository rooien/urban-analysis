# Stream C: COVID-19 Parking Dynamics & Spatial Intervention Analysis

This directory contains Jupyter notebooks developed by **Team C** for the **Victoria Urban Planning — SIT Capstone Project** in partnership with **Infrastructure Victoria**.

---

## Notebook Catalog

| Notebook | Purpose | Key Outputs / Figures |
|---|---|---|
| [`StreetComparison.ipynb`](StreetComparison.ipynb) | Evaluates on-street parking behavior across **four COVID-19 eras** for three key corridors (Albert St, Southbank Blvd, Elizabeth St), triangulating sensor metrics with **Google Mobility**, **BOM Weather**, and **VicRoads Arterial Traffic**. | `fig1_daily_events_timeseries.png`<br>`fig2_metrics_comparison.png`<br>`fig3_heatmaps.png`<br>`fig5_mobility_policy_triangulation.png`<br>`fig6_weather_correlation.png`<br>`fig7_traffic_divergence.png`<br>`street_covid_comparison.csv` |
| [`DataCollector.ipynb`](DataCollector.ipynb) | Ingests real-time IoT bay status from the City of Melbourne Live Parking API, extracts coordinates, and executes spatial nearest-neighbor joining (`sjoin_nearest`) against road network centerlines. | `fig4_postcovid_occupancy.png`<br>`live_harvester_august_2026.csv` |
| [`StreetData.ipynb`](StreetData.ipynb) | Implements a **Difference-in-Differences (DiD)** quasi-experimental framework across 315 Inner Melbourne fringe street segments (55 treatment vs 99 control segments) to isolate streetscape reallocation effects. | `street_data_output.txt`<br>Baseline DiD turnover and duration metrics |

---

## COVID-19 Study Eras

The analysis formalizes four distinct regulatory and operational periods:

| Era Tag | Period | Regulatory / Operational Context |
|---|---|---|
| `1_Pre-COVID` | Jan 1, 2019 – Dec 31, 2019 | Normal pre-pandemic baseline activity and standard economic turnover |
| `2_Pre-Lockdown` | Jan 1, 2020 – Mar 22, 2020 | Global pandemic emergence; State of Emergency declared March 16 |
| `3_Lockdown` | Mar 23, 2020 – May 31, 2020 | Victorian Stage 3 Stay-at-Home orders (4 permitted reasons to leave home) |
| `4_Post-COVID` | August 2026 | Modern post-intervention recovery & live bay occupancy monitoring |

---

## Spatial Standards & CRS Notice

* **Standard Project CRS:** `EPSG:7899` (**GDA2020 / VicGrid**).
* **Reprojection:** Point sensor coordinates (`EPSG:4326` WGS84) and municipal shapefiles must be reprojected to `EPSG:7899` before buffering or spatial joins to prevent geometric distortion and ensure accurate distance calculations.

---

## Required Raw Datasets (`data/raw/`)

Before executing the notebooks, ensure the following datasets are present in `data/raw/`:

```
data/raw/
├── On-street_Car_Parking_Sensor_Data_-_2019.csv              # ~42.7M baseline parking events
├── On-street_Car_Parking_Sensor_Data_-_2020__Jan_-_May_.csv  # ~14.2M lockdown parking events
├── live_harvester_august_2026.csv                            # Live API sensor readings
├── streets_spatial.gpkg                                      # Street segment geometry & interventions
├── road_segments_15dec.shp                                   # Base road network shapefile
├── google_mobility_victoria_2020.csv                         # Google Community Mobility Reports
├── melbourne_weather_2019_2020.csv                           # Daily rainfall & temperature (BOM/Open-Meteo)
├── vicroads_traffic_proxy_2019_2020.csv                      # SCATS arterial volume proxy
└── victoria_covid_restrictions_timeline.csv                  # Official restriction milestone dates
```

*(Note: Raw data files are excluded from Git tracking via `.gitignore` due to large file sizes).*
*(Note: you can replace live_harvester_august_2026.csv with a new dataset that you harvest using the DataCollector.ipynb Notebook).*
---

## Findings Summary

1. **Policy Impact:** On-street parking demand collapsed by **60% to 80%** precisely aligned with Victorian Stage 3 Stay-at-Home orders, strongly tracking Google Workplace and Retail Mobility indices ($r = 0.68 - 0.75$).
2. **Duration Surge & Turnover Collapse:** During lockdowns, average parking duration more than doubled on Albert St (47 min $\rightarrow$ 98 min) and Southbank Blvd (16 min $\rightarrow$ 42 min) as kerbsides shifted to essential/residential stays.
3. **Thoroughfare vs. Destination Divergence:** Elizabeth Street sustained high arterial through-traffic (~75% of baseline) despite local parking reductions, confirming its function as a transit/movement spine.
4. **Weather Independence:** Regression against rainfall and temperature showed near-zero correlation ($r \approx 0$), proving environmental factors do not govern parking demand trends.
5. **Modern Kerbside Capacity:** 2026 live telemetry shows ~18% occupancy on Albert Street, confirming available kerbside space for active transport reallocation.

---

## Execution Instructions

1. Activate your virtual environment:
   ```bash
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   ```
2. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch JupyterLab:
   ```bash
   jupyter lab
   ```
4. Run `DataCollector.ipynb` first (to test live API spatial joining), then execute `StreetComparison.ipynb` to reproduce all figures and export statistical tables into `data/processed/`.
