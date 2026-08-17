# Victoria Urban Planning - Dataset Inventory
**Stream 2: Traffic Volumes & Parking**

This document identifies the datasets required to address the gaps outlined in the readme, enabling a comprehensive before/after analysis of streetscape interventions (specifically bike lanes) across all target LGAs (Yarra, Port Phillip, Merri-bek, Maribyrnong, Greater Dandenong, and Greater Geelong).

### Process Undertaken
To identify and compile these datasets, the following steps were taken:
- Reviewed the initial scope and dataset gaps regarding spatial coverage and historical time series.
- Clarified research parameters with stakeholders, confirming a maximum available historical timeframe (with a post-COVID focus) and the strict constraint that all data must be free and publicly available.
- Explored Victorian open data portals including DataVic, Open Data Transport Victoria, Geelong Data Exchange, and local council platforms (Yarra, Port Phillip, Merri-bek, and Maribyrnong).
- Identified datasets matching the required spatial coverage (Statewide or Metro Melbourne) and temporal coverage (2015 to present).
- Developed a proxy methodology leveraging free high-resolution aerial imagery to bypass the lack of historical in-ground parking sensors in non-CoM LGAs.
- Documented restricted datasets (Nearmap, Consultant data) for completeness, while ensuring robust and independent free alternatives were prioritized.

## 1. Free & Public Dataset Inventory

All datasets in this section are free and publicly available for educational and research purposes, strictly adhering to the project constraints.

### Bike Lane Interventions (Spatial & Temporal)

| Dataset Name | Source / Portal | Spatial Coverage | Temporal Coverage | Metrics / Data Fields | CRS | Gaps Addressed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bicycle Infrastructure Network (BIN)** | [Transport Victoria](https://opendata.transport.vic.gov.au/) | Statewide (Includes all target LGAs & Geelong) | Current snapshot (regularly updated) | Existing cycling infrastructure, path types, spatial layout. | GDA2020 / VICGRID94 | Maps the bike lanes across all missing LGAs. |
| **Pop-up Bike Lanes Dataset** | [DataVic](https://discover.data.vic.gov.au/) | Metropolitan Melbourne | 2020 - Present | Bike lane locations and **Installation Dates**. | Web Mercator / GDA2020 | Solves the critical need for "before/after" construction dates, especially for COVID-era rollouts. |
| **Strategic Cycling Corridors (SCC)** | [DataVic](https://discover.data.vic.gov.au/) | Statewide | Planning layer | High-priority routes and planning corridors. | GDA2020 | Useful for identifying future or high-priority intervention areas. |

### Traffic Volumes & Active Transport

| Dataset Name | Source / Portal | Spatial Coverage | Temporal Coverage | Metrics / Data Fields | CRS | Gaps Addressed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SCATS Traffic Signal Volume Data** | [DataVic](https://discover.data.vic.gov.au/) | Statewide (All signalized intersections) | 2014 - Present (15-min intervals) | Traffic volumes, degree of saturation, intersection turning movements. | GDA2020 (Spatial layer) | Provides historical traffic volumes and congestion metrics across ALL missing LGAs. |
| **Telemetry & TIRTL Traffic Counts** | [Transport Victoria](https://opendata.transport.vic.gov.au/) | Strategic Roads (Statewide) | Real-time & Daily historical | Volumes, speeds, vehicle classifications (cars vs heavy vehicles). | GDA2020 | Provides speed and vehicle classification metrics. |
| **Bicycle Volume and Speed** | [Transport Victoria](https://opendata.transport.vic.gov.au/) | 50+ permanent counters (Metro Melbourne) | Real-time & Historical | Bike volumes and speeds. | GDA2020 | Measures active transport usage to see if bike lanes led to modal shift. |
| **Historical AADT Volume** | [Transport Victoria](https://opendata.transport.vic.gov.au/) | Strategic Roads (Statewide) | 2001 - 2019 (Annual averages) | Annual Average Daily Traffic (AADT). | GDA2020 | Excellent for long-term historical baseline comparison prior to 2020. |

### Parking Utilization & Proxies

| Dataset Name | Source / Portal | Spatial Coverage | Temporal Coverage | Metrics / Data Fields | CRS | Gaps Addressed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Vicmap Aerial (Statewide) Imagery** | [DataVic](https://discover.data.vic.gov.au/) / MapShareVic | Statewide | 2015 - Present (Periodic captures) | High-resolution aerial photography mosaics (WMS/WMTS/Download). | GDA2020 / Web Mercator | Acts as the primary proxy for historical parking utilization in non-CoM LGAs (see Methodology below). |
| **Off-Street Parking (Congestion Levy)** | [DataVic](https://discover.data.vic.gov.au/) | Metropolitan Melbourne | Current | Spatial layout of off-street parking facilities. | GDA2020 | Identifies off-street parking capacity that might absorb displaced on-street parking. |
| **On-Street Parking Sensors (Historical)** | [City of Melbourne](https://data.melbourne.vic.gov.au/) | Melbourne CBD & Surrounds (CoM LGA only) | 2015 - Present | Occupancy, stay duration. | Web Mercator | Included for completeness; partial source for CBD-adjacent sites. |
| **Geelong Real-Time Parking Occupancy** | [Geelong Data Exchange](https://www.geelongdataexchange.com.au/) | Central Geelong | Real-time & Recent Historical | IoT parking sensor occupancy. | GDA2020 | Fills the parking gap specifically for the Geelong LGA. |

### Economic & Social Impact Proxies

| Dataset Name | Source / Portal | Spatial Coverage | Temporal Coverage | Metrics / Data Fields | CRS | Gaps Addressed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **VISTA (Victorian Integrated Survey of Travel and Activity)** | [Transport Victoria](https://opendata.transport.vic.gov.au/) | Greater Melbourne & Geelong | Multi-year periodic surveys | Travel mode shifts, trip purpose, business/shopping trip frequency. | Non-spatial (Tabular) | Addresses social impacts, behavioral shifts, and modal shifts. |
| **Local Council Pedestrian & Spend Portals** | Yarra, Port Phillip, Merri-bek, Maribyrnong, Geelong Open Data | Respective LGAs | Varied (typically 2018-Present) | Pedestrian footfall counts, local economic indicators, business precinct activity. | Varied | Directly addresses the economic and business impact objectives outlined in the [README.md](README.md). |

---

## 2. Commercial / Restricted Datasets

The following datasets were identified as highly relevant (and mentioned in [scratchpad.txt](scratchpad.txt)) but are **Commercial or Restricted**. They are documented here for completeness and to justify the free alternatives leveraged above.

### A. Nearmap Aerial Imagery
- **Status**: Commercial / Paid Subscription.
- **Value**: Extremely high resolution and frequent (monthly/quarterly) captures, perfect for tracking parked cars over time.
- **Free Alternative**: **Vicmap Aerial Imagery + Google Earth Historical Imagery** (see Methodology below). While capture frequency is lower, it is sufficient for establishing seasonal or annual pre/post baselines.

### B. Consultant Pre/Post Dataset
- **Status**: Restricted (Must be procured or requested via Infrastructure Victoria).
- **Value**: Likely contains high-frequency parking occupancy and turning counts specifically tailored to the intervention sites.
- **Free Alternative**: **SCATS Intersection Volume Data + Pop-up Bike Lanes (Installation Dates) + Imagery AI Counting**. Combining these provides a robust, independent proxy dataset.

---

## 3. Free Aerial Imagery Proxy Methodology (Parking Utilization)

Since historical in-ground parking sensors are largely unavailable outside the City of Melbourne, we will use a Remote Sensing / Computer Vision approach to estimate historical parking utilization.

### Objective
Calculate parking occupancy rates along intervention corridors "before" and "after" bike lane construction.

### Data Sources
- **Intervention Dates**: `Pop-up Bike Lanes Dataset` or Council capital works records.
- **Imagery**: `Vicmap Aerial Imagery` or free Google Earth Historical Imagery.

### High-Level Workflow
1. **Site Selection**: Buffer the spatial lines of bike lanes by ~20 meters to capture on-street parking bays.
2. **Date Matching**: For each site, identify the construction date ($T_c$). Select the closest available high-res aerial images for "Before" ($T_c - 6 \text{ months}$) and "After" ($T_c + 6 \text{ months}$).
3. **Capacity Baseline**: Manually or via vector layers map the total number of marked parking bays along the corridor to establish `Total Capacity`.
4. **Vehicle Counting (Computer Vision or Sampling)**:
    - **Option A (Automated)**: Deploy a pre-trained Object Detection model (e.g., YOLOv8, Detectron2) fine-tuned on aerial vehicle datasets (like DOTA or cowc) to detect and count parked cars in the buffered zones.
    - **Option B (Manual Sampling)**: Since the number of pilot sites is limited (as per street list), conduct manual counts of parked cars in the "before" and "after" images to ensure 100% accuracy.
5. **Metric Calculation**:
   $$\text{Parking Utilization Rate} = \frac{\text{Counted Parked Cars}}{\text{Total Parking Capacity}} \times 100$$
6. **Comparison**: Assess if parking utilization significantly increased, decreased, or remained stable, accounting for any reduction in total capacity due to the bike lane.
