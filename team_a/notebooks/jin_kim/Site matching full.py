"""
Group 1 (Cycling) — Site Matching & Intervention Date Check

Two steps:
1. Site matching: out of 96 treatment street segments, find which ones
   actually have a cycling counter nearby (GPS distance match).
2. Intervention dates: for the matched sites, pull each segment's
   construction/intervention history from sites_db.csv.

Inputs:
    - streets_spatial.xlsx   -> 315 street segments (96 treatment, 219 control)
    - bike_site_listing.csv  -> 58 cycling counter sites with GPS coordinates
    - sites_db.csv           -> intervention/construction history per segment

Place the three input files in the same folder as this script.
"""

from pathlib import Path

import pandas as pd
from shapely import wkt
from shapely.geometry import Point
from pyproj import Transformer

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 160)

# ---------------------------------------------------------------
# 0. Paths
# ---------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

STREETS_SPATIAL_PATH = BASE_DIR / "streets_spatial.xlsx"
BIKE_SITE_LISTING_PATH = BASE_DIR / "bike_site_listing.csv"
SITES_DB_PATH = BASE_DIR / "sites_db.csv"

# ---------------------------------------------------------------
# 1. Load the 96 treatment segments
# ---------------------------------------------------------------
streets = pd.read_excel(STREETS_SPATIAL_PATH)
treatment = streets[streets["treatment_or_control"] == "treatment"].copy()
treatment["geom"] = treatment["wkt_geom"].apply(wkt.loads)

print(f"Total segments: {len(streets)}")
print(f"Treatment segments: {len(treatment)}")

# ---------------------------------------------------------------
# 2. Load the 58 cycling counter sites
# ---------------------------------------------------------------
counters = pd.read_csv(BIKE_SITE_LISTING_PATH)
print(f"Total counter rows: {len(counters)}")
print(f"Unique counter sites: {counters['SITE_XN_ROUTE'].nunique()}")

# ---------------------------------------------------------------
# 3. Match each counter to the nearest treatment segment
# ---------------------------------------------------------------
transformer = Transformer.from_crs(
    "EPSG:7844",
    "EPSG:7899",
    always_xy=True
)

DISTANCE_THRESHOLD_M = 12

matches = []

for site_id, group in counters.groupby("SITE_XN_ROUTE"):
    for _, row in group.iterrows():
        x, y = transformer.transform(row["GPS_LONG"], row["GPS_LAT"])
        pt = Point(x, y)

        dists = treatment["geom"].apply(lambda g: pt.distance(g))
        nearest_idx = dists.idxmin()

        matches.append({
            "counter_site": site_id,
            "loc_leg": row["LOC_LEG"],
            "tfm_desc": row["TFM_DESC"],
            "nearest_segment_id": treatment.loc[
                nearest_idx, "street_segment_id"
            ],
            "nearest_street": treatment.loc[
                nearest_idx, "street_name"
            ],
            "nearest_suburb": treatment.loc[
                nearest_idx, "suburb"
            ],
            "distance_m": round(dists.min(), 2),
        })

matches_df = pd.DataFrame(matches)

confirmed = matches_df[
    matches_df["distance_m"] <= DISTANCE_THRESHOLD_M
]

print(
    f"\nRows within {DISTANCE_THRESHOLD_M}m "
    f"of a treatment segment: {len(confirmed)}"
)

print(
    confirmed
    .sort_values("distance_m")
    .to_string()
)

confirmed_sites = confirmed[
    ["counter_site", "nearest_street", "nearest_suburb"]
].drop_duplicates()

print("\nConfirmed counter sites:")
print(confirmed_sites.to_string())

# Save results
confirmed.sort_values("distance_m").to_csv(
    BASE_DIR / "confirmed_matches.csv",
    index=False
)

# ---------------------------------------------------------------
# 4. Intervention dates for the matched sites
# ---------------------------------------------------------------
sites_db = pd.read_csv(
    SITES_DB_PATH,
    encoding="latin1"
)

matched_segment_ids = (
    confirmed["nearest_segment_id"]
    .unique()
    .tolist()
)

print("\nMatched segment IDs:", sorted(matched_segment_ids))

history = sites_db[
    sites_db["StreetSegmentID"].isin(matched_segment_ids)
]

history_view = history[[
    "SiteID",
    "StreetSegmentID",
    "StreetInScope",
    "DateOfIntervention/InitialCapture",
    "InterventionSummary"
]].sort_values([
    "StreetSegmentID",
    "DateOfIntervention/InitialCapture"
])

print("\nIntervention history for matched segments:")
print(history_view.to_string())

history_view.to_csv(
    BASE_DIR / "intervention_history.csv",
    index=False
)

print(
    "\nSaved: confirmed_matches.csv and "
    "intervention_history.csv in the same folder."
)

# ---------------------------------------------------------------
# Result:
#   96 treatment segments filtered from the 315-row spatial file.
#   Cross-referencing against all 58 cycling counter sites, only
#   counters within a few metres of a treatment segment count as
#   confirmed matches -> narrows the field to 4 streets / 5 counters:
#     Wellington (32493), Moorabool (34687),
#     Heidelberg Road (40004, 40005), Albert (9077)
#   Each matched segment's intervention history comes from
#   sites_db.csv, giving the basis for further before/after analysis.
# ---------------------------------------------------------------