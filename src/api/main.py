"""
Victoria Urban Planning API

FastAPI backend providing endpoints for querying block-level parking occupancy
and spatial data for the bike lane impact analysis across supported streets and suburbs.
"""

import os
import sys
import json
import duckdb
import pandas as pd
import numpy as np

# Ensure project root is in PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from src.config import DB_PATH, BASELINE_YEAR, POST_YEAR

app = FastAPI(
    title="Victoria Urban Planning API",
    description="API for analyzing the impact of bike lanes on parking utilization across supported streets and suburbs.",
    version="1.0.0"
)

# Enable CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection() -> duckdb.DuckDBPyConnection:
    """
    Establishes a read-only connection to the DuckDB database.
    """
    if not os.path.exists(DB_PATH):
        raise HTTPException(
            status_code=500, 
            detail="Database file not found. Ingestion must be completed first."
        )
    return duckdb.connect(DB_PATH, read_only=True)


@app.get("/")
def read_root() -> dict:
    """
    Root endpoint returning API status and available endpoints.
    """
    return {
        "status": "success", 
        "message": "Victoria Urban Planning API is running",
        "endpoints": ["/api/locations", "/api/blocks", "/api/blocks/occupancy"]
    }


@app.get("/api/locations")
def get_locations() -> dict:
    """
    Retrieves a hierarchical list of supported suburbs and streets that have data.
    """
    con = get_db_connection()
    try:
        query = """
            SELECT DISTINCT suburb, street_name 
            FROM blocks_summary 
            WHERE baseline_bays > 0 OR final_bays > 0
            ORDER BY suburb, street_name
        """
        df = con.execute(query).df()
        
        grouped = df.groupby("suburb")["street_name"].apply(list).reset_index()
        suburbs = []
        for _, row in grouped.iterrows():
            suburbs.append({
                "name": row["suburb"],
                "streets": row["street_name"]
            })
            
        return {"status": "success", "suburbs": suburbs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


from typing import Optional

@app.get("/api/blocks")
def get_blocks(
    suburb: str = Query(..., description="The selected suburb"),
    street: Optional[str] = Query(None, description="The selected street (optional)")
) -> dict:
    """
    Retrieves a GeoJSON FeatureCollection of blocks for a specific suburb (and optional street).
    """
    con = get_db_connection()
    try:
        if street and street != "All Streets":
            query = """
                SELECT 
                    block_desc, 
                    baseline_bays, 
                    final_bays, 
                    bays_removed, 
                    pre_occupancy, 
                    post_occupancy, 
                    geom_json 
                FROM blocks_summary
                WHERE suburb = ? AND street_name = ?
                  AND (baseline_bays > 0 OR final_bays > 0)
            """
            df = con.execute(query, [suburb, street]).df()
        else:
            query = """
                SELECT 
                    block_desc, 
                    baseline_bays, 
                    final_bays, 
                    bays_removed, 
                    pre_occupancy, 
                    post_occupancy, 
                    geom_json 
                FROM blocks_summary
                WHERE suburb = ?
                  AND (baseline_bays > 0 OR final_bays > 0)
            """
            df = con.execute(query, [suburb]).df()
        
        features = []
        for _, row in df.iterrows():
            features.append({
                "type": "Feature",
                "geometry": json.loads(row["geom_json"]),
                "properties": {
                    "block_desc": row["block_desc"],
                    "baseline_bays": int(row["baseline_bays"]),
                    "final_bays": int(row["final_bays"]),
                    "bays_removed": int(row["bays_removed"]),
                    "pre_occupancy": float(row["pre_occupancy"]) if not pd.isna(row["pre_occupancy"]) else None,
                    "post_occupancy": float(row["post_occupancy"]) if not pd.isna(row["post_occupancy"]) else None
                }
            })
            
        return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


@app.get("/api/blocks/occupancy")
def get_block_occupancy(
    suburb: str = Query(..., description="The selected suburb"),
    street: str = Query(..., description="The selected street"),
    block_desc: str = Query(..., description="The block description")
) -> dict:
    """
    Retrieves the hourly occupancy profile (0-23) for baseline vs post-intervention.
    """
    con = get_db_connection()
    try:
        query = f"""
            SELECT 
                hour(hr) as h,
                AVG(CASE WHEN year={BASELINE_YEAR} THEN occupancy_rate ELSE NULL END) as occ_pre,
                AVG(CASE WHEN year={POST_YEAR} THEN occupancy_rate ELSE NULL END) as occ_post
            FROM hourly_occupancy
            WHERE suburb = ? AND street_name = ? AND block_desc = ?
            GROUP BY 1
            ORDER BY 1
        """
        df = con.execute(query, [suburb, street, block_desc]).df()
        
        if df.empty:
            raise HTTPException(
                status_code=404, 
                detail=f"No occupancy data found for block: {block_desc}"
            )
            
        df = df.replace({np.nan: None})
        data_list = df.to_dict(orient="records")
        
        has_pre = df["occ_pre"].notnull().any() if "occ_pre" in df else False
        has_post = df["occ_post"].notnull().any() if "occ_post" in df else False
        
        data_map = {row["h"]: row for row in data_list}
        
        padded_data = []
        for h in range(24):
            if h in data_map:
                row = data_map[h]
                padded_data.append({
                    "h": h,
                    "occ_pre": row["occ_pre"] if row["occ_pre"] is not None else (0.0 if has_pre else None),
                    "occ_post": row["occ_post"] if row["occ_post"] is not None else (0.0 if has_post else None)
                })
            else:
                padded_data.append({
                    "h": h, 
                    "occ_pre": 0.0 if has_pre else None, 
                    "occ_post": 0.0 if has_post else None
                })
        
        return {
            "status": "success",
            "block_desc": block_desc,
            "data": padded_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()
