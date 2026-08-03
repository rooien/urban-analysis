"""
Shared Configuration Module

This module loads 'config.yaml' from the project root and exposes all
configuration parameters as module-level constants. This ensures
consistency across all ingestion scripts and the backend API.
"""

import os
from typing import Any

import yaml

# Project Root is two levels up from src/config.py
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.yaml")


def load_config() -> dict[str, Any]:
    """
    Loads the YAML configuration file.

    Returns:
        dict[str, Any]: The parsed YAML configuration as a dictionary.

    Raises:
        FileNotFoundError: If config.yaml is missing.
    """
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(
            f"Config file not found at {CONFIG_PATH}. "
            "Please ensure config.yaml exists at the project root."
        )
    with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


CONFIG = load_config()

# Ports
BACKEND_PORT = CONFIG["ports"]["backend"]
FRONTEND_PORT = CONFIG["ports"]["frontend"]

# Data Sources
BIKE_URL = CONFIG["data_sources"]["bicycle_network"]
BAYS_URL = CONFIG["data_sources"]["parking_bays"]
SUBURBS_URL = CONFIG["data_sources"]["suburbs"]

# Paths
# Note: os.path.join will ignore ROOT_DIR if the path in config is already absolute,
# allowing for flexible local path overrides while maintaining relative defaults.
DATA_DIR = os.path.join(ROOT_DIR, CONFIG["paths"]["data_dir"])
RAW_DIR = os.path.join(ROOT_DIR, CONFIG["paths"]["raw_dir"])
PROCESSED_DIR = os.path.join(ROOT_DIR, CONFIG["paths"]["processed_dir"])
DB_PATH = os.path.join(ROOT_DIR, CONFIG["paths"]["database"])

# Processing: Buffers
BUFFER_BIKE_LANES = CONFIG["processing"]["buffers"]["bike_lanes_meters"]
BUFFER_PARKING_BAYS = CONFIG["processing"]["buffers"]["parking_bays_meters"]

# Processing: Spatial
EPSG_PROJECTED = CONFIG["processing"]["spatial"]["epsg_projected"]
EPSG_WGS84 = CONFIG["processing"]["spatial"]["epsg_wgs84"]

# Processing: Historical (legacy PoC fixed windows)
BASELINE_YEAR = CONFIG["processing"]["historical"]["baseline"]["year"]
BASELINE_MONTHS = CONFIG["processing"]["historical"]["baseline"]["months"]
POST_YEAR = CONFIG["processing"]["historical"]["post_intervention"]["year"]
POST_MONTHS = CONFIG["processing"]["historical"]["post_intervention"]["months"]

# Site-specific parking windows
SITE_WINDOW_MONTHS = CONFIG["processing"]["site_windows"]["window_months"]
SITES_DB_PATH = os.path.join(ROOT_DIR, CONFIG["processing"]["site_windows"]["sites_db"])
PARKING_YEARS = CONFIG["processing"]["site_windows"]["parking_years"]
