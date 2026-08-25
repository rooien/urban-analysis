"""
Look up a segment's construction start/end from IV's authoritative quarterly
panel (street_segment_qtr_attributes.csv), by finding the is_under_construction
0->1 and 1->0 transitions.

Usage: python construction_window.py <street_segment_id>
"""
import sys
import pandas as pd

BASE = r"C:\Users\erteo\Desktop\26T2\SIT378 - Project B"


def decode_quarter(q: str) -> pd.Timestamp:
    """Decode IV's financial-year quarter code, e.g. '1819Q1' -> 2018-07-01."""
    y1 = int(q[:2])
    century = 1900 if y1 >= 90 else 2000
    fy_start = century + y1
    qn = int(q[-1])
    cal_year = fy_start if qn <= 2 else fy_start + 1
    month = {1: 7, 2: 10, 3: 1, 4: 4}[qn]
    return pd.Timestamp(year=cal_year, month=month, day=1)


def construction_window(segment_id: int) -> pd.DataFrame:
    qtr = pd.read_csv(BASE + r"\street_segment_qtr_attributes.csv")
    sub = qtr[qtr["STREET_SEGMENT_ID"] == segment_id].copy()
    assert len(sub) > 0, f"No quarterly rows found for segment {segment_id}"
    sub["q_date"] = sub["QUARTER"].apply(decode_quarter)
    return sub.sort_values("q_date")[
        ["QUARTER", "q_date", "is_under_construction", "InterventionType", "InterventionSummary"]
    ]


def get_construction_window(segment_id: int):
    """
    Returns (start_date, end_date) as date objects for the segment's single
    is_under_construction 0->1 / 1->0 transition pair, or None if the segment
    has zero or more than one such transition (e.g. never built on, an
    ambiguous multi-phase history, or -- as with 11 known treatment segments
    IV has already confirmed -- no intervention date recorded at all) --
    callers should skip and log those rather than guess.
    """
    segment_id = int(segment_id)  # gpkg stores this as float64; qtr CSV as int
    try:
        window = construction_window(segment_id)
    except AssertionError:
        return None
    flags = window["is_under_construction"].values
    dates = window["q_date"].values
    starts = [dates[i] for i in range(1, len(flags)) if flags[i - 1] == 0 and flags[i] == 1]
    ends = [dates[i] for i in range(1, len(flags)) if flags[i - 1] == 1 and flags[i] == 0]
    if len(starts) != 1 or len(ends) != 1:
        return None
    return pd.Timestamp(starts[0]).date(), pd.Timestamp(ends[0]).date()


if __name__ == "__main__":
    seg_id = int(sys.argv[1]) if len(sys.argv) > 1 else 9168
    window = construction_window(seg_id)
    print(window.to_string(index=False))
    print("\nget_construction_window():", get_construction_window(seg_id))
