"""
routers/dashboard.py – Save & manage dashboard configurations.

POST   /api/dashboard/             →  save a new dashboard for a file
GET    /api/dashboard/             →  list all saved dashboards
GET    /api/dashboard/{dash_id}    →  get one dashboard
PUT    /api/dashboard/{dash_id}    →  update dashboard name / config
DELETE /api/dashboard/{dash_id}    →  delete a dashboard
GET    /api/dashboard/{dash_id}/chart-data  →  get chart-ready data from the file
"""

import json
import os
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import get_conn
from dependencies import get_current_user

router = APIRouter()
UPLOAD_DIR = "uploads"

# ── Request models ────────────────────────────────────────────────────────────

class SaveDashboardRequest(BaseModel):
    file_id:      int
    name:         str
    kpis:         Optional[dict] = {}
    chart_config: Optional[dict] = {}

class UpdateDashboardRequest(BaseModel):
    name:         Optional[str]  = None
    kpis:         Optional[dict] = None
    chart_config: Optional[dict] = None

# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/", status_code=201)
def save_dashboard(body: SaveDashboardRequest, current_user: dict = Depends(get_current_user)):
    """Save a dashboard configuration linked to an uploaded file."""
    conn = get_conn()

    # Verify the file belongs to this user
    file_row = conn.execute(
        "SELECT id FROM uploaded_files WHERE id = ? AND user_id = ?",
        (body.file_id, current_user["id"])
    ).fetchone()
    if not file_row:
        conn.close()
        raise HTTPException(status_code=404, detail="File not found.")

    cursor = conn.execute(
        """INSERT INTO dashboards (user_id, file_id, name, kpis, chart_config)
           VALUES (?, ?, ?, ?, ?)""",
        (
            current_user["id"],
            body.file_id,
            body.name,
            json.dumps(body.kpis),
            json.dumps(body.chart_config),
        )
    )
    dash_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"message": "Dashboard saved!", "dashboard_id": dash_id}


@router.get("/")
def list_dashboards(current_user: dict = Depends(get_current_user)):
    """Return all dashboards saved by the current user, with the original filename."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT d.id, d.name, d.created_at, d.updated_at,
                  f.filename, f.rows, f.columns
           FROM dashboards d
           JOIN uploaded_files f ON f.id = d.file_id
           WHERE d.user_id = ?
           ORDER BY d.updated_at DESC""",
        (current_user["id"],)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/{dash_id}")
def get_dashboard(dash_id: int, current_user: dict = Depends(get_current_user)):
    """Get full details of a single saved dashboard."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM dashboards WHERE id = ? AND user_id = ?",
        (dash_id, current_user["id"])
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Dashboard not found.")

    result = dict(row)
    result["kpis"]         = json.loads(result["kpis"] or "{}")
    result["chart_config"] = json.loads(result["chart_config"] or "{}")
    return result


@router.put("/{dash_id}")
def update_dashboard(
    dash_id: int,
    body: UpdateDashboardRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update name or config of an existing dashboard."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM dashboards WHERE id = ? AND user_id = ?",
        (dash_id, current_user["id"])
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Dashboard not found.")

    new_name         = body.name         if body.name         is not None else row["name"]
    new_kpis         = json.dumps(body.kpis)         if body.kpis         is not None else row["kpis"]
    new_chart_config = json.dumps(body.chart_config) if body.chart_config is not None else row["chart_config"]

    conn.execute(
        """UPDATE dashboards
           SET name = ?, kpis = ?, chart_config = ?, updated_at = datetime('now')
           WHERE id = ?""",
        (new_name, new_kpis, new_chart_config, dash_id)
    )
    conn.commit()
    conn.close()
    return {"message": "Dashboard updated successfully."}


@router.delete("/{dash_id}")
def delete_dashboard(dash_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM dashboards WHERE id = ? AND user_id = ?",
        (dash_id, current_user["id"])
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Dashboard not found.")

    conn.execute("DELETE FROM dashboards WHERE id = ?", (dash_id,))
    conn.commit()
    conn.close()
    return {"message": "Dashboard deleted."}


@router.get("/{dash_id}/chart-data")
def get_chart_data(dash_id: int, current_user: dict = Depends(get_current_user)):
    """
    Re-reads the file linked to a saved dashboard and returns
    chart-ready JSON data (first 30 rows for line/bar, up to 100 for scatter).
    """
    conn = get_conn()
    dash = conn.execute(
        "SELECT * FROM dashboards WHERE id = ? AND user_id = ?",
        (dash_id, current_user["id"])
    ).fetchone()
    if not dash:
        conn.close()
        raise HTTPException(status_code=404, detail="Dashboard not found.")

    file_row = conn.execute(
        "SELECT * FROM uploaded_files WHERE id = ?", (dash["file_id"],)
    ).fetchone()
    conn.close()

    if not file_row:
        raise HTTPException(status_code=404, detail="Linked file not found.")

    file_path = os.path.join(UPLOAD_DIR, file_row["stored_name"])
    ext = os.path.splitext(file_row["stored_name"])[1].lower()
    df = pd.read_csv(file_path) if ext == ".csv" else pd.read_excel(file_path)

    # Identify numeric and text columns
    numeric_cols = [
        c for c in df.columns
        if pd.to_numeric(
            df[c].astype(str).str.replace(",", "", regex=False), errors="coerce"
        ).notna().sum() / max(len(df), 1) >= 0.8
    ]
    text_cols = [c for c in df.columns if c not in numeric_cols]

    result = {}

    # Bar chart data (first 20 rows)
    if numeric_cols:
        label_col = text_cols[0] if text_cols else None
        bar_labels = (
            df[label_col].astype(str).head(20).tolist()
            if label_col else [f"Row {i+1}" for i in range(min(20, len(df)))]
        )
        result["bar"] = {
            "labels":  bar_labels,
            "values":  pd.to_numeric(
                df[numeric_cols[0]].astype(str).str.replace(",", "", regex=False),
                errors="coerce"
            ).fillna(0).head(20).tolist(),
            "column": numeric_cols[0],
        }

    # Pie chart data (categorical column ≤10 unique values)
    pie_col = next(
        (c for c in text_cols if 2 <= df[c].nunique() <= 10), None
    )
    if pie_col:
        counts = df[pie_col].astype(str).value_counts().head(10)
        result["pie"] = {"labels": counts.index.tolist(), "values": counts.tolist(), "column": pie_col}

    # Line chart data (up to 3 numeric columns, 30 rows)
    if numeric_cols:
        result["line"] = {
            "labels":   [f"Point {i+1}" for i in range(min(30, len(df)))],
            "datasets": [
                {
                    "column": c,
                    "values": pd.to_numeric(
                        df[c].astype(str).str.replace(",", "", regex=False),
                        errors="coerce"
                    ).fillna(0).head(30).tolist(),
                }
                for c in numeric_cols[:3]
            ],
        }

    # Scatter chart data (first 2 numeric cols, 100 rows)
    if len(numeric_cols) >= 2:
        x_vals = pd.to_numeric(df[numeric_cols[0]].astype(str).str.replace(",","",regex=False), errors="coerce").fillna(0)
        y_vals = pd.to_numeric(df[numeric_cols[1]].astype(str).str.replace(",","",regex=False), errors="coerce").fillna(0)
        result["scatter"] = {
            "x_column": numeric_cols[0],
            "y_column": numeric_cols[1],
            "points": [{"x": x, "y": y} for x, y in zip(x_vals.head(100), y_vals.head(100))],
        }

    return result
