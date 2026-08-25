# USIA — Data Audit & Method Notes

Prepared 4 August 2026. Covers the two assigned tasks: (1) sensor EDA for baseline
and post-intervention parking utilisation, (2) bike lane / parking buffer overlap.

---

## 1. Findings that change the plan

### 1.1 The sensor strand supports before/after on 11 segments, not 96

The City of Melbourne archive covers **Jan 2011 – May 2020**. Sensors were
decommissioned after that; there is no post-2020 data at any price.

Of the 315 study segments, 39 are CBD and 16 of those are treatment segments.
Cross-referencing intervention dates against the sensor window:

| Street | Segments | Intervention | Sensor coverage |
|---|---|---|---|
| La Trobe Street | 7 | Jan 2013 (FY12-13 Q3) | 2 yrs pre, 7 yrs post — **usable** |
| William Street | 4 | Apr 2017 (FY16-17 Q4) | 6 yrs pre, 3 yrs post — **usable, best case** |
| Peel Street | 2 | Jul 2020 | baseline only — intervention post-dates the archive |
| Exhibition Street | 2 | Oct 2020 | baseline only — intervention post-dates the archive |
| La Trobe Street (seg 3830) | 1 | *no record* | unusable |

**Implication.** Frame the sensor work as a *deep, high-confidence case study on
two corridors*, triangulated against 23 CBD control segments (Queen, Collins,
Russell, Spencer, Lonsdale, Bourke). Do not frame it as the primary evidence base —
that is the imagery strand. Peel and Exhibition still have value as **pre-intervention
baselines** whose post period comes from Nearmap; that is a genuine methodological
contribution, not a gap.

**William Street is the flagship analysis.** Apr 2017 sits clear of COVID, has
six years of pre-period and three years of post-period, and the intervention is a
protected bike lane — exactly IV's core question.

### 1.2 COVID barely matters for this strand

The archive ends May 2020, roughly ten weeks after Victoria's first restrictions
(16 Mar 2020). Rather than modelling the COVID period, the defensible choice is to
**truncate the series at 29 Feb 2020** and state that the 2020 tail is excluded as
a structural break with insufficient post-period to model. This is simpler than any
adjustment and easier to defend to IV.

### 1.3 CRS is not uniform — one file is in a different projection

| File | CRS | Note |
|---|---|---|
| `streets_spatial.gpkg` | EPSG:7899 (GDA2020 / Vicgrid) | analysis CRS |
| `street_spatial_study_area.gpkg` | EPSG:7899 | also throws a benign GPKG `user_version` warning |
| `road_segments_15dec.shp` | **EPSG:7855** (GDA2020 / MGA zone 55) | must be reprojected before any join |

Earlier project notes recorded all three as 7899. That is incorrect. Anything
joining `road_segments_15dec.shp` without `.to_crs(7899)` will silently produce
wrong distances.

### 1.4 `street_spatial_study_area.gpkg` is a 250 m catchment, not a kerb buffer

Implied buffer half-width is ~250 m (median). This is the surrounding-street
catchment for IV's "nice to have" extension, not a kerbside buffer. Kerb-scale
buffers (5 m direct, 20 m adjacent) are generated fresh from the centrelines in
`03_bikelane_parking_overlap.py`.

It also holds **316** features against the streets layer's **315** — segment
`3500` exists in the buffer file but not in the street list. Query with IV.

### 1.5 The `street_segment_id` join, resolved

Three different storage types across four files:

| File | Type | Example |
|---|---|---|
| `streets_spatial.gpkg` | float64 | `211.0` |
| `street_spatial_study_area.gpkg` | object | `'123'` |
| `street_segment_qtr_attributes.csv` | int | `12016` |
| `sites_db.csv` | object | `'11903'` |

Canonical form used everywhere: `pd.to_numeric(s).astype("Int64").astype(str)`.
Casting straight to `str` from float yields `'211.0'` and silently matches nothing.

### 1.6 `sites_db.csv` is cp1252, not UTF-8

`pd.read_csv(..., encoding="cp1252")`. Reading as UTF-8 raises at byte 10590.

### 1.7 `QUARTER` is a financial year code

`"1819Q1"` = FY2018-19 Q1 = **Jul–Sep 2018**, not calendar 2018 Q1.
`"9900Q2"` = Oct 1999 (two-digit year rolls at 90). Reading these as calendar
quarters shifts every intervention date by up to six months and puts the earliest
records in 2099.

### 1.8 Eleven treatment segments have no intervention date

`990, 1446, 1903, 1970, 3100, 3125, 3830, 5634, 5635, 5640, 10916` — 11 of 96.
These need to go to IV as a single consolidated query. Segment `3830` is a
La Trobe Street segment sitting between segments that all have Jan 2013 dates,
so it is very likely a data entry omission rather than a genuinely untreated street.

---

## 2. Calibrated kerb capacity (result, not plan)

Running the Grattan Appendix D conversion across all 315 segments:

- Total centreline: **98.9 km**; total kerb (both sides): **197.8 km**
- Mean segment length 314 m, median 235 m
- Raw geometric capacity at 6.0 m per parallel space: ~33,000 spaces
- **Obstruction factor: 0.418** (median of IV's reported capacity ÷ geometric capacity, n=270)
- Calibrated estimate: **~15,155 spaces**

The obstruction factor is the useful output here. Grattan assume an obscured-visibility
adjustment; this project can *empirically calibrate* it against IV's own consultant
counts on 270 segments. Only 42% of raw kerb length is actually parkable once
driveways, hydrants, clearways and loading zones are removed. That is a defensible,
project-specific number and worth reporting to IV as a standalone finding.

**Caveats on the factor.** The distribution is wide (IQR 0.27–0.53, mean 0.43 vs
median 0.42), so a single global factor is a first pass, not a final method. Two
improvements worth making before this goes to IV:

1. Fit the factor separately by location type (CBD / Metro / Regional) and parking
   format — CBD kerbs have far more clearway and loading-zone loss than regional ones.
2. Four segments return a factor above 1.0 (reported capacity exceeds raw geometric
   capacity). Those are either angled parking mis-coded as parallel, or the reported
   figure includes bays on adjoining side streets. Inspect them individually before
   including them in the calibration.

### 2.1 External validation of the quarter decoding

The financial-year decode was checked against Melbourne's known bike lane build
history, and it reconstructs it correctly:

| Segment | Decoded date | Real-world event |
|---|---|---|
| Peel St | Jul 2020 | COVID pop-up protected lane program |
| Exhibition St | Oct 2020 | COVID pop-up protected lane program |
| William St | Apr 2017 | separated lane construction |
| La Trobe St | Jan 2013 | staged separated lane rollout |

A calendar-quarter reading would have placed the pop-up lanes in early 2020 and
2021 respectively, both wrong. This is good evidence the decode is right.

---

## 2.5 The control group cannot serve as a capacity counterfactual

The quarterly panel carries `StreetInScopeOnStreetParkingCap` for every segment in
every quarter, which looks like a free before/after measure of parking supply — no
sensors or imagery needed. It isn't.

A placebo test settles it. Assigning each control segment a random pseudo-intervention
date drawn from the real treatment dates and applying the identical pre/post
comparison:

| Group | n | Segments whose capacity *ever* changes | Median Δ | Mean Δ | Share losing |
|---|---|---|---|---|---|
| Control | 204 | **1.5%** | 0.0 | 0.00 | 0.0% |
| Treatment (all) | 85 | **91.8%** | 0.0 | −3.9 | 42.4% |
| Protected bike lane only | 69 | — | 0.0 | −3.9 | 43.5% |

Control capacity is frozen: 3 of 204 segments show any change across 105 quarters
(≈26 years). Real streets do not behave that way — permit zones, clearway extensions
and redevelopment change kerb supply constantly. The overwhelmingly likely explanation
is that **IV re-survey capacity only when a site is treated**, so the field records
intervention events rather than the state of the world.

Consequences:

1. The treatment−control difference in this field is an artefact of data maintenance,
   not an effect estimate. Do not report it as one.
2. The treatment-side numbers may still be real, since they come from actual re-survey.
   Read as within-treatment descriptives, they say: **43% of protected bike lane
   segments lost recorded parking, 54% were unchanged, mean −3.9 spaces, total −330
   spaces** across all treatment segments. Pedestrianisation is far more severe
   (median −75%, n=6).
3. This is *why* the imagery strand is load-bearing. Nearmap is the only source that
   observes treatment and control on the same basis. That reframes it from "the
   laborious manual option" to "the only internally valid one" — worth stating
   plainly to IV and in the mentor update.

Also note the earlier treatment/control gap in the obstruction factor (0.28 vs 0.46,
and it survives stratification by location type) is the same artefact viewed from a
different angle, not a finding about street design.

---

## 3. Data still to obtain

| Dataset | Source | Purpose |
|---|---|---|
| On-street Parking Bays (geometry) | CoM portal, API export | join sensors to segments |
| On-street Parking Bay Sensors | CoM portal, API export | current snapshot; `marker_id` join key |
| On-street Car Park Bay Restrictions | CoM portal, API export | `bay_id` join; restriction context |
| Parking event archives 2011–2020 | S3 zips, ~9 GB total | the actual utilisation data |
| Bicycle Infrastructure Network | data.vic | protected bike lane geometry for Task 2 |

Suggested download order — **2016, 2017, 2018, 2019 first** (~3.9 GB). Those four
years alone deliver the William Street before/after. Add 2012–2014 later for
La Trobe. 2011 and 2020 are optional.

### Event data caveats (from CoM's own metadata)

- Rows with **negative duration** where arrival is logged after departure — drop them.
- Rows where arrival/departure were not recorded are back-filled to midnight —
  these inflate long-stay counts; cap durations at 24 h.
- `Sign` values ending in `OLD` (342k rows in 2016, 453k in 2015) indicate the
  restriction changed or the sensor was replaced after the event. Fine for
  occupancy, unreliable for restriction-type analysis.
- Events spanning a year boundary are truncated at midnight 31 Dec.

---

## 4. Method: events are not snapshots

Each archive row is one parking event, not one observation of a bay. Utilisation
cannot be a row count.

```
utilisation(bay, hour) = occupied_minutes_in_hour / 60
utilisation(segment, hour) = Σ occupied_minutes / (n_bays × 60)
```

Events are exploded across the hours they span, then aggregated to
segment × date × hour, split weekday/weekend, and restricted to 08:00–18:00
for the headline pre/post comparison.

**Watch `n_bays`.** If a bike lane removed parking bays, sensor count drops after
the intervention. Utilisation is then a ratio over a shrinking denominator and can
*rise* while absolute parked vehicles *fall*. Report both `utilisation` and
`n_bays`, and the change in each. This is likely the single most policy-relevant
result for IV: whether reallocation reduced supply, reduced demand, or neither.

---

## 5. Pipeline

```
analysis/
├── config.py                         paths, CRS, constants
├── src/
│   ├── 00_download_com_data.py       fetch CoM reference layers + event archives
│   ├── 01_build_intervention_dates.py  ✅ run — authoritative dates + usability flags
│   ├── 02_sensor_utilisation.py      events → hourly occupancy → pre/post
│   └── 03_bikelane_parking_overlap.py  ✅ partially run — kerb capacity done
├── data/{raw,interim,processed}/
├── outputs/
└── docs/data_audit.md
```

Run order:

```bash
python analysis/src/01_build_intervention_dates.py
python analysis/src/00_download_com_data.py --reference
python analysis/src/00_download_com_data.py --years 2016 2017 2018 2019
python analysis/src/02_sensor_utilisation.py --years 2016 2017 2018 2019
python analysis/src/03_bikelane_parking_overlap.py --bin data/raw/<bin>.geojson
```
