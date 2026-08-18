"""
USIA Team A (Cycling) — Intervention Data Quality Check

Purpose:
Validate intervention information for the cycling sites selected during
the site-matching stage.

This script:
1. Loads the intervention and quarterly street-segment datasets.
2. Applies the PO-recommended forward-fill and backward-fill method to
   InterventionType and InterventionSummary within each street segment.
3. Reviews Wellington Street segments 5881, 5882 and 5883.
4. Identifies duplicate or conflicting quarter records that cannot be
   resolved by filling missing values.
5. Checks the five matched cycling segments:
      - 5881  Wellington Street
      - 10838 Moorabool Street
      - 8218  Heidelberg Road
      - 8221  Heidelberg Road
      - 9801  Albert Street
6. Cross-checks candidate completion quarters against intervention dates
   recorded in sites_db.

Input files:
    - ref_sites_db.csv
    - ref_street_segment_qtr_attributes.csv

The input files should be stored in the same folder as this script/notebook.

This code can run as either:
    - a Python script (.py), or
    - a Jupyter Notebook (.ipynb).
"""

from pathlib import Path

import pandas as pd


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

pd.set_option("display.width", 160)
pd.set_option("display.max_rows", 200)
pd.set_option("display.max_columns", None)

# Works in both Python scripts and Jupyter notebooks.
try:
    BASE_DIR = Path(__file__).resolve().parent
except NameError:
    BASE_DIR = Path.cwd()

SITES_DB_PATH = BASE_DIR / "ref_sites_db.csv"
QTR_ATTR_PATH = BASE_DIR / "ref_street_segment_qtr_attributes.csv"

WELLINGTON_SEGMENTS = {
    5881: "matched to counter 32493 (~6–7 m)",
    5882: "~67–121 m from counter 32493",
    5883: "~309–363 m from counter 32493",
}

MATCHED_CYCLING_SEGMENTS = {
    5881: "Wellington St (counter 32493)",
    10838: "Moorabool St (counter 34687)",
    8218: "Heidelberg Rd (counter 40004)",
    8221: "Heidelberg Rd (counter 40005)",
    9801: "Albert St (counter 9077)",
}

FILL_COLUMNS = [
    "InterventionType",
    "InterventionSummary",
]


print("Working directory:", BASE_DIR)
print("sites_db input:", SITES_DB_PATH)
print("quarter attributes input:", QTR_ATTR_PATH)


# -------------------------------------------------------------------
# 1. Check input files
# -------------------------------------------------------------------

for path in [SITES_DB_PATH, QTR_ATTR_PATH]:
    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}\n"
            "Make sure the reference files are stored in the same "
            "folder as this script or notebook."
        )


# -------------------------------------------------------------------
# 2. Load data
# -------------------------------------------------------------------

sites_db = pd.read_csv(
    SITES_DB_PATH,
    encoding="latin1",
)

qtr = pd.read_csv(
    QTR_ATTR_PATH,
)

print("\nData loaded successfully.")
print(f"sites_db rows: {len(sites_db):,}")
print(f"quarter attribute rows: {len(qtr):,}")


# -------------------------------------------------------------------
# 3. Check required columns
# -------------------------------------------------------------------

required_qtr_columns = {
    "STREET_SEGMENT_ID",
    "SiteID",
    "QUARTER",
    "Baseline",
    "InterventionType",
    "InterventionSummary",
    "is_under_construction",
    "other_major_construction",
}

missing_qtr_columns = required_qtr_columns - set(qtr.columns)

if missing_qtr_columns:
    raise KeyError(
        "Missing required columns in "
        "ref_street_segment_qtr_attributes.csv: "
        f"{sorted(missing_qtr_columns)}"
    )


required_sites_db_columns = {
    "StreetSegmentID",
    "Baseline",
    "DateOfIntervention/InitialCapture",
}

missing_sites_db_columns = (
    required_sites_db_columns - set(sites_db.columns)
)

if missing_sites_db_columns:
    raise KeyError(
        "Missing required columns in ref_sites_db.csv: "
        f"{sorted(missing_sites_db_columns)}"
    )


# -------------------------------------------------------------------
# 4. Prepare missing intervention values
# -------------------------------------------------------------------

# Treat empty strings as missing values.
for column in FILL_COLUMNS:
    qtr[column] = (
        qtr[column]
        .replace(r"^\s*$", pd.NA, regex=True)
    )

# Keep the original row order.
qtr = qtr.sort_index().copy()


# -------------------------------------------------------------------
# 5. Apply PO-recommended forward-fill + backward-fill
# -------------------------------------------------------------------

qtr_filled = qtr.copy()

qtr_filled[FILL_COLUMNS] = (
    qtr_filled
    .groupby("STREET_SEGMENT_ID")[FILL_COLUMNS]
    .transform(lambda group: group.ffill().bfill())
)

print("\nForward-fill + backward-fill completed.")


# -------------------------------------------------------------------
# 6. Wellington Street segment review
# -------------------------------------------------------------------

def show_segment(segment_id: int, label: str) -> None:
    """
    Display known intervention rows, Baseline == 0 candidate quarters,
    and remaining blanks for one street segment.
    """

    print("\n" + "=" * 70)
    print(f"Segment {segment_id} — {label}")
    print("=" * 70)

    before = qtr.loc[
        qtr["STREET_SEGMENT_ID"] == segment_id
    ].copy()

    after = qtr_filled.loc[
        qtr_filled["STREET_SEGMENT_ID"] == segment_id
    ].copy()

    if before.empty:
        print("No rows found for this segment.")
        return

    known_columns = [
        "QUARTER",
        "Baseline",
        "InterventionType",
        "InterventionSummary",
        "is_under_construction",
        "other_major_construction",
    ]

    known = before.loc[
        before["InterventionType"].notna(),
        known_columns,
    ]

    print("\nKnown intervention rows before fill:")

    if known.empty:
        print("No known intervention rows.")
    else:
        print(
            known.to_string(index=False)
        )

    # Baseline == 0 can occur more than once.
    # Do not automatically assume that the first occurrence is
    # the actual intervention completion quarter.
    candidates = before.loc[
        before["Baseline"] == 0,
        [
            "QUARTER",
            "InterventionSummary",
        ],
    ]

    print("\nBaseline == 0 candidate quarters:")

    if candidates.empty:
        print("None found.")
    else:
        print(
            candidates.to_string(index=False)
        )

    remaining_blanks = (
        after["InterventionType"]
        .isna()
        .sum()
    )

    print(
        "\nBlank InterventionType cells remaining "
        f"after fill: {remaining_blanks}"
    )


print("\n" + "#" * 70)
print("WELLINGTON STREET SEGMENTS")
print("#" * 70)

for segment_id, label in WELLINGTON_SEGMENTS.items():
    show_segment(
        segment_id,
        label,
    )


# -------------------------------------------------------------------
# 7. Find duplicate quarter rows
# -------------------------------------------------------------------

print("\n" + "#" * 70)
print("DUPLICATE / CONFLICTING QUARTER RECORDS")
print("#" * 70)

duplicate_mask = qtr.duplicated(
    subset=[
        "STREET_SEGMENT_ID",
        "QUARTER",
    ],
    keep=False,
)

duplicate_rows = (
    qtr.loc[duplicate_mask]
    .sort_values(
        [
            "STREET_SEGMENT_ID",
            "QUARTER",
        ]
    )
    .copy()
)

all_duplicate_segments = sorted(
    duplicate_rows[
        "STREET_SEGMENT_ID"
    ]
    .dropna()
    .unique()
    .tolist()
)


# -------------------------------------------------------------------
# 8. Separate multi-SiteID mapping issues
# -------------------------------------------------------------------

site_id_counts = (
    qtr
    .groupby("STREET_SEGMENT_ID")["SiteID"]
    .nunique()
)

multi_site_segments = sorted(
    site_id_counts.loc[
        site_id_counts > 1
    ]
    .index
    .tolist()
)

problem_segments = sorted(
    set(all_duplicate_segments)
    - set(multi_site_segments)
)

print(
    f"\n{len(problem_segments)} segments have a genuine "
    "duplicate/conflicting quarter record:"
)

print(problem_segments)


if problem_segments:
    print("\nExample conflicting rows:")

    example_duplicates = (
        duplicate_rows.loc[
            duplicate_rows["STREET_SEGMENT_ID"].isin(
                problem_segments
            ),
            [
                "STREET_SEGMENT_ID",
                "QUARTER",
                "Baseline",
                "InterventionType",
                "InterventionSummary",
            ],
        ]
        .head(20)
    )

    print(
        example_duplicates.to_string(index=False)
    )


print(
    "\nSegments with more than one SiteID mapped to the same "
    "street segment:"
)

print(
    multi_site_segments
    if multi_site_segments
    else "None"
)


# -------------------------------------------------------------------
# 9. Summary for matched cycling segments
# -------------------------------------------------------------------

print("\n" + "#" * 70)
print("SUMMARY — MATCHED CYCLING SEGMENTS")
print("#" * 70)

for segment_id, label in MATCHED_CYCLING_SEGMENTS.items():

    segment_data = qtr.loc[
        qtr["STREET_SEGMENT_ID"] == segment_id
    ]

    completion_quarters = (
        segment_data.loc[
            segment_data["Baseline"] == 0,
            "QUARTER",
        ]
        .tolist()
    )

    has_duplicate_issue = (
        segment_id in problem_segments
    )

    print(
        f"Segment {segment_id:>6} | "
        f"{label:<32} | "
        f"Baseline==0 quarters: {completion_quarters} | "
        "duplicate-row issue: "
        f"{'YES' if has_duplicate_issue else 'no'}"
    )


# -------------------------------------------------------------------
# 10. Identify segments with multiple Baseline == 0 candidates
# -------------------------------------------------------------------

multi_candidate_segments = []

for segment_id in MATCHED_CYCLING_SEGMENTS:

    count = (
        qtr.loc[
            qtr["STREET_SEGMENT_ID"] == segment_id,
            "Baseline",
        ]
        .eq(0)
        .sum()
    )

    if count > 1:
        multi_candidate_segments.append(
            segment_id
        )


if multi_candidate_segments:

    example_id = multi_candidate_segments[0]

    example_rows = qtr.loc[
        (qtr["STREET_SEGMENT_ID"] == example_id)
        & (qtr["Baseline"] == 0),
        [
            "QUARTER",
            "InterventionSummary",
        ],
    ]

    print(
        f"\nNote: {len(multi_candidate_segments)} matched segment(s) "
        "have more than one Baseline == 0 quarter:"
    )

    print(multi_candidate_segments)

    print(
        "\nDo not automatically assume the first quarter is "
        "the actual intervention completion date."
    )

    print(
        f"\nExample — segment {example_id}:"
    )

    print(
        example_rows.to_string(index=False)
    )

else:
    print(
        "\nNone of the matched cycling segments have more than "
        "one Baseline == 0 quarter."
    )


# -------------------------------------------------------------------
# 11. Convert financial-year quarter to date range
# -------------------------------------------------------------------

def fy_quarter_to_range(
    quarter_code: str,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """
    Convert an Australian financial-year quarter code such as
    '1516Q1' into its calendar start and end dates.

    Q1 = July–September
    Q2 = October–December
    Q3 = January–March
    Q4 = April–June
    """

    year_code = int(
        quarter_code[0:2]
    )

    quarter_number = int(
        quarter_code[-1]
    )

    year_start = (
        1900 + year_code
        if year_code >= 90
        else 2000 + year_code
    )

    quarter_starts = {
        1: (year_start, 7),
        2: (year_start, 10),
        3: (year_start + 1, 1),
        4: (year_start + 1, 4),
    }

    if quarter_number not in quarter_starts:
        raise ValueError(
            f"Invalid quarter code: {quarter_code}"
        )

    year, month = quarter_starts[
        quarter_number
    ]

    start = pd.Timestamp(
        year=year,
        month=month,
        day=1,
    )

    end = (
        start
        + pd.DateOffset(months=3)
        - pd.Timedelta(days=1)
    )

    return start, end


# -------------------------------------------------------------------
# 12. Cross-check quarter completion against sites_db
# -------------------------------------------------------------------

print("\n" + "#" * 70)
print("CROSS-CHECK — QUARTER FILE VS SITES_DB")
print("#" * 70)

sites_db_dates = sites_db.copy()

sites_db_dates[
    "DateOfIntervention/InitialCapture"
] = pd.to_datetime(
    sites_db_dates[
        "DateOfIntervention/InitialCapture"
    ],
    format="%Y%m%d",
    errors="coerce",
)


for segment_id, label in MATCHED_CYCLING_SEGMENTS.items():

    segment_rows = qtr.loc[
        qtr["STREET_SEGMENT_ID"] == segment_id
    ]

    candidate_quarters = (
        segment_rows.loc[
            segment_rows["Baseline"] == 0,
            "QUARTER",
        ]
        .dropna()
        .astype(str)
        .tolist()
    )

    sites_rows = sites_db_dates.loc[
        (
            sites_db_dates["StreetSegmentID"]
            == segment_id
        )
        & (
            sites_db_dates["Baseline"]
            == "No"
        )
    ]

    matches = []

    for quarter in candidate_quarters:

        try:
            start, end = fy_quarter_to_range(
                quarter
            )
        except (ValueError, TypeError):
            continue

        dates_in_range = sites_rows.loc[
            (
                sites_rows[
                    "DateOfIntervention/InitialCapture"
                ]
                >= start
            )
            & (
                sites_rows[
                    "DateOfIntervention/InitialCapture"
                ]
                <= end
            )
        ]

        for date in dates_in_range[
            "DateOfIntervention/InitialCapture"
        ].dropna():

            matches.append(
                (
                    quarter,
                    date.date(),
                )
            )

    if matches:
        status = (
            "CONSISTENT — matching sites_db date(s) found"
        )
    else:
        status = (
            "NO matching sites_db date found"
        )

    print(
        f"Segment {segment_id:>6} | "
        f"{label:<32} | "
        f"{status}: {matches}"
    )


# -------------------------------------------------------------------
# 13. Headline data-quality numbers
# -------------------------------------------------------------------

total_blanks_before = (
    qtr["InterventionType"]
    .isna()
    .sum()
)

total_blanks_after = (
    qtr_filled["InterventionType"]
    .isna()
    .sum()
)

matched_duplicate_segments = [
    segment_id
    for segment_id in MATCHED_CYCLING_SEGMENTS
    if segment_id in problem_segments
]


print("\n" + "#" * 70)
print("HEADLINE NUMBERS")
print("#" * 70)

print(
    "- InterventionType blank cells before fill:",
    total_blanks_before,
)

print(
    "- InterventionType blank cells after fill:",
    total_blanks_after,
)

print(
    "- Segments with genuine duplicate/conflicting quarter rows:",
    len(problem_segments),
    "->",
    problem_segments,
)

print(
    "- Segments with multi-SiteID mapping issues:",
    len(multi_site_segments),
    "->",
    multi_site_segments,
)

print(
    "- Matched cycling segments with duplicate-row issues:",
    matched_duplicate_segments
    if matched_duplicate_segments
    else "none",
)


# -------------------------------------------------------------------
# Final summary
# -------------------------------------------------------------------

print(
    """
Analysis complete.

This check:
- applied the PO-recommended forward/backward fill;
- reviewed Wellington segments 5881, 5882 and 5883;
- identified duplicate/conflicting quarter records;
- separated multi-SiteID mapping issues;
- reviewed the five matched cycling segments; and
- cross-checked candidate completion quarters against sites_db dates.

Use the printed intervention summaries and cross-check results when deciding
which intervention period should be used for the cycling before/after analysis.
"""
)