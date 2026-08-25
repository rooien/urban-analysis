#!/usr/bin/env python3
"""
Victoria Urban Planning - Ingestion Pipeline Orchestrator (Team B)

Orchestrates all Stream B ingestion, spatial processing, weather telemetry,
aggregation, and validation steps sequentially.
"""

import os
import sys
import subprocess
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Use the current Python executable to ensure portability across environments
PYTHON_EXEC = sys.executable


def run_script(script_path: str, args: list = None) -> None:
    """
    Runs an ingestion python script using the current python executable.
    """
    if args is None:
        args = []
    
    cmd = [PYTHON_EXEC, script_path] + args
    script_name = os.path.basename(script_path)
    
    print("=" * 60)
    print(f"[*] Running {script_name} {' '.join(args)}...")
    print("=" * 60)
    
    start = time.time()
    result = subprocess.run(cmd, cwd=ROOT_DIR)
    duration = time.time() - start
    
    if result.returncode != 0:
        print(f"\n[E] {script_name} failed with exit code {result.returncode}.")
        sys.exit(result.returncode)
    
    print(f"\n[+] {script_name} completed successfully in {duration:.2f} seconds.\n")


def main() -> None:
    """
    Main execution function to orchestrate the pipeline.
    """
    print("=" * 60)
    print("      Victoria Urban Planning - Team B Ingestion Pipeline    ")
    print("=" * 60)
    print("This script runs the full end-to-end data pipeline to build")
    print("the DuckDB database for all supported streets and suburbs.")
    print("This includes downloading GeoJSON layers, filtering sensor events,")
    print("ingesting hourly weather and SCATS volumes, and running validations.\n")

    pipeline_start = time.time()

    # Step 1: Download Base GeoJSONs and Raw Archives
    run_script(os.path.join(ROOT_DIR, "team_b", "ingestion", "download_base_data.py"))

    # Step 2: Match Bike Lanes with Suburbs and Parking Bays
    run_script(os.path.join(ROOT_DIR, "team_b", "ingestion", "match_bike_lanes.py"))

    # Step 3: Extract and Filter Historical Events for 2013 and 2014
    run_script(os.path.join(ROOT_DIR, "team_b", "ingestion", "filter_supported_events.py"), ["2013"])
    run_script(os.path.join(ROOT_DIR, "team_b", "ingestion", "filter_supported_events.py"), ["2014"])

    # Step 4: Process Weather Telemetry (Open-Meteo Hourly Meteorological Data)
    run_script(os.path.join(ROOT_DIR, "team_b", "ingestion", "process_weather.py"))

    # Step 5: Process Traffic Volumes (SCATS & Vehicle Classification)
    run_script(os.path.join(ROOT_DIR, "team_b", "ingestion", "process_scats_traffic.py"))

    # Step 6: Aggregate Hourly Occupancy & Turnover across all supported blocks
    run_script(os.path.join(ROOT_DIR, "team_b", "ingestion", "aggregate_occupancy.py"))

    # Step 7: Assign Blocks to Bike Lanes, Calibrate Capacity, and Build Summary
    run_script(os.path.join(ROOT_DIR, "team_b", "ingestion", "match_bike_to_blocks.py"))

    # Step 8: Run Pipeline Validation & Generate Report
    run_script(os.path.join(ROOT_DIR, "team_b", "ingestion", "validate_pipeline.py"))

    total_duration = time.time() - pipeline_start
    mins = int(total_duration // 60)
    secs = int(total_duration % 60)

    print("=" * 60)
    print(" SUCCESS: Team B Ingestion Pipeline Completed Successfully!")
    print(f" Total Execution Time: {mins}m {secs}s")
    print(" The DuckDB database is now fully populated and ready for the app.")
    print(" Run 'python run_app.py' to start the dashboard.")
    print("=" * 60)


if __name__ == "__main__":
    main()
