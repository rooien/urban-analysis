"""
01 — Build the authoritative intervention-date table.

Source: street_segment_qtr_attributes.csv (IV's quarterly panel, 1999-00 Q2 -> 2025-26 Q2).
QUARTER is an Australian FINANCIAL-year code, not a calendar year:
    "1819Q1" = FY2018-19, quarter 1 = Jul-Sep 2018
    Q1 = Jul-Sep (y1) | Q2 = Oct-Dec (y1) | Q3 = Jan-Mar (y1+1) | Q4 = Apr-Jun (y1+1)
"9900Q2" is FY1999-00 -> Oct 1999. The two-digit year rolls at 90.

Outputs
    data/processed/intervention_dates.csv     one row per study segment
    data/processed/qtr_attributes_filled.csv  panel with InterventionType/Summary down-filled

Run:  python analysis/src/01_build_intervention_dates.py
"""
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as C


def quarter_to_date(code: str) -> pd.Timestamp:
    """'1819Q1' -> Timestamp('2018-07-01'). Returns start of the quarter."""
    fy, qn = code[:4], int(code[5])
    y1 = int(fy[:2])
    y1 += 1900 if y1 >= 90 else 2000
    month = {1: 7, 2: 10, 3: 1, 4: 4}[qn]
    year = y1 if qn <= 2 else y1 + 1
    return pd.Timestamp(year, month, 1)


def norm_sid(s: pd.Series) -> pd.Series:
    """Canonical street_segment_id: float/int/str -> zero-padding-free string.

    The GeoPackage stores it as float64, the buffer layer as object, the quarterly
    panel as int. Cast through Int64 so 211.0 and '211' both land on '211'.
    """
    return pd.to_numeric(s, errors="coerce").astype("Int64").astype(str)


def main():
    # ---- quarterly panel ----
    q = pd.read_csv(C.QTR_ATTRS_CSV, index_col=0, dtype=str)
    q["sid"] = norm_sid(q["STREET_SEGMENT_ID"])
    q["qdate"] = q["QUARTER"].map(quarter_to_date)
    q = q.sort_values(["sid", "qdate"])

    # Down-fill: IV populate InterventionType/Summary only in the quarter of change.
    # Forward-fill within segment so every subsequent quarter carries the state.
    for col in ("InterventionType", "InterventionSummary"):
        q[col] = q[col].replace("", pd.NA)
        q[col + "_filled"] = q.groupby("sid")[col].ffill()

    q.to_csv(C.PROCESSED / "qtr_attributes_filled.csv", index=False)

    # ---- first real intervention per segment ----
    treated = q[q["InterventionType"].notna() & (q["InterventionType"] != "Control")]
    first = (
        treated.groupby("sid")
        .agg(
            intervention_quarter=("QUARTER", "first"),
            intervention_date=("qdate", "first"),
            intervention_type_iv=("InterventionType", "first"),
            intervention_summary=("InterventionSummary", "first"),
        )
        .reset_index()
    )

    # ---- join to the study-area street list ----
    st = gpd.read_file(C.STREETS_GPKG, layer=C.STREETS_LAYER)
    st["sid"] = norm_sid(st["street_segment_id"])
    st["segment_length_m"] = st.to_crs(C.CRS_PROJECT).length

    out = st.drop(columns="geometry").merge(first, on="sid", how="left")

    # ---- usability flags for the sensor strand ----
    sensor_end = pd.Timestamp(C.SENSOR_END)
    sensor_start = pd.Timestamp(C.SENSOR_START)
    d = out["intervention_date"]
    out["in_sensor_window"] = d.between(sensor_start, sensor_end)
    out["sensor_pre_days"] = (d - sensor_start).dt.days.clip(lower=0)
    out["sensor_post_days"] = (sensor_end - d).dt.days.clip(lower=0)
    out["covid_contaminated_post"] = d.between(
        pd.Timestamp(C.COVID_START) - pd.Timedelta(days=365), sensor_end
    )
    out["sensor_usable"] = (
        (out["cbd"] == 1)
        & out["in_sensor_window"]
        & (out["sensor_pre_days"] >= 180)
        & (out["sensor_post_days"] >= 180)
    )
    out["missing_intervention_date"] = (
        out["treatment_or_control"].eq("treatment") & d.isna()
    )

    out.to_csv(C.PROCESSED / "intervention_dates.csv", index=False)

    # ---- console summary ----
    tr = out[out["treatment_or_control"] == "treatment"]
    print(f"segments: {len(out)}  treatment: {len(tr)}  control: {len(out)-len(tr)}")
    print(f"treatment missing a date: {int(out['missing_intervention_date'].sum())}")
    print(f"  -> {out.loc[out.missing_intervention_date, 'sid'].tolist()}")
    print(f"\nCBD segments: {int((out['cbd']==1).sum())}")
    print(f"sensor-usable before/after segments: {int(out['sensor_usable'].sum())}")
    print(
        out.loc[out.sensor_usable, ["street_name", "sid", "intervention_date"]].to_string(
            index=False
        )
    )
    print("\nwrote:", C.PROCESSED / "intervention_dates.csv")


if __name__ == "__main__":
    main()
