"""
03 — Bike lane / on-street parking buffer overlap analysis.

Identifies which study segments have protected bike lane infrastructure physically
coincident with kerbside parking, and estimates the parking capacity at risk.

Important: street_spatial_study_area.gpkg ("buffered_full") is a ~250 m CATCHMENT
buffer for surrounding-street analysis. It is NOT a kerb buffer. Kerb-scale buffers
are generated here from the centrelines at BUFFER_KERB / BUFFER_ADJACENT.

Inputs
    streets_spatial.gpkg                  315 study segments, EPSG:7899
    sites_db.csv                          per-site parking capacity + format (cp1252)
    Bicycle Infrastructure Network        data.vic — download as GeoJSON/SHP into data/raw/
        https://discover.data.vic.gov.au/dataset/bicycle-infrastructure-network
        Filter: InfraType == "Protected bike lane (on-road)"

Known data quality exception (raised by IV):
    Gheringhap Street, Geelong is mis-tagged "Shared Use Path" and is force-corrected
    to a protected bike lane below. See GHERINGHAP_FIX.

Outputs
    outputs/segment_overlap.csv        per-segment overlap length + spaces at risk
    outputs/segment_kerb_capacity.csv  kerb capacity estimates (runs without the BIN)

Run:  python analysis/src/03_bikelane_parking_overlap.py [--bin data/raw/bin.geojson]
"""
import argparse
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as C

GHERINGHAP_FIX = {"street_name_contains": "GHERINGHAP", "set_infratype": "Protected bike lane (on-road)"}
PROTECTED = "Protected bike lane (on-road)"


def norm_sid(s):
    return pd.to_numeric(s, errors="coerce").astype("Int64").astype(str)


def load_streets() -> gpd.GeoDataFrame:
    st = gpd.read_file(C.STREETS_GPKG, layer=C.STREETS_LAYER).to_crs(C.CRS_PROJECT)
    st["sid"] = norm_sid(st["street_segment_id"])
    st["segment_length_m"] = st.length
    return st


def kerb_capacity(st: gpd.GeoDataFrame) -> pd.DataFrame:
    """Grattan Appendix D style kerb-length -> spaces conversion, calibrated on sites_db."""
    sites = pd.read_csv(C.SITES_DB_CSV, dtype=str, encoding="cp1252")
    sites["sid"] = norm_sid(sites["StreetSegmentID"])
    sites["cap_reported"] = pd.to_numeric(
        sites["StreetInScopeOnStreetParkingCapacity"], errors="coerce"
    )
    agg = (
        sites.groupby("sid")
        .agg(
            cap_reported=("cap_reported", "median"),
            parking_format=("StreetInScopeParkingFormat", lambda x: x.mode().iat[0] if len(x.mode()) else pd.NA),
            has_parking=("StreetInScopeOnStreetParking", lambda x: x.mode().iat[0] if len(x.mode()) else pd.NA),
        )
        .reset_index()
    )

    df = st.drop(columns="geometry").merge(agg, on="sid", how="left")
    df["kerb_length_m"] = df["segment_length_m"] * 2  # both sides
    m_per_space = df["parking_format"].map(
        {"Parallel": C.METRES_PER_PARALLEL_SPACE,
         "Angled": C.METRES_PER_ANGLED_SPACE,
         "Mixed": (C.METRES_PER_PARALLEL_SPACE + C.METRES_PER_ANGLED_SPACE) / 2}
    ).fillna(C.METRES_PER_PARALLEL_SPACE)
    df["cap_geometric"] = df["kerb_length_m"] / m_per_space

    # Calibration factor: reported capacity is lower than raw geometry because of
    # driveways, hydrants, clearways, loading zones. Fit one global ratio.
    both = df.dropna(subset=["cap_reported"])
    k = (both["cap_reported"] / both["cap_geometric"]).median()
    df["obstruction_factor"] = k
    df["cap_estimated"] = df["cap_geometric"] * k
    df["cap_best"] = df["cap_reported"].fillna(df["cap_estimated"])
    print(f"obstruction factor (reported/geometric, median): {k:.3f}  n={len(both)}")
    return df


def overlap(st: gpd.GeoDataFrame, bin_path: Path, cap: pd.DataFrame) -> pd.DataFrame:
    bl = gpd.read_file(bin_path).to_crs(C.CRS_PROJECT)

    infra_col = next((c for c in bl.columns if c.lower() in ("infratype", "infra_type")), None)
    name_col = next((c for c in bl.columns if "name" in c.lower()), None)
    if infra_col and name_col:
        fix = bl[name_col].astype(str).str.upper().str.contains(GHERINGHAP_FIX["street_name_contains"])
        n = int(fix.sum())
        bl.loc[fix, infra_col] = GHERINGHAP_FIX["set_infratype"]
        print(f"Gheringhap St correction applied to {n} feature(s)")
    if infra_col:
        bl = bl[bl[infra_col] == PROTECTED]
    print(f"protected on-road bike lane features: {len(bl)}")

    rows = []
    for dist, label in ((C.BUFFER_KERB, "kerb"), (C.BUFFER_ADJACENT, "adjacent")):
        buf = bl.copy()
        buf["geometry"] = buf.buffer(dist)
        buf = gpd.GeoDataFrame(geometry=[buf.union_all()], crs=C.CRS_PROJECT)
        clipped = gpd.overlay(st[["sid", "geometry"]], buf, how="intersection")
        clipped["overlap_m"] = clipped.length
        g = clipped.groupby("sid", as_index=False)["overlap_m"].sum()
        g["buffer"] = label
        rows.append(g)

    ov = pd.concat(rows).pivot(index="sid", columns="buffer", values="overlap_m").reset_index()
    ov = ov.rename(columns={"kerb": "overlap_kerb_m", "adjacent": "overlap_adjacent_m"}).fillna(0)

    out = cap.merge(ov, on="sid", how="left").fillna({"overlap_kerb_m": 0, "overlap_adjacent_m": 0})
    out["overlap_share"] = (out["overlap_kerb_m"] / out["segment_length_m"]).clip(0, 1)
    out["spaces_at_risk"] = out["cap_best"] * out["overlap_share"]
    out["impact_zone"] = out["overlap_share"] > 0.25
    return out.sort_values("spaces_at_risk", ascending=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", type=Path, default=None, help="Bicycle Infrastructure Network file")
    a = ap.parse_args()

    st = load_streets()
    cap = kerb_capacity(st)
    cap.to_csv(C.OUTPUTS / "segment_kerb_capacity.csv", index=False)
    print(f"total kerb: {cap.kerb_length_m.sum()/1000:.1f} km   "
          f"estimated capacity: {cap.cap_best.sum():,.0f} spaces")
    print("wrote:", C.OUTPUTS / "segment_kerb_capacity.csv")

    if a.bin and a.bin.exists():
        res = overlap(st, a.bin, cap)
        res.drop(columns=[c for c in res.columns if c == "geometry"]).to_csv(
            C.OUTPUTS / "segment_overlap.csv", index=False
        )
        print(res.head(20)[["street_name", "sid", "overlap_share", "cap_best", "spaces_at_risk"]].to_string(index=False))
        print("wrote:", C.OUTPUTS / "segment_overlap.csv")
    else:
        print("\n[skipped overlap] Download the Bicycle Infrastructure Network to data/raw/ "
              "and re-run with --bin data/raw/<file>.geojson")


if __name__ == "__main__":
    main()
