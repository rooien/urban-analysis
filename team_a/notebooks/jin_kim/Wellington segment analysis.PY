"""
USIA Team A (Cycling) - Wellington St / segment data-quality re-check

What this script does:
1. Loads sites_db.csv and street_segment_qtr_attributes.csv
2. Applies the PO's recommended fix (forward-fill then backward-fill,
   grouped by STREET_SEGMENT_ID) to InterventionType / InterventionSummary
3. Shows Wellington St segments 5881 / 5882 / 5883 before and after the fill,
   and reads off the completion quarter using Baseline == 0
4. Finds the segments where fill will NOT give a clean answer, because the
   same quarter has two conflicting rows (the real data-quality issue)
5. Prints a summary for our 5 matched cycling segments (5881, 10838, 8218,
   8221, 9801)

Run with: python3 wellington_segment_analysis.py
Expects sites_db.csv and street_segment_qtr_attributes.csv in the same folder
(or edit the paths below).
"""

import pandas as pd
from pathlib import Path

pd.set_option("display.width", 160)
pd.set_option("display.max_rows", 200)

# Resolve paths relative to THIS script's folder, not the terminal's current
# working directory - this is what was causing FileNotFoundError when running
# from VS Code with a different cwd (e.g. the VS Code install folder).
SCRIPT_DIR = Path(__file__).resolve().parent
SITES_DB_PATH = SCRIPT_DIR / "sites_db.csv"
QTR_ATTR_PATH = SCRIPT_DIR / "street_segment_qtr_attributes.csv"

# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
sites_db = pd.read_csv(SITES_DB_PATH, encoding="latin1")
qtr = pd.read_csv(QTR_ATTR_PATH)

# Treat empty strings as real missing values
qtr["InterventionType"] = qtr["InterventionType"].replace("", pd.NA)
qtr["InterventionSummary"] = qtr["InterventionSummary"].replace("", pd.NA)

# Quarters are strings like "1415Q3" - not naturally sortable, but the file
# is already stored in chronological order per segment, so we sort by the
# original row order within each segment instead of parsing the label.
qtr = qtr.sort_index()

# ---------------------------------------------------------------------------
# 2. Apply the PO's fix: forward-fill then backward-fill, per segment
# ---------------------------------------------------------------------------
qtr_filled = qtr.copy()
fill_cols = ["InterventionType", "InterventionSummary"]

qtr_filled[fill_cols] = (
    qtr_filled.groupby("STREET_SEGMENT_ID")[fill_cols]
    .apply(lambda g: g.ffill().bfill())
    .reset_index(level=0, drop=True)
)

# ---------------------------------------------------------------------------
# 3. Wellington St: segments 5881, 5882, 5883 - before vs after fill
# ---------------------------------------------------------------------------
def show_segment(seg_id, label):
    print(f"\n=== Segment {seg_id} ({label}) ===")
    before = qtr[qtr["STREET_SEGMENT_ID"] == seg_id]
    after = qtr_filled[qtr_filled["STREET_SEGMENT_ID"] == seg_id]

    known = before.loc[before["InterventionType"].notna(),
                        ["QUARTER", "Baseline", "InterventionType", "InterventionSummary",
                         "is_under_construction", "other_major_construction"]]
    print("Known (non-blank) rows before fill:")
    print(known.to_string(index=False))

    # Baseline == 0 can appear at MORE THAN ONE quarter per segment (e.g. an
    # initial protected-lane completion, then a later re-confirmation or a
    # separate later upgrade). Do not assume the first one is "the"
    # completion quarter - list them all with their InterventionSummary so
    # the actual intervention can be read off, not guessed.
    candidates = before.loc[before["Baseline"] == 0,
                             ["QUARTER", "InterventionSummary"]]
    if len(candidates):
        print("Baseline == 0 candidate quarters (check InterventionSummary, don't assume the first row):")
        print(candidates.to_string(index=False))
    else:
        print("No Baseline == 0 quarter found for this segment.")

    remaining_blanks = after["InterventionType"].isna().sum()
    print(f"Blank InterventionType cells remaining AFTER forward+backward fill: {remaining_blanks}")


print("#" * 70)
print("WELLINGTON ST SEGMENTS")
print("#" * 70)
show_segment(5881, "matched to counter 32493, ~6-7m away")
show_segment(5882, "~67-121m from counter 32493")
show_segment(5883, "~309-363m from counter 32493")

# ---------------------------------------------------------------------------
# 4. Real data-quality issue: duplicate/conflicting rows in the same quarter
#    (this is what forward/backward fill can NOT resolve cleanly)
# ---------------------------------------------------------------------------
print("\n" + "#" * 70)
print("SEGMENTS WITH DUPLICATE / CONFLICTING VALUES IN THE SAME QUARTER")
print("#" * 70)

dup_mask = qtr.duplicated(subset=["STREET_SEGMENT_ID", "QUARTER"], keep=False)
dupes = qtr[dup_mask].sort_values(["STREET_SEGMENT_ID", "QUARTER"])

all_dupe_segments = sorted(dupes["STREET_SEGMENT_ID"].unique())

# Segment(s) where more than one SiteID maps to the same STREET_SEGMENT_ID -
# this is a DIFFERENT problem (a mapping error) from a genuine conflicting
# duplicate entry, so it's reported separately rather than folded into the
# same list.
multi_site = qtr.groupby("STREET_SEGMENT_ID")["SiteID"].nunique()
multi_site_segments = sorted(multi_site[multi_site > 1].index)

problem_segments = sorted(set(all_dupe_segments) - set(multi_site_segments))
print(f"\n{len(problem_segments)} segments have a genuine duplicate/conflicting quarter row:")
print(problem_segments)

print("\nExample conflicting rows:")
print(dupes[dupes["STREET_SEGMENT_ID"].isin(problem_segments)]
      [["STREET_SEGMENT_ID", "QUARTER", "Baseline", "InterventionType", "InterventionSummary"]]
      .head(20).to_string(index=False))

print(f"\nSegment(s) with more than one SiteID mapped to it (separate issue - mapping error, "
      f"not a value conflict): {multi_site_segments}")

# ---------------------------------------------------------------------------
# 5. Summary for our 5 matched cycling segments
# ---------------------------------------------------------------------------
print("\n" + "#" * 70)
print("SUMMARY: OUR 5 MATCHED CYCLING SEGMENTS")
print("#" * 70)

our_segments = {
    5881: "Wellington St (counter 32493)",
    10838: "Moorabool St (counter 34687)",
    8218: "Heidelberg Rd (counter 40004)",
    8221: "Heidelberg Rd (counter 40005)",
    9801: "Albert St (counter 9077)",
}

for seg_id, label in our_segments.items():
    sub = qtr[qtr["STREET_SEGMENT_ID"] == seg_id]
    completion_qs = sub.loc[sub["Baseline"] == 0, "QUARTER"].tolist()
    has_dupe = seg_id in problem_segments
    print(f"Segment {seg_id:>6} | {label:<32} | Baseline==0 quarters: {completion_qs} | "
          f"duplicate-row issue: {'YES' if has_dupe else 'no'}")

# ---------------------------------------------------------------------------
# 6. Auto-generated notes (derived from the actual results above, not typed
#    in by hand - if the data changes, these lines change with it)
# ---------------------------------------------------------------------------
multi_candidate_segments = [
    seg_id for seg_id in our_segments
    if (qtr.loc[qtr["STREET_SEGMENT_ID"] == seg_id, "Baseline"] == 0).sum() > 1
]
if multi_candidate_segments:
    example_id = multi_candidate_segments[0]
    example_rows = qtr.loc[(qtr["STREET_SEGMENT_ID"] == example_id) & (qtr["Baseline"] == 0),
                            ["QUARTER", "InterventionSummary"]]
    print(f"\nNote: {len(multi_candidate_segments)} of our matched segments "
          f"{multi_candidate_segments} have more than one Baseline == 0 quarter - "
          f"don't assume the first one is the real completion date. Check "
          f"InterventionSummary per candidate, e.g. segment {example_id}:")
    print(example_rows.to_string(index=False))
else:
    print("\nNote: none of our matched segments have more than one Baseline == 0 "
          "quarter, so completion is unambiguous for all 5.")


def fy_quarter_to_range(qcode: str):
    """Convert a code like '1516Q1' to a (start, end) date range.
    Australian FY: Q1=Jul-Sep, Q2=Oct-Dec, Q3=Jan-Mar(+1yr), Q4=Apr-Jun(+1yr)."""
    yy_start = int(qcode[0:2])
    q = int(qcode[-1])
    year_start = (1900 if yy_start >= 90 else 2000) + yy_start
    q_starts = {1: (year_start, 7), 2: (year_start, 10), 3: (year_start + 1, 1), 4: (year_start + 1, 4)}
    y, m = q_starts[q]
    start = pd.Timestamp(year=y, month=m, day=1)
    end = start + pd.DateOffset(months=3) - pd.Timedelta(days=1)
    return start, end


print("\n" + "#" * 70)
print("AUTO-CHECK: does each segment's qtr-file completion quarter actually")
print("contain a matching sites_db.csv completion date?")
print("#" * 70)

sites_db_dates = sites_db.copy()
sites_db_dates["DateOfIntervention/InitialCapture"] = pd.to_datetime(
    sites_db_dates["DateOfIntervention/InitialCapture"], format="%Y%m%d", errors="coerce"
)

for seg_id, label in our_segments.items():
    seg_rows = qtr[qtr["STREET_SEGMENT_ID"] == seg_id]
    candidate_quarters = seg_rows.loc[seg_rows["Baseline"] == 0, "QUARTER"].tolist()
    sdb_rows = sites_db_dates[
        (sites_db_dates["StreetSegmentID"] == seg_id) & (sites_db_dates["Baseline"] == "No")
    ]
    matches = []
    for q in candidate_quarters:
        start, end = fy_quarter_to_range(q)
        in_range = sdb_rows[
            (sdb_rows["DateOfIntervention/InitialCapture"] >= start)
            & (sdb_rows["DateOfIntervention/InitialCapture"] <= end)
        ]
        for d in in_range["DateOfIntervention/InitialCapture"]:
            matches.append((q, d.date()))
    status = "CONSISTENT - matching sites_db.csv date(s) found" if matches else "NO matching sites_db.csv date found"
    print(f"Segment {seg_id:>6} | {label:<32} | {status}: {matches}")

# ---------------------------------------------------------------------------
# 7. Auto-generated headline numbers (no hand-typed conclusion text)
# ---------------------------------------------------------------------------
total_blanks_before = qtr["InterventionType"].isna().sum()
total_blanks_after = qtr_filled["InterventionType"].isna().sum()

print("\n" + "#" * 70)
print("HEADLINE NUMBERS (computed, not hand-typed)")
print("#" * 70)
print(f"- InterventionType blank cells, whole file, before fill: {total_blanks_before}")
print(f"- InterventionType blank cells, whole file, after forward+backward fill: {total_blanks_after}")
print(f"- Segments with a genuine duplicate/conflicting quarter row: {len(problem_segments)} -> {problem_segments}")
print(f"- Segments with a multi-SiteID mapping error: {len(multi_site_segments)} -> {multi_site_segments}")
print(f"- Of our 5 matched segments, segments with a duplicate-row issue: "
      f"{[s for s in our_segments if s in problem_segments] or 'none'}")