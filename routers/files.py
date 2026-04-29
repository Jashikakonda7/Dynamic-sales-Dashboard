"""
routers/files.py – File upload and analysis endpoints.

POST   /api/files/upload          →  upload Excel/CSV, get columns + KPIs back
GET    /api/files/                →  list all files uploaded by current user
GET    /api/files/{file_id}       →  details + re-analysis of a specific file
DELETE /api/files/{file_id}       →  delete file from disk and DB
"""

import os
import uuid
import json
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from database import get_conn
from dependencies import get_current_user

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Helper: column type detection (mirrors your frontend algorithm) ───────────

def detect_column_type(series: pd.Series) -> str:
    sample = series.dropna().head(50)
    if sample.empty:
        return "text"

    str_sample = sample.astype(str).str.strip()

    # Boolean
    bool_vals = {"true", "false", "yes", "no", "1", "0"}
    if str_sample.str.lower().isin(bool_vals).all():
        return "boolean"

    # Numeric first (80% threshold) — prevents numbers being misread as dates
    numeric_count = pd.to_numeric(
        str_sample.str.replace(",", "", regex=False), errors="coerce"
    ).notna().sum()
    if numeric_count / len(sample) >= 0.8:
        return "numeric"

    # Date — only try if values contain date-like separators
    date_pattern = str_sample.str.contains(r"[-/]", regex=True)
    if date_pattern.mean() >= 0.7:
        try:
            pd.to_datetime(sample, format="mixed", errors="raise")
            return "date"
        except Exception:
            pass

    return "text"


def analyze_dataframe(df: pd.DataFrame) -> dict:
    """Return column metadata + KPIs for a dataframe."""
    columns_meta = []
    numeric_cols = []

    for col in df.columns:
        ctype = detect_column_type(df[col])
        meta = {"name": col, "type": ctype, "unique_values": int(df[col].nunique())}

        if ctype == "text":
            top = df[col].astype(str).value_counts().head(10).to_dict()
            meta["top_values"] = top

        columns_meta.append(meta)
        if ctype == "numeric":
            numeric_cols.append(col)

    # KPIs from first numeric column
    kpis = {}
    if numeric_cols:
        primary = numeric_cols[0]
        vals = pd.to_numeric(
            df[primary].astype(str).str.replace(",", "", regex=False), errors="coerce"
        ).dropna()
        if not vals.empty:
            growth = (
                ((vals.iloc[-1] - vals.iloc[0]) / abs(vals.iloc[0])) * 100
                if len(vals) > 1 and vals.iloc[0] != 0 else 0
            )
            kpis = {
                "primary_column": primary,
                "total":   round(float(vals.sum()), 2),
                "average": round(float(vals.mean()), 2),
                "maximum": round(float(vals.max()), 2),
                "minimum": round(float(vals.min()), 2),
                "growth_rate_pct": round(float(growth), 1),
            }

    return {"columns": columns_meta, "numeric_columns": numeric_cols, "kpis": kpis}


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/upload", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload an Excel or CSV file. Returns analysis results immediately."""
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".xlsx", ".xls", ".csv"):
        raise HTTPException(status_code=400, detail="Only .xlsx, .xls, and .csv files are accepted.")

    # Save to disk with a unique name
    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    # Parse with pandas
    try:
        if ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=422, detail=f"Could not parse file: {e}")

    rows, cols = df.shape
    file_size_kb = round(len(contents) / 1024, 2)

    # Run analysis
    analysis = analyze_dataframe(df)

    # Save metadata to DB
    conn = get_conn()
    cursor = conn.execute(
        """INSERT INTO uploaded_files (user_id, filename, stored_name, rows, columns, file_size_kb)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (current_user["id"], file.filename, stored_name, rows, cols, file_size_kb)
    )
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "file_id":      file_id,
        "filename":     file.filename,
        "rows":         rows,
        "columns":      cols,
        "file_size_kb": file_size_kb,
        "analysis":     analysis,
    }


@router.get("/")
def list_files(current_user: dict = Depends(get_current_user)):
    """List all files uploaded by the current user."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT id, filename, rows, columns, file_size_kb, uploaded_at
           FROM uploaded_files WHERE user_id = ? ORDER BY uploaded_at DESC""",
        (current_user["id"],)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/{file_id}")
def get_file(file_id: int, current_user: dict = Depends(get_current_user)):
    """Re-analyze a previously uploaded file and return full details."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM uploaded_files WHERE id = ? AND user_id = ?",
        (file_id, current_user["id"])
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="File not found.")

    file_path = os.path.join(UPLOAD_DIR, row["stored_name"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File data missing from disk.")

    ext = os.path.splitext(row["stored_name"])[1].lower()
    df = pd.read_csv(file_path) if ext == ".csv" else pd.read_excel(file_path)
    analysis = analyze_dataframe(df)

    return {**dict(row), "analysis": analysis}


@router.delete("/{file_id}", status_code=200)
def delete_file(file_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a file from disk and all its DB records."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM uploaded_files WHERE id = ? AND user_id = ?",
        (file_id, current_user["id"])
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="File not found.")

    # Remove disk file
    file_path = os.path.join(UPLOAD_DIR, row["stored_name"])
    if os.path.exists(file_path):
        os.remove(file_path)

    # Remove DB records (dashboards first due to FK)
    conn.execute("DELETE FROM dashboards WHERE file_id = ?", (file_id,))
    conn.execute("DELETE FROM uploaded_files WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()
    return {"message": "File deleted successfully."}
