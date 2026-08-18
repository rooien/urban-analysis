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


if __name__ == "__main__":
    seg_id = int(sys.argv[1]) if len(sys.argv) > 1 else 9168
    window = construction_window(seg_id)
    print(window.to_string(index=False))
