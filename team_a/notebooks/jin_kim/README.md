# Cycling Site Matching and Intervention Validation

This folder contains the Cycling Group site-matching and intervention validation work for Team A.

## Workflow

1. `00_GPS_site_matching.ipynb`
   - Validates GPS distance between cycling counters and treatment street segments.
   - Confirms Wellington counter 32493 is closest to segment 5881.

2. `01_full_site_matching.py`
   - Matches all cycling counters to the nearest treatment street segments.
   - Uses a 12 m distance threshold.
   - Identifies the main candidate cycling sites.

3. `02_confirmed_matches.csv`
   - Stores the confirmed counter-to-segment matches.

4. `03_intervention_history.csv`
   - Stores intervention history for the matched street segments.

5. `04_intervention_data_quality_check.py`
   - Applies the PO-recommended forward-fill and backward-fill method.
   - Checks intervention timing and data-quality issues.
   - Reviews duplicate/conflicting quarter records.
   - Cross-checks completion quarters against `sites_db`.

6. `05_Sprint1_cycling_site_analysis.pdf`
   - Summarises Sprint 1 findings, candidate sites and data limitations.

## Reference Data

- `ref_bike_site_listing.csv` — cycling counter locations and GPS coordinates
- `ref_sites_db.csv` — intervention history by street segment
- `ref_streets_spatial.xlsx` — treatment/control street segments and geometry
- `ref_street_segment_qtr_attributes.csv` — quarterly intervention attributes

## Main Findings

The site-matching process identified four candidate streets:

- Wellington Street
- Moorabool Street
- Heidelberg Road
- Albert Street

Albert Street was the most suitable site for a preliminary before-and-after cycling analysis.

Wellington counter 32493 was confirmed as matching segment 5881. The relevant protected-bike-lane intervention occurred in 2015, while the later 2019 record for segment 5881 represents a post-intervention observation rather than a new intervention.

The intervention data-quality check also confirmed that none of the five matched cycling segments had conflicting duplicate-quarter records. Where multiple `Baseline == 0` quarters existed, the intervention summary and `sites_db` dates were used to identify the relevant intervention period.
