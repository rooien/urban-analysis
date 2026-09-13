"""
Validate Pipeline Script

Automated Data Quality Validation Suite to run post-ingestion assertions
and generate a validation report markdown file in data/processed/.
Validates blocks_summary, block_geometries, hourly_occupancy, traffic_volumes, and weather_hourly.
"""

import sys
import os
import duckdb

# Ensure project root is in PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import DB_PATH, PROCESSED_DIR


def run_assertions(con: duckdb.DuckDBPyConnection) -> dict:
    """
    Executes automated data quality validation queries across all database tables.
    """
    stats = {}
    
    # 1. Row counts
    stats["blocks_summary_count"] = con.execute("SELECT count(*) FROM blocks_summary").fetchone()[0]
    stats["block_geometries_count"] = con.execute("SELECT count(*) FROM block_geometries").fetchone()[0]
    stats["hourly_occupancy_count"] = con.execute("SELECT count(*) FROM hourly_occupancy").fetchone()[0]
    stats["traffic_volumes_count"] = con.execute("SELECT count(*) FROM traffic_volumes").fetchone()[0]
    
    # Check if weather_hourly table exists
    has_weather = con.execute("""
        SELECT count(*) FROM information_schema.tables WHERE table_name = 'weather_hourly'
    """).fetchone()[0] > 0
    stats["has_weather"] = has_weather
    stats["weather_hourly_count"] = con.execute("SELECT count(*) FROM weather_hourly").fetchone()[0] if has_weather else 0
    
    # 2. Check for null keys in summary and occupancy
    null_summary_keys = con.execute("""
        SELECT count(*) FROM blocks_summary 
        WHERE suburb IS NULL OR street_name IS NULL OR block_desc IS NULL
    """).fetchone()[0]
    stats["null_summary_keys"] = null_summary_keys
    
    null_occupancy_keys = con.execute("""
        SELECT count(*) FROM hourly_occupancy 
        WHERE suburb IS NULL OR street_name IS NULL OR block_desc IS NULL OR hr IS NULL
    """).fetchone()[0]
    stats["null_occupancy_keys"] = null_occupancy_keys
    
    # 3. Check occupancy bounds [0, 1]
    out_of_bounds_occ = con.execute("""
        SELECT count(*) FROM hourly_occupancy 
        WHERE occupancy_rate < 0.0 OR occupancy_rate > 1.0
    """).fetchone()[0]
    stats["out_of_bounds_occ"] = out_of_bounds_occ
    
    # 4. Check negative traffic volumes or invalid saturations
    invalid_traffic = con.execute("""
        SELECT count(*) FROM traffic_volumes 
        WHERE traffic_volume < 0 OR degree_of_saturation < 0.0 OR degree_of_saturation > 1.0
    """).fetchone()[0]
    stats["invalid_traffic"] = invalid_traffic
    
    # 5. Check weather bounds (-10°C to 55°C, precip >= 0)
    if has_weather and stats["weather_hourly_count"] > 0:
        invalid_weather = con.execute("""
            SELECT count(*) FROM weather_hourly
            WHERE temperature_2m < -10.0 OR temperature_2m > 55.0 OR precipitation < 0.0
        """).fetchone()[0]
    else:
        invalid_weather = 0
    stats["invalid_weather"] = invalid_weather

    # 6. Check for streets with actual data support (baseline_bays > 0 or final_bays > 0)
    supported_streets_count = con.execute("""
        SELECT count(distinct street_name) FROM blocks_summary 
        WHERE baseline_bays > 0 OR final_bays > 0
    """).fetchone()[0]
    stats["supported_streets_count"] = supported_streets_count
    
    # 7. Averages for report
    avg_pre_occ = con.execute("SELECT avg(pre_occupancy) FROM blocks_summary WHERE pre_occupancy IS NOT NULL").fetchone()[0]
    avg_post_occ = con.execute("SELECT avg(post_occupancy) FROM blocks_summary WHERE post_occupancy IS NOT NULL").fetchone()[0]
    stats["avg_pre_occ"] = avg_pre_occ
    stats["avg_post_occ"] = avg_post_occ
    
    # 8. Total bays removed summary
    total_bays_removed = con.execute("SELECT sum(bays_removed) FROM blocks_summary").fetchone()[0]
    stats["total_bays_removed"] = total_bays_removed or 0
    
    # 9. Turnover and Duration averages
    avg_turnover = con.execute("SELECT avg(turnover_rate) FROM hourly_occupancy").fetchone()[0]
    avg_duration = con.execute("SELECT avg(avg_duration_min) FROM hourly_occupancy").fetchone()[0]
    stats["avg_turnover"] = avg_turnover or 0.0
    stats["avg_duration"] = avg_duration or 0.0

    return stats


def generate_report(stats: dict, report_path: str) -> None:
    """
    Writes validation results and counts into a markdown report.
    """
    pre_occ_pct = f"{stats['avg_pre_occ']*100:.2f}%" if stats['avg_pre_occ'] is not None else "N/A"
    post_occ_pct = f"{stats['avg_post_occ']*100:.2f}%" if stats['avg_post_occ'] is not None else "N/A"
    
    passed_all = (
        stats["null_summary_keys"] == 0 and 
        stats["null_occupancy_keys"] == 0 and 
        stats["out_of_bounds_occ"] == 0 and
        stats["invalid_traffic"] == 0 and
        stats["invalid_weather"] == 0 and
        stats["hourly_occupancy_count"] > 0 and
        stats["weather_hourly_count"] > 0
    )
    
    status_label = "🟢 PASSED" if passed_all else "🔴 FAILED"
    
    content = f"""# Victoria Urban Planning - Ingestion Pipeline Validation Report

## Execution Status: {status_label}

This report was automatically generated after the execution of the enhanced Stream B ingestion pipeline.

---

## 1. Database Table Summary

| Table Name | Row Count | Status | Notes |
| :--- | :--- | :--- | :--- |
| `block_geometries` | {stats['block_geometries_count']:,} | {"Active" if stats['block_geometries_count'] > 0 else "Empty"} | Dissolved vector geometries |
| `blocks_summary` | {stats['blocks_summary_count']:,} | {"Active" if stats['blocks_summary_count'] > 0 else "Empty"} | Before/after metrics with obstruction calibration |
| `hourly_occupancy` | {stats['hourly_occupancy_count']:,} | {"Active" if stats['hourly_occupancy_count'] > 0 else "Empty"} | Hourly records with turnover & duration metrics |
| `traffic_volumes` | {stats['traffic_volumes_count']:,} | {"Active" if stats['traffic_volumes_count'] > 0 else "Empty"} | SCATS 15-min traffic with vehicle classification |
| `weather_hourly` | {stats['weather_hourly_count']:,} | {"Active" if stats['weather_hourly_count'] > 0 else "Empty"} | Open-Meteo meteorological telemetry |

---

## 2. Data Quality Assertions

| Data Quality Check | Assertion Rule | Actual Value | Status |
| :--- | :--- | :--- | :--- |
| **No Null Keys in Summary** | `null_keys == 0` | {stats['null_summary_keys']} | {"✔️ PASS" if stats['null_summary_keys'] == 0 else "❌ FAIL"} |
| **No Null Keys in Occupancy** | `null_keys == 0` | {stats['null_occupancy_keys']} | {"✔️ PASS" if stats['null_occupancy_keys'] == 0 else "❌ FAIL"} |
| **Valid Occupancy Rates** | `occupancy_rate` in `[0.0, 1.0]` | {stats['out_of_bounds_occ']} out-of-bounds | {"✔️ PASS" if stats['out_of_bounds_occ'] == 0 else "❌ FAIL"} |
| **Valid Traffic Volumes & Saturation** | `volume >= 0` & `saturation` in `[0, 1]` | {stats['invalid_traffic']} invalid | {"✔️ PASS" if stats['invalid_traffic'] == 0 else "❌ FAIL"} |
| **Valid Weather Telemetry** | `temp` in `[-10, 55]` & `precip >= 0` | {stats['invalid_weather']} invalid | {"✔️ PASS" if stats['invalid_weather'] == 0 else "❌ FAIL"} |
| **Min Volume Threshold** | `hourly_occupancy > 0` | {stats['hourly_occupancy_count']:,} rows | {"✔️ PASS" if stats['hourly_occupancy_count'] > 0 else "❌ FAIL"} |
| **Weather Telemetry Ingestion** | `weather_hourly > 0` | {stats['weather_hourly_count']:,} rows | {"✔️ PASS" if stats['weather_hourly_count'] > 0 else "❌ FAIL"} |

---

## 3. High-Level Urban Analytics Metrics

- **Supported Corridors with Empirical Data:** {stats['supported_streets_count']} unique streets
- **Total Kerbside Parking Bays Removed:** {int(stats['total_bays_removed'])} bays
- **Average Occupancy (Baseline Period):** {pre_occ_pct}
- **Average Occupancy (Post-Intervention Period):** {post_occ_pct}
- **Mean Parking Turnover Rate:** {stats['avg_turnover']:.2f} events / bay / hour
- **Mean Parking Stay Duration:** {stats['avg_duration']:.1f} minutes

---
"""
    
    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write(content)
        
    print(f"[+] Validation report written to {report_path}")


def main() -> None:
    """
    Runs assertions and generates validation report.
    """
    if not os.path.exists(DB_PATH):
        print(f"[E] Database not found at {DB_PATH}. Run run_ingestion.py first.")
        sys.exit(1)
        
    print(f"[*] Running data quality validation on {DB_PATH}...")
    con = duckdb.connect(DB_PATH)
    
    try:
        stats = run_assertions(con)
        
        passed_all = (
            stats["null_summary_keys"] == 0 and 
            stats["null_occupancy_keys"] == 0 and 
            stats["out_of_bounds_occ"] == 0 and
            stats["invalid_traffic"] == 0 and
            stats["invalid_weather"] == 0 and
            stats["hourly_occupancy_count"] > 0 and
            stats["weather_hourly_count"] > 0
        )
        
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        report_path = os.path.join(PROCESSED_DIR, "validation_report.md")
        generate_report(stats, report_path)
        
        if passed_all:
            print("[+] Pipeline validation PASSED.")
        else:
            print("[!] Pipeline validation FAILED. See report for details.")
            sys.exit(1)
            
    except Exception as e:
        print(f"[E] Validation failed with error: {e}")
        sys.exit(1)
    finally:
        con.close()


if __name__ == "__main__":
    main()
