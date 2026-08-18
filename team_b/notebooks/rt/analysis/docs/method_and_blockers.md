# Sensor Utilisation — Method and Blockers

**Task:** EDA on historical City of Melbourne parking sensor records to evaluate
baseline and post-intervention parking utilisation.

**Status as at 4 August 2026:** block-level before/after produced for William Street.
Not yet attributable — control comparison and segment crosswalk outstanding.

---

## 1. Data acquisition

Source: City of Melbourne open data portal, `On-street Car Parking Sensor Data`,
published as one dataset per calendar year.

- **Coverage:** 1 Jan 2011 – 31 May 2020. Sensors were decommissioned after May 2020;
  no later data exists at any price.
- **Volume:** 363.6 million rows across ten files, ~52 GB uncompressed.
- **Held locally:** 2011–2018 and 2020 (Jan–May). **2019 outstanding.**
- **Granularity:** one row per parking event (a vehicle arriving and later departing
  one sensored bay), not a periodic snapshot.

Files are stored outside the git repository and referenced by path. Committing them
is neither possible nor desirable at this size.

### Verification of completeness

2017 was reconciled against the publisher's stated row count: monthly event totals
summed to **35,908,877** against a published 35.9 million. No rows were lost during
parsing.

---

## 2. Why DuckDB rather than pandas

A single year is 5–8 GB and up to 52 million rows. `pandas.read_csv` loads the whole
file into memory and would exhaust a laptop on one year, let alone nine.

The conventional workaround is chunked reading with manual filtering, which is what
the original pipeline script does. DuckDB was adopted instead because:

1. **It queries CSV on disk without loading it.** Aggregations stream; memory stays flat.
2. **It handles all years in one statement** via filename wildcards, with
   `union_by_name` to tolerate differing column sets.
3. **It reduces before it materialises.** The 150,000-row hourly result comes back as a
   pandas DataFrame; the 35 million source rows never enter Python.
4. **It is already the team standard** — declared in `requirements.txt`, used by
   `src/ingestion`, and `config.yaml` names `data/parking_analytics.duckdb`.

Analysis is therefore split: DuckDB performs scanning, filtering and aggregation;
pandas performs the small-data statistics and plotting.

---

## 3. Identifying street blocks

### Why the intended spatial join failed

The original design was to join sensor events to the 315 study segments through bay
geometry, using `marker_id` as the key. This is not possible: the published
`on-street-parking-bays` file contains `RoadSegmentID`, `KerbsideID`, latitude and
longitude, but **no `StreetMarker`**. There is no key linking bay geometry to the
historical event records.

### Method adopted instead

Every event row carries `StreetName`, `BetweenStreet1`, `BetweenStreet2` and a
side-of-street indicator. The pair of cross streets identifies a city block directly,
without geometry.

Blocks are therefore the unit of analysis. Mapping blocks to Infrastructure Victoria's
`street_segment_id` values is a separate manual step (see Blockers).

This has an advantage over the spatial approach: a text crosswalk is human-inspectable
and reviewable, whereas the output of a nearest-neighbour spatial join with an
arbitrary snapping distance is not.

### Name normalisation

Cross-street names are abbreviated inconsistently between years — `Lt BOURKE STREET`
in 2016, `LITTLE BOURKE STREET` in 2018. Unnormalised, the same block appears as two
distinct rows, each with data on only one side of the intervention. Names are
uppercased and `Lt ` expanded to `LITTLE ` before grouping.

---

## 4. Converting events to occupancy

### The core problem

Utilisation cannot be derived from a row count. A busy hour and a quiet hour may
contain identical numbers of events — a single all-day parker generates one row, while
ten quick shoppers generate ten.

Further, a single event spans multiple clock hours. A vehicle arriving 09:40 and
departing 12:15 contributes to four separate hours in unequal amounts.

### Hour-splitting

Each event is expanded into one record per hour it overlaps, using
`generate_series` to enumerate the hours and `unnest` to expand them into rows. Minutes
occupied within each hour are obtained by clipping the event to the hour boundaries:

    occupied_minutes(hour) = min(departure, hour_end) − max(arrival, hour_start)

Worked example, 09:40 → 12:15:

| Hour | Minutes |
|---|---|
| 09:00 | 20 |
| 10:00 | 60 |
| 11:00 | 60 |
| 12:00 | 15 |

Total 155 minutes, equal to the original 2 h 35 m duration. This identity is the check
that the splitting is correct.

### Occupied versus available

The archive records **both** occupied and vacant intervals; the `Vehicle Present`
boolean distinguishes them. Utilisation is therefore:

    utilisation(block, hour) = Σ minutes where present / Σ all minutes

This is preferable to dividing by `bays × 60`, because a bay only appears in the data
when it generates an event — so a bay-count denominator silently excludes bays that
were vacant, which biases utilisation upward.

### Schema drift

Column names are not stable across the series. The break occurs at 2018:

| 2011–2017 | 2018 onward |
|---|---|
| `Vehicle Present` | `VehiclePresent` |
| `In Violation` | `InViolation` |
| `Side Of Street` | `SideOfStreet` |
| `DurationSeconds` | `DurationMinutes` |

2018 additionally introduces `BetweenStreet1ID`, `BetweenStreet2ID`, `BayId`,
`SignPlateID`, `AreaName` and `SideName`.

The rename of `DurationSeconds` to `DurationMinutes` is a **silent unit change** — the
column name changes but nothing errors, and any cross-year use of that field without
inspection would be wrong by a factor of 60. Duration is therefore recomputed from the
timestamps rather than read from the published column.

Column names are detected per file at runtime and the query adapted accordingly.

---

## 5. Date parsing

Timestamps are formatted `MM/DD/YYYY hh:mm:ss AM/PM` — **month first**, despite being
Australian council data. Confirmed three ways:

1. In a 400,000-row sample, the first component never exceeds 12 while the second
   reaches 31.
2. DuckDB's format sniffer parses the column cleanly; a day-first interpretation would
   fail on any date after the 12th of a month.
3. All 35.9 M rows of 2017 reconcile after parsing, with all twelve months present and
   plausibly distributed (per-day rates lowest in January, consistent with the
   Melbourne summer holiday period).

A day-first reading would silently relocate roughly two-thirds of all events.

---

## 6. Data cleaning

Applied exclusions, all corresponding to issues documented by the publisher:

| Rule | Rationale |
|---|---|
| `DepartureTime > ArrivalTime` | CoM document records where a sensor logged arrival after departure, producing negative durations |
| Duration < 24 hours | Where a timestamp was not recorded, CoM back-fill to midnight, fabricating implausibly long stays |
| `avail_min > 0` retained | Genuinely empty hours are real low-utilisation observations; dropping them would bias averages upward |

`Sign` values ending in `OLD` (342,475 rows in 2016; 453,178 in 2015) indicate the
restriction changed or the sensor was replaced after the event. These remain valid for
occupancy but are unreliable for restriction-type analysis.

---

## 7. Before/after design

- **Treatment:** William Street, protected bike lane, April 2017.
- **Windows:** 12 months either side of the intervention date. A full year each way
  ensures seasonal variation cancels rather than confounds.
- **Exclusion:** the first 30 days after the intervention date are dropped, so
  construction disruption is not counted as the post-intervention state.
- **Hours:** weekdays only, 08:00–18:00. Overnight hours are near-empty and would drag
  all averages toward zero, diluting differences in the periods that matter.
- **Bay counts reported alongside utilisation** at all times (see below).

### Why bay counts must accompany utilisation

Utilisation is a ratio, and a street reallocation can change its denominator.

| Bays | Utilisation | Interpretation |
|---|---|---|
| ↓ | ↑ | Supply reduced; same demand over fewer spaces. **Not** increased parking |
| — | ↓ | Supply unchanged; genuinely reduced demand |
| — | — | No measurable parking effect |

Reporting a utilisation increase without noting bay removal would invert the policy
conclusion.

---

## 8. Result to date

William Street, 11 sensored blocks, 2016 versus 2018:

- Utilisation rose on 10 of 11 blocks, range 0.36–0.74
- Bays fell on 3 blocks, rose on 4, unchanged on 4; net +8
- **Every block that lost bays saw utilisation rise** — consistent with reallocation
- One outlier: Little Collins–Collins, −17.0 pp with no bay change

**This is not yet attributable to the bike lane.** Utilisation also rose on blocks with
unchanged or increased bay counts, indicating a general upward drift. Separating
intervention effect from city-wide trend requires the control comparison.

---

## 9. Blockers

### 9.1 Block-to-segment crosswalk — critical path

Eleven sensored blocks exist on William Street; Infrastructure Victoria lists **four**
treatment segments there. The analysis currently describes "William Street", not "the
treated segments", and some blocks likely fall outside the intervention extent.

Resolution: manual mapping in QGIS — load the study segments over a basemap, read the
cross streets at each segment's endpoints, record as a committed CSV. Approximately 39
CBD segments.

### 9.2 Control comparison not yet run

No result can be attributed until the identical analysis runs on untreated CBD streets
(Lonsdale, Bourke, Russell). If controls show comparable drift, the William Street
increase is city-wide trend rather than intervention effect.

### 9.3 Coverage — only 11 of 96 treatment segments analysable

The sensor archive is CBD-only and ends May 2020.

| Street | Segments | Intervention | Status |
|---|---|---|---|
| William St | 4 | Apr 2017 | Usable |
| La Trobe St | 7 | Jan 2013 | Usable; pre-period overlaps sensor rollout |
| Peel St | 2 | Jul 2020 | Baseline only |
| Exhibition St | 2 | Oct 2020 | Baseline only |

The remaining 85 treatment segments require aerial imagery. The sensor strand is a
deep case study, not the primary evidence base.

### 9.4 Control group invalid as a capacity counterfactual

IV's quarterly `StreetInScopeOnStreetParkingCap` appears to offer a free supply
measure. A placebo test — assigning controls random pseudo-intervention dates and
applying the identical comparison — shows **1.5%** of control segments ever change
recorded capacity across 105 quarters, against **91.8%** of treatment segments.

Real streets do not hold parking supply constant for 26 years. The likely explanation
is that capacity is re-surveyed only when a site is treated, making the field a record
of intervention events rather than of the world. The treatment−control difference is
therefore a data-maintenance artefact and must not be reported as an effect.

Pending confirmation from IV.

### 9.5 Partial sensor coverage of each block

Blocks carry 4–17 sensored bays, which is a subset of total kerbside capacity. Results
describe the sensored subset, not total parking supply.

### 9.6 Bay disappearance is ambiguous

A bay vanishing between years may mean physical removal or sensor decommissioning.
The dataset cannot distinguish these; Nearmap imagery is required.

### 9.7 Outstanding data

- 2019 archive not yet downloaded — needed for William Street's second post-year and
  the Peel/Exhibition baselines
- Bicycle Infrastructure Network (data.vic) not yet obtained — blocks the buffer
  overlap task entirely

### 9.8 Anomalies to investigate

- William St, Victoria–Walsh: 62→71 bays, four times the events of any other block,
  lowest utilisation. May be several blocks recorded as one; sits outside the CBD grid
- Little Collins–Collins: −17.0 pp with no bay change, the only block to fall

---

## 10. Validation performed

| Check | Result |
|---|---|
| Row-count reconciliation, 2017 | 35,908,877 vs published 35.9 M — complete |
| Monthly distribution | All 12 months, per-day rates plausible |
| Date format | Verified three independent ways |
| Hour-splitting identity | Split minutes sum to original event duration |
| Utilisation bounds | 0.36–0.74, within 0–1 |
| Quarter-code decoding | Reproduces known Melbourne build history |

An earlier version of the utilisation calculation returned 0.99–1.00 for every block.
The cause was counting vacancy events as occupancy and using a bay-count denominator
that excluded vacant bays. It was detected because the result was implausible, not
because anything raised an error.

This is the general risk in this dataset: **the failure modes are silent.** Date
misparsing, schema drift, inconsistent street naming and the utilisation error would
all have produced confident, plausible, wrong numbers. Each was caught by a
sanity check rather than an exception.
