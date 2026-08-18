"""
Selects candidate Strand-2 (imagery) pilot streets: treatment segments with a
single clean is_under_construction 0->1->0 transition, protected-bike-lane
type, outside the 4 sensor-covered CBD streets (William/La Trobe/Peel/Exhibition).

Used once to choose the two pilot segments: 9168 (Elizabeth St, Richmond) and
10838 (Moorabool St, South Geelong). Kept for the record of why those two were
picked, per IV's reproducibility requirement.
"""
import pandas as pd

BASE = r"C:\Users\erteo\Desktop\26T2\SIT378 - Project B"

SENSOR_STREETS = {"WILLIAM STREET", "LA TROBE STREET", "PEEL STREET", "EXHIBITION STREET"}


def decode_quarter(q: str) -> pd.Timestamp:
    """Decode IV's financial-year quarter code, e.g. '1819Q1' -> 2018-07-01."""
    y1 = int(q[:2])
    century = 1900 if y1 >= 90 else 2000
    fy_start = century + y1
    qn = int(q[-1])
    cal_year = fy_start if qn <= 2 else fy_start + 1
    month = {1: 7, 2: 10, 3: 1, 4: 4}[qn]
    return pd.Timestamp(year=cal_year, month=month, day=1)


def find_candidates() -> pd.DataFrame:
    spatial = pd.read_csv(BASE + r"\street_spatial.csv")
    qtr = pd.read_csv(BASE + r"\street_segment_qtr_attributes.csv")
    qtr["q_date"] = qtr["QUARTER"].apply(decode_quarter)
    qtr = qtr.sort_values(["STREET_SEGMENT_ID", "q_date"])

    treatment = spatial[spatial["treatment_or_control"] == "treatment"]
    treatment = treatment[~treatment["street_name"].isin(SENSOR_STREETS)]
    treatment_ids = set(treatment["street_segment_id"])

    results = []
    for seg_id, grp in qtr.groupby("STREET_SEGMENT_ID"):
        if seg_id not in treatment_ids:
            continue
        flags = grp["is_under_construction"].values
        dates = grp["q_date"].values
        starts = [dates[i] for i in range(1, len(flags)) if flags[i - 1] == 0 and flags[i] == 1]
        ends = [dates[i] for i in range(1, len(flags)) if flags[i - 1] == 1 and flags[i] == 0]
        if len(starts) == 1 and len(ends) >= 1:
            row = treatment[treatment["street_segment_id"] == seg_id].iloc[0]
            results.append({
                "street_segment_id": seg_id,
                "street_name": row["street_name"],
                "suburb": row["suburb"],
                "lga": row["lga"],
                "intervention_type": row["intervention_type"],
                "cbd": row["cbd"], "metro": row["metro"], "regional": row["regional"],
                "construction_start": pd.Timestamp(starts[0]).date(),
                "construction_end": pd.Timestamp(ends[0]).date(),
            })

    res = pd.DataFrame(results)
    return res[res["intervention_type"].str.contains("bike", case=False, na=False)]


if __name__ == "__main__":
    candidates = find_candidates()
    for loc in ("cbd", "metro", "regional"):
        sub = candidates[candidates[loc] == 1].sort_values("construction_start")
        print(f"--- {loc.upper()} ({len(sub)} candidates) ---")
        print(sub.to_string(index=False))
        print()
