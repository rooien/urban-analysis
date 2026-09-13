# USIA — Imagery Pilot (Strand 2): Status & Handover

**Last updated:** 19 August 2026
**Owner:** Ro (Team B), with a buddy now helping on manual counting
**Paste this whole file into a new chat to pick up where we left off.**

---

## 1. Context

Deakin capstone (SIT378, "Chameleon" program) with Infrastructure Victoria. 315 street
segments (96 treatment, 219 control). Two evidence strands, split by what data exists,
not by location type:

- **Strand 1 (sensor)** — 17 segments on 4 CBD streets (William, La Trobe, Peel,
  Exhibition) with real CoM parking sensor data. Separate, parked branch
  (`feature/rt/sensor-eda-writeup`), blocked on a block-to-segment crosswalk. Not
  touched this session.
- **Strand 2 (imagery)** — everything else (~298 segments). No sensor data ever
  existed; only path to before/after utilisation is Nearmap aerial imagery, manually
  counted, later validated against SAM3. **This document covers Strand 2 only.**

Branch: `feature/rt/imagery-pilot` (pushed to both `upstream` =
`Chameleon-company/Victoria-Urban-Planning` and `origin` = your fork
`rooien/urban-analysis`).

---

## 2. Where everything lives

| What | Path |
|---|---|
| Scripts | `team_b/notebooks/rt/analysis/scripts/` |
| Coverage-audit output | `team_b/notebooks/rt/analysis/docs/capture_matrix.csv` |
| Pilot-only date lookup (2 streets) | `team_b/notebooks/rt/analysis/docs/nearmap_survey_dates_pilot.csv` |
| QGIS bulk-import XML, pilot (20 images) | `team_b/notebooks/rt/analysis/scripts/qgis_xyz_connections_pilot.xml` |
| QGIS bulk-import XML, full scale (678 images) | `team_b/notebooks/rt/analysis/scripts/qgis_xyz_connections_full.xml` |
| Coverage-API response cache | `team_b/notebooks/rt/analysis/data/coverage_cache/` |
| IV source data | `C:\Users\erteo\Desktop\26T2\SIT378 - Project B` |

Both XML files ship with an `apikey=YOUR_API_KEY` placeholder — Find & Replace with
your real key in your own local copy before importing into QGIS. Never commit the
keyed version.

---

## 3. Scripts (all reusable, not one-off)

- **`pilot_street_scan.py`** — selects candidate segments (single clean construction
  transition, protected bike lane, outside sensor streets). Used once to pick the 2
  pilot streets; reusable for future segment scans.
- **`construction_window.py`** — `get_construction_window(segment_id)` returns
  `(start_date, end_date)` from IV's quarterly `is_under_construction` transitions, or
  `None` if the segment doesn't have a single clean transition. Handles the
  float/int/string `street_segment_id` dtype trap internally.
- **`survey_date_lookup.py`** — `build_lookup(...)` merges two endpoints' coverage
  dates, classifies before/during-construction/after, labels day-of-week and IV's
  financial-year-quarter format.
- **`00_coverage_audit.py`** — the stage-00 gate. Loads all treatment segments outside
  sensor coverage from `streets_spatial.gpkg`, filters to segments with a construction
  window, queries Nearmap's coverage API at both endpoints (cached, retried, rate-limit
  aware), bounds results to 12 months either side of construction (**this bound was a
  bug fix made this session — the first run pulled entire multi-year histories before
  the fix; if you ever see a segment with 50+ images, the fix didn't take**), and
  auto-generates the QGIS XYZ XML for every feasible segment.

Requires `NEARMAP_API_KEY` as an environment variable, set via `setx` (permanent, not
session-only) so it survives across terminal windows — **never pasted into chat or
committed.** (One earlier key did get exposed in a chat message during setup, due to a
`setx` syntax error being pasted with the key still in it — if that key hasn't been
rotated since, worth doing so via whatever dashboard issued it, low priority.)

---

## 4. Key findings and decisions this session

- **Pilot streets:** Elizabeth St, Richmond (segment 9168, metro, construction Apr–Oct
  2020) and Moorabool St, South Geelong (segment 10838, regional, construction Oct
  2021–Jan 2022). Picked deliberately as one metro + one regional to stress-test the
  known regional-coverage-gap risk early. **Moorabool St caveat:** it already had a
  *painted* bike lane since 2016 — its "before" images aren't a true no-bike-lane
  baseline, only painted→protected.
- **Coverage is genuinely per-location**, not a global calendar — proven directly: even
  the two ends of the same ~130m segment had different available survey dates.
  Everything has to be looked up per-segment, per-endpoint; nothing can be assumed.
- **Nearmap coordinate order is long,lat** (not lat,long) — a real gotcha, easy to get
  backwards when copying from QGIS.
- **The 79 treatment segments needing imagery** (outside the 4 sensor streets) split:
  **53 have a clean single construction window**, **26 don't**.
  - Of those 26: **18 have no data in `sites_db.csv` either** (two independent sources
    agree — genuine gap). **8 do appear in `sites_db.csv`** but still lack a clean
    transition in IV's own panel — a real discrepancy, documented, not resolved
    (`sites_db.csv`'s intervention dates are explicitly non-authoritative, so not used
    to patch this).
  - Ro's idea for these 26: scan multi-year imagery to visually date the intervention
    where IV's panel doesn't record it. Good idea, but explicitly **deferred** until
    after SAM3 validation on the pilot — it's a manual/visual task, not scriptable, and
    stacking a 4th unvalidated thing (after SAM3 accuracy, the 53-segment scale-up, and
    the 26-segment recovery idea) on top of an unvalidated pilot was flagged as
    scope-creep risk.
- **Coverage-audit run result (53 segments queried):** 0 segments had zero coverage at
  either endpoint. **51 of 53 turned out feasible** (both a before *and* an after date
  with full both-ends coverage). After the 12-month-window bug fix: **678 images total**
  across those 51 segments (~13 per segment, consistent with the pilot's per-segment
  average).
- **Sensor-covered CBD streets:** of 10 streets checked against the CoM sensor archive,
  only 4 (William, La Trobe, Peel, Exhibition) are actual treatment streets; the other 6
  (Queen, Collins, Russell, Spencer, Lonsdale, Bourke) are controls. Found a naming
  inconsistency while checking this: `street_spatial.csv` stores Bourke St as
  `"BOURKE ST"` not `"BOURKE STREET"` — same abbreviation trap already known for
  cross-street names in the sensor data. Worth checking other streets for the same issue
  before it silently breaks a future join.
- **Controls (219 segments) are explicitly out of scope for this audit** — they have no
  construction window to classify against, and the method for assigning them a
  comparison window (nearest treatment segment's dates? a fixed study-wide window?)
  hasn't been decided. Separate follow-up.
- **A cloud-generated script (`01_build_count_workspace.py`) was reviewed and rejected
  as unsafe to run as-is** — defaulted to a different team member's personal reference
  file instead of our authoritative `streets_spatial.gpkg`, and assumed an 18-person
  counting team when only 2 people (Ro + buddy) exist. Not committed anywhere; sitting
  only in chat history if it's needed for reference later.

---

## 5. Manual counting rules (agreed, not yet applied)

- Count any stationary vehicle in the kerbside lane as occupying a space; exclude
  driveways, clearways, loading/bus zones, moving traffic.
- Cropped/edge vehicles: count in whichever image tile contains their visual center.
- Obscured by trees/shadow: if <15% of a kerb stretch is visible, exclude and note it
  (Grattan's threshold).
- **Capacity measured per-image, not once per segment** — kerb length ÷ 6.0m
  (parallel) or ÷ 2.5m (angle), round down, −18% where a run >15m has driveways. A bike
  lane can change available kerb length between before/after, so capacity must be
  measured on each image separately.
- Count all vehicle types (not just cars) — SAM3's prompt is "car" only, so an expected
  discrepancy on vans/trucks should be treated as known, not a bug.

---

## 6. Where we're actually up to, and what's next

**Done:** street selection, coverage audit (all 79 treatment segments, 53 with clean
windows, 51 feasible), counting rules written, both pilot and full-scale QGIS XML
generated.

**Not yet done:** no image has actually been exported, no car has been counted, SAM3
hasn't been touched.

**Immediate next step — do the pilot first, not the full 51-segment set:**
1. Import `qgis_xyz_connections_pilot.xml` (20 images, 2 streets) into QGIS via Layer →
   Data Source Manager → XYZ Tiles → Load Connections (after Find & Replace-ing your API
   key into your own copy).
2. Export all 20 images per the procedure in §... (zoom to buffer → hide vector layers →
   only the correct dated layer visible → Export Map to Image, world file **ticked**,
   ~7cm/pixel → filename `{street_segment_id}_{capture_date}.tif` → reopen and confirm
   georeferencing before moving on).
3. **Both Ro and buddy independently count all 20 images** against the rules in §5 —
   full overlap, not a split, specifically to get a real inter-rater reliability number
   before this becomes SAM3's ground truth.
4. Compare the two counts; where they disagree, that's signal about the rules
   themselves, not just measurement noise.
5. Run SAM3 in Colab on the same 20 images, compare to the (cross-checked) manual
   counts. Grattan's own benchmark: F1 > 94%.
6. **Only after that validates** — decide how to deploy Ro + buddy across the 51-segment,
   678-image full set (likely: split segments between them, with a smaller double-coding
   percentage for ongoing quality checks, not full duplication like the pilot).

**Deferred, not forgotten:** the 26 no-window segments (cheap coverage-lookup-only pass
recommended, no classification possible); the 219 control segments (window-assignment
method undecided); the second assigned task (bike-lane/parking buffer overlap — blocked
on obtaining the Bicycle Infrastructure Network dataset, not started); 2019 sensor
archive download; sensor-strand block-to-segment crosswalk.
