"""
Group 1 (Cycling) — Site Matching & Intervention Validation

Workflow:
1. Match cycling counters to treatment street segments using GPS distance.
2. Keep only close matches within the distance threshold.
3. Save confirmed counter-to-segment matches.
4. Retrieve intervention history for matched street segments.

Input files:
    - ref_streets_spatial.xlsx
      315 street segments (96 treatment, 219 control)

    - ref_bike_site_listing.csv
      58 cycling counter sites with GPS coordinates

    - ref_sites_db.csv
      Intervention and construction history by street segment

Output files:
    - 02_confirmed_matches.csv
    - 03_intervention_history.csv

All input files should be placed in the same folder as this script.
"""

from pathlib import Path

import pandas as pd
from pyproj import Transformer
from shapely import wkt
from shapely.geometry import Point


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 160)

BASE_DIR = Path(__file__).resolve().parent

STREETS_SPATIAL_PATH = BASE_DIR / "ref_streets_spatial.xlsx"
BIKE_SITE_LISTING_PATH = BASE_DIR / "ref_bike_site_listing.csv"
SITES_DB_PATH = BASE_DIR / "ref_sites_db.csv"

CONFIRMED_MATCHES_PATH = BASE_DIR / "02_confirmed_matches.csv"
INTERVENTION_HISTORY_PATH = BASE_DIR / "03_intervention_history.csv"

DISTANCE_THRESHOLD_M = 12


# -------------------------------------------------------------------
# 1. Load treatment street segments
# -------------------------------------------------------------------

streets = pd.read_excel(STREETS_SPATIAL_PATH)

treatment = streets.loc[
    streets["treatment_or_control"] == "treatment"
].copy()

treatment["geom"] = treatment["wkt_geom"].apply(wkt.loads)

print(f"Total street segments: {len(streets)}")
print(f"Treatment segments: {len(treatment)}")


# -------------------------------------------------------------------
# 2. Load cycling counter sites
# -------------------------------------------------------------------

counters = pd.read_csv(BIKE_SITE_LISTING_PATH)

print(f"Total counter rows: {len(counters)}")
print(
    f"Unique cycling counter sites: "
    f"{counters['SITE_XN_ROUTE'].nunique()}"
)


# -------------------------------------------------------------------
# 3. Match each cycling counter to the nearest treatment segment
# -------------------------------------------------------------------

transformer = Transformer.from_crs(
    "EPSG:7844",
    "EPSG:7899",
    always_xy=True,
)

matches = []

for site_id, group in counters.groupby("SITE_XN_ROUTE"):

    for _, row in group.iterrows():

        x, y = transformer.transform(
            row["GPS_LONG"],
            row["GPS_LAT"],
        )

        counter_point = Point(x, y)

        distances = treatment["geom"].apply(
            lambda geom: counter_point.distance(geom)
        )

        nearest_idx = distances.idxmin()

        matches.append({
            "counter_site": site_id,
            "loc_leg": row["LOC_LEG"],
            "tfm_desc": row["TFM_DESC"],
            "nearest_segment_id": treatment.loc[
                nearest_idx,
                "street_segment_id",
            ],
            "nearest_street": treatment.loc[
                nearest_idx,
                "street_name",
            ],
            "nearest_suburb": treatment.loc[
                nearest_idx,
                "suburb",
            ],
            "distance_m": round(distances.min(), 2),
        })


matches_df = pd.DataFrame(matches)

confirmed = (
    matches_df.loc[
        matches_df["distance_m"] <= DISTANCE_THRESHOLD_M
    ]
    .sort_values("distance_m")
    .copy()
)

print(
    f"\nRows within {DISTANCE_THRESHOLD_M} m "
    f"of a treatment segment: {len(confirmed)}"
)

print(confirmed.to_string())


# -------------------------------------------------------------------
# 4. Summarise confirmed counter sites
# -------------------------------------------------------------------

confirmed_sites = (
    confirmed[
        [
            "counter_site",
            "nearest_street",
            "nearest_suburb",
        ]
    ]
    .drop_duplicates()
    .sort_values(
        [
            "nearest_street",
            "counter_site",
        ]
    )
)

print("\nConfirmed cycling counter sites:")
print(confirmed_sites.to_string(index=False))


# -------------------------------------------------------------------
# 5. Save confirmed matches
# -------------------------------------------------------------------

confirmed.to_csv(
    CONFIRMED_MATCHES_PATH,
    index=False,
)

print(
    f"\nSaved confirmed matches: "
    f"{CONFIRMED_MATCHES_PATH.name}"
)


# -------------------------------------------------------------------
# 6. Load intervention history
# -------------------------------------------------------------------

sites_db = pd.read_csv(
    SITES_DB_PATH,
    encoding="latin1",
)

matched_segment_ids = (
    confirmed["nearest_segment_id"]
    .dropna()
    .unique()
    .tolist()
)

print(
    "\nMatched street segment IDs:",
    sorted(matched_segment_ids),
)


# -------------------------------------------------------------------
# 7. Extract intervention history for matched segments
# -------------------------------------------------------------------

history = sites_db.loc[
    sites_db["StreetSegmentID"].isin(matched_segment_ids)
].copy()

history_view = (
    history[
        [
            "SiteID",
            "StreetSegmentID",
            "StreetInScope",
            "DateOfIntervention/InitialCapture",
            "InterventionSummary",
        ]
    ]
    .sort_values(
        [
            "StreetSegmentID",
            "DateOfIntervention/InitialCapture",
        ]
    )
)

print("\nIntervention history for matched segments:")
print(history_view.to_string(index=False))


# -------------------------------------------------------------------
# 8. Save intervention history
# -------------------------------------------------------------------

history_view.to_csv(
    INTERVENTION_HISTORY_PATH,
    index=False,
)

print(
    f"\nSaved intervention history: "
    f"{INTERVENTION_HISTORY_PATH.name}"
)


# -------------------------------------------------------------------
# Summary
# -------------------------------------------------------------------

print("\nAnalysis complete.")

print(
    """
Summary:
- Started with 315 street segments.
- Filtered to 96 treatment segments.
- Compared treatment segments with 58 cycling counter sites.
- Retained counter locations within 12 m of a treatment segment.
- Confirmed candidate sites include:
    Wellington Street
    Moorabool Street
    Heidelberg Road
    Albert Street
- Retrieved intervention history for the matched street segments.
"""
)