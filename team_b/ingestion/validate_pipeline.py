"""
Validate Pipeline Script

Automated Data Quality Validation Suite to run post-ingestion assertions
and generate a validation report markdown file in data/processed/.
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
    Executes automated data quality validation queries.
    """
    stats = {}
    
    # 1. Row counts
    stats["blocks_summary_count"] = con.execute("SELECT count(*) FROM blocks_summary").fetchone()[0]
    stats["block_geometries_count"] = con.execute("SELECT count(*) FROM block_geometries").fetchone()[0]
    stats["hourly_occupancy_count"] = con.execute("SELECT count(*) FROM hourly_occupancy").fetchone()[0]
    stats["traffic_volumes_count"] = con.execute("SELECT count(*) FROM traffic_volumes").fetchone()[0]
    
    # 2. Check for null keys
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
    
    # 3. Check occupancy bounds
    out_of_bounds_occ = con.execute("""
        SELECT count(*) FROM hourly_occupancy 
        WHERE occupancy_rate < 0.0 OR occupancy_rate > 1.0
    """).fetchone()[0]
    stats["out_of_bounds_occ"] = out_of_bounds_occ
    
    # 4. Check for streets with actual data support (baseline_bays > 0 or final_bays > 0)
    supported_streets_count = con.execute("""
        SELECT count(distinct street_name) FROM blocks_summary 
        WHERE baseline_bays > 0 OR final_bays > 0
    """).fetchone()[0]
    stats["supported_streets_count"] = supported_streets_count
    
    # 5. Get sample averages for report
    avg_pre_occ = con.execute("SELECT avg(pre_occupancy) FROM blocks_summary WHERE pre_occupancy IS NOT NULL").fetchone()[0]
    avg_post_occ = con.execute("SELECT avg(post_occupancy) FROM blocks_summary WHERE post_occupancy IS NOT NULL").fetchone()[0]
    stats["avg_pre_occ"] = avg_pre_occ
    stats["avg_post_occ"] = avg_post_occ
    
    # 6. Total bays removed summary
    total_bays_removed = con.execute("SELECT sum(bays_removed) FROM blocks_summary").fetchone()[0]
    stats["total_bays_removed"] = total_bays_removed or 0
    
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
        stats["hourly_occupancy_count"] > 0
    )
    
    status_label = "🟢 PASSED" if passed_all else "🔴 FAILED"
    
    content = f"""# Victoria Urban Planning - Ingestion Pipeline Validation Report

## Execution Status: {status_label}

This report was automatically generated after the execution of the ingestion pipeline.

---

## 1. Database Table Summary

| Table Name | Row Count | Status | Notes |
| :--- | :--- | :--- | :--- |
| `block_geometries` | {stats['block_geometries_count']:,} | {"Active" if stats['block_geometries_count'] > 0 else "Empty"} | Dissolved vector geometries |
| `blocks_summary` | {stats['blocks_summary_count']:,} | {"Active" if stats['blocks_summary_count'] > 0 else "Empty"} | Before/after metrics summary |
| `hourly_occupancy` | {stats['hourly_occupancy_count']:,} | {"Active" if stats['hourly_occupancy_count'] > 0 else "Empty"} | Transactional hourly records |
| `traffic_volumes` | {stats['traffic_volumes_count']:,} | {"Active" if stats['traffic_volumes_count'] > 0 else "Empty"} | Simulated traffic volumes |

---

## 2. Data Quality Assertions

| Data Quality Check | Assertion Rule | Actual Value | Status |
| :--- | :--- | :--- | :--- |
| **No Null Keys in Summary** | `null_keys == 0` | {stats['null_summary_keys']} | {"✔️ PASS" if stats['null_summary_keys'] == 0 else "❌ FAIL"} |
| **No Null Keys in Occupancy** | `null_keys == 0` | {stats['null_occupancy_keys']} | {"✔️ PASS" if stats['null_occupancy_keys'] == 0 else "❌ FAIL"} |
| **Valid Occupancy Rates** | `occupancy_rate` in `[0.0, 1.0]` | {stats['out_of_bounds_occ']} out-of-bounds | {"✔️ PASS" if stats['out_of_bounds_occ'] == 0 else "❌ FAIL"} |
| **Min Volume Threshold** | `row_count > 0` | {stats['hourly_occupancy_count']:,} rows | {"✔️ PASS" if stats['hourly_occupancy_count'] > 0 else "❌ FAIL"} |

---

## 3. High-Level Metrics Summary

- **Supported Streets with Data:** {stats['supported_streets_count']} unique streets
- **Total Parking Bays Removed:** {int(stats['total_bays_removed'])} bays
- **Average Occupancy (Before Interventions):** {pre_occ_pct}
- **Average Occupancy (After Interventions):** {post_occ_pct}

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
        
        # Determine pass/fail
        passed_all = (
            stats["null_summary_keys"] == 0 and 
            stats["null_occupancy_keys"] == 0 and 
            stats["out_of_bounds_occ"] == 0 and
            stats["hourly_occupancy_count"] > 0
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
