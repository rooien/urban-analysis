"""Shared paths and constants for the USIA analysis pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJ = ROOT.parent

# --- source data (as delivered by IV) ---
SPATIAL_DIR = PROJ / "260724 street spatial files" / "260724 street spatial files"
STREETS_GPKG = SPATIAL_DIR / "streets_spatial.gpkg"
STREETS_LAYER = "street_list_spatial_updated"
STUDY_AREA_GPKG = SPATIAL_DIR / "street_spatial_study_area.gpkg"   # 250 m catchment buffer
STUDY_AREA_LAYER = "buffered_full"
ROAD_SEGMENTS_SHP = SPATIAL_DIR / "road_segments_15dec.shp"        # NOTE: EPSG:7855, not 7899

QTR_ATTRS_CSV = PROJ / "street_segment_qtr_attributes.csv"   # authoritative quarterly panel
SITES_DB_CSV = PROJ / "sites_db.csv"                         # consultant reference (cp1252!)
STREET_SPATIAL_CSV = PROJ / "street_spatial.csv"

# --- working dirs ---
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
for _d in (RAW, INTERIM, PROCESSED, OUTPUTS):
    _d.mkdir(parents=True, exist_ok=True)

# --- project constants ---
CRS_PROJECT = 7899        # GDA2020 / Vicgrid — analysis CRS for everything
CRS_ROAD_SEGMENTS = 7855  # GDA2020 / MGA zone 55 — road_segments_15dec.shp only
CRS_WGS84 = 4326          # CoM open data lat/lon

# City of Melbourne sensor archive coverage
SENSOR_START = "2011-01-01"
SENSOR_END = "2020-05-31"

# COVID regime boundaries (Victoria)
COVID_START = "2020-03-16"   # first major restrictions
COVID_END = "2022-04-22"     # last state-wide restrictions lifted

# Grattan "Wasted Space" Appendix D conversion
METRES_PER_PARALLEL_SPACE = 6.0    # incl. manoeuvring allowance
METRES_PER_ANGLED_SPACE = 3.0

# Buffer distances for bike-lane / parking overlap (metres, valid in 7899)
BUFFER_KERB = 5      # direct kerbside reallocation
BUFFER_ADJACENT = 20  # displacement onto adjacent kerb space
