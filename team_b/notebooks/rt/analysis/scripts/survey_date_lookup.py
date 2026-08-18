"""
Merges Nearmap coverage-API results from both ends of a street segment,
decodes each survey date into IV's financial-year quarter format, and
classifies each date as before / during-construction / after relative to
the segment's construction window.

The Nearmap API responses themselves are fetched by hand in PowerShell
(see team_b/notebooks/rt/analysis/docs/method_and_blockers.md for why: the
coverage API needs an API key that must never be pasted into chat/committed
code, so the fetch step is manual and only the merge/classify step is
scripted).
"""
import os
from datetime import date

import pandas as pd


def fy_quarter(d: date) -> str:
    """Convert a calendar date to IV's financial-year quarter code, e.g. 2020-04-28 -> '1920Q4'."""
    y, m = d.year, d.month
    if m in (4, 5, 6):
        fy_start, qn = y - 1, 4
    elif m in (7, 8, 9):
        fy_start, qn = y, 1
    elif m in (10, 11, 12):
        fy_start, qn = y, 2
    else:
        fy_start, qn = y - 1, 3
    return f"{str(fy_start)[-2:]}{str(fy_start + 1)[-2:]}Q{qn}"


def build_lookup(
    street_segment_id: int,
    street_name: str,
    end_a_dates: list[str],
    end_b_dates: list[str],
    construction_start: date,
    construction_end: date,
) -> pd.DataFrame:
    rows = []
    for ds in sorted(set(end_a_dates) | set(end_b_dates)):
        d = date.fromisoformat(ds)
        coverage = "both ends" if (ds in end_a_dates and ds in end_b_dates) else "End A only"
        if d < construction_start:
            period = "before"
        elif d < construction_end:
            period = "during construction (exclude)"
        else:
            period = "after"
        rows.append({
            "street_segment_id": street_segment_id,
            "street_name": street_name,
            "captureDate": ds,
            "day_of_week": d.strftime("%A"),
            "fy_quarter": fy_quarter(d),
            "period": period,
            "coverage": coverage,
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    # Elizabeth St, Richmond (segment 9168) pilot dates.
    end_a = ["2019-04-07", "2019-08-31", "2019-12-17", "2020-02-17", "2020-04-28", "2020-06-04",
             "2020-09-07", "2020-11-02", "2020-11-08", "2021-01-22", "2021-03-11", "2021-04-29",
             "2021-06-21", "2021-07-27", "2021-09-01", "2021-09-23", "2021-09-26"]
    end_b = ["2019-04-07", "2019-08-31", "2019-12-17", "2020-02-17", "2020-04-28", "2020-09-07",
             "2020-11-08", "2021-01-22", "2021-03-11", "2021-04-29", "2021-09-01", "2021-09-23",
             "2021-09-26"]

    df = build_lookup(9168, "ELIZABETH STREET", end_a, end_b, date(2020, 4, 1), date(2020, 10, 1))
    print(df.to_string(index=False))

    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "nearmap_survey_dates_pilot.csv")
    df.to_csv(out_path, index=False)
    print(f"\nWritten to {out_path}")
