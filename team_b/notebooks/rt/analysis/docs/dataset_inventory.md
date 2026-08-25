# CoM Parking Data — What Each Dataset Gives Us

Verified against the City of Melbourne open data portal, 4 August 2026.
Full archive: **10 files, ~9.8 GB compressed, 363.6 million rows**, covering
1 Jan 2011 – 31 May 2020.

---

## 1. The ten event archives

Every row is one parking event (a vehicle arriving and departing one bay), not one
observation. Download URL pattern:
`https://opendatasoft-s3.s3.amazonaws.com/downloads/archive/<id>.zip`

| Year | id | Size | Rows | What this year gives USIA |
|---|---|---|---|---|
| 2011 | `vkxi-k7ps` | 592.8 MB | 21.8 M | La Trobe pre-period (partial — sensor rollout still in progress, so lowest row count in the series) |
| 2012 | `vbe9-m4tk` | 1.51 GB | 52.5 M | **La Trobe pre-period, the clean one.** Peak coverage year |
| 2013 | `7jq6-k9kf` | 1.24 GB | 43.2 M | **La Trobe post-period** (intervention Jan 2013) |
| 2014 | `t6hb-9uf2` | 1.56 GB | 51.5 M | La Trobe post +1yr; medium-term persistence check |
| 2015 | `apua-t2tb` | 1.17 GB | 37.5 M | William St pre; control-group trend |
| 2016 | `dj7e-rdx9` | 1.07 GB | 34.1 M | **William St pre-period, the clean one** |
| 2017 | `u9sa-j86i` | 1.13 GB | 35.9 M | **William St post-period** (intervention Apr 2017) |
| 2018 | `5532-ig9r` | 504 MB | 30.2 M | William St post +1yr; persistence |
| 2019 | `7pgd-bdf2` | 717.1 MB | 42.7 M | Last full normal year. **Baseline for Peel & Exhibition** (treated 2020) |
| 2020 | `4n3a-s6rn` | 258.5 MB | 14.2 M | **Jan–May only.** Immediate pre-treatment baseline + COVID natural experiment |

### Reading the row counts

The series is not flat and the shape is itself informative: 21.8 M (2011) → 52.5 M
(2012) → down to 30.2 M (2018) → back up to 42.7 M (2019). Two candidate
explanations — sensor fleet size changing, or genuine turnover changing — and they
have opposite meanings for utilisation.

**Normalise per active sensor before comparing any two years.** Count distinct
`StreetMarker` values per month and divide. A raw year-on-year event count is
uninterpretable. This is the most likely way to get the analysis wrong.

---

## 2. Reference layers (small, API export)

| Dataset | What it gives us | Join key |
|---|---|---|
| `on-street-parking-bays` | Bay polygons. **This is what links sensor events to your 315 street segments** — without it the event files are unmappable | `marker_id` |
| `on-street-parking-bay-sensors` | Live sensor points, current snapshot | `marker_id` → bays, `bay_id` → restrictions |
| `on-street-car-park-bay-restrictions` | Restriction type and hours per bay (1P, 2P, clearway, loading) | `bay_id` |

**Caveat on the bays layer.** It is a *current* snapshot. Bays decommissioned before
2026 may be absent, so historical `StreetMarker` values from 2011–2015 will not all
match. Expect attrition on the early years — measure it and report it rather than
assuming a full join. This directly limits how far back La Trobe can be pushed.

---

## 3. Event file fields

Column names drift between years, so `02_sensor_utilisation.py` normalises via
`COLMAP`. Broadly each row carries:

- **`StreetMarker`** — bay identifier, the join key to bay geometry. Essential.
- **`ArrivalTime` / `DepartureTime`** — event bounds. Occupied-minutes come from these.
- **`DurationSeconds`** — precomputed, but **can be negative**; recompute from timestamps.
- **`StreetName`, `BetweenStreet1/2`, `SideOfStreet`** — text location. Useful as a
  fallback filter and a sanity check on the spatial join, and `SideOfStreet` matters
  because bike lanes usually affect one side only.
- **`Sign`** — restriction in force at event time.
- **`InViolation`** — overstay flag.

Verify field names on first load of each year rather than trusting this list.

---

## 4. What the whole archive delivers, by question

| Question | Years needed | What you get |
|---|---|---|
| **William St before/after** | 2015–2019 | The flagship result. 2 yrs pre, 2.7 yrs post, clear of COVID, protected bike lane. Highest-confidence estimate in the project |
| **La Trobe St before/after** | 2011–2015 | Second case. Weaker — pre-period sits in the sensor rollout, so pre-coverage is unstable |
| **Peel & Exhibition baseline** | 2019–2020 | Pre-intervention baseline only. Post comes from Nearmap. Sets up the imagery/sensor calibration |
| **Control trend (23 CBD segments)** | all | The counterfactual. Queen, Collins, Russell, Spencer, Lonsdale, Bourke — untreated, sensored, same period |
| **Imagery calibration** | any | Sensor utilisation vs Nearmap visual classification on the same street-hour. **This is what makes the other 85 imagery-only segments defensible** |
| **COVID natural experiment** | 2019 + 2020 | Feb vs Apr 2020 on identical bays. A clean demand shock with supply held constant |
| **Diurnal / day-of-week profiles** | any 1 yr | Peak-hour definition, weekday vs weekend, for the report's method section |
| **Turnover & duration** | any | Mean stay, turnover per bay per day, overstay rates — richer than occupancy alone and directly relevant to IV's policy narrative |

---

## 5. Two uses beyond the core question

**Calibration is the highest-value use of the full archive.** Only 11 segments support
sensor before/after — but all 39 CBD segments have sensor coverage across all ten
years. That is a large ground-truth set for validating the Nearmap classification:
classify an aerial image, compare to measured occupancy at the same timestamp, derive
an accuracy rate. Report that rate alongside every imagery-based figure and the
imagery strand stops being "indicative" and becomes calibrated. This is IV's stated
priority — "transparent, replicable methods" — and it is what makes the other 85
segments credible.

**The COVID window is a free experiment.** Feb 2020 vs Apr 2020, same bays, same
sensors, supply unchanged, demand collapsed. It gives an empirical answer to "what
does a large drop in parking demand look like in this data", which is the natural
reference scale for judging whether a bike lane effect is large or small. IV asked how
you would treat COVID; using it as a calibration benchmark rather than a nuisance to
be adjusted away is a stronger answer than excluding it.

---

## 6. Practical notes

I could not download these from this environment — the sandbox blocks the CoM and S3
domains. Run locally or in Colab:

```bash
python analysis/src/00_download_com_data.py --reference
python analysis/src/00_download_com_data.py --all          # ~9.8 GB
# or, minimum viable path (~3.9 GB) — delivers William St:
python analysis/src/00_download_com_data.py --years 2015 2016 2017 2018 2019
```

- **Disk**: ~9.8 GB compressed, roughly 45–60 GB uncompressed. Do not extract the
  CSVs; `02_sensor_utilisation.py` streams from inside the zips.
- **Memory**: never `read_csv` a whole year. The script chunks at 2 M rows and filters
  to study-segment bays before anything else, which should cut 90–95% of rows immediately.
- **Time**: expect 20–40 min per year end-to-end on a laptop. The full ten years is an
  overnight job. Intermediate results are cached per year as parquet in `data/interim/`,
  so it is resumable.
- **Colab**: the free tier will not hold this. Mount Drive, or run locally.

Suggested order: 2016–2019 first. That is 3.9 GB and delivers the flagship William
Street result. Add 2011–2015 for La Trobe, then 2020 for COVID and the Peel/Exhibition
baselines.
