"""
database.py – SQLite setup using Python's built-in sqlite3.
Creates three tables:
  - users       : login credentials
  - uploaded_files : metadata about each file a user uploads
  - dashboards  : saved dashboard configurations per file
"""

import sqlite3
import os

DB_PATH = "sales_dashboard.db"

def get_conn():
    """Return a new SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets us access columns by name
    return conn

def init_db():
    """Create all tables if they don't already exist."""
    conn = get_conn()
    c = conn.cursor()

    # ── Users ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT    UNIQUE NOT NULL,
            email        TEXT    UNIQUE NOT NULL,
            password     TEXT    NOT NULL,          -- bcrypt hash
            created_at   TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Uploaded Files ────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL REFERENCES users(id),
            filename     TEXT    NOT NULL,          -- original name
            stored_name  TEXT    NOT NULL,          -- UUID-based name on disk
            rows         INTEGER,
            columns      INTEGER,
            file_size_kb REAL,
            uploaded_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Dashboards ────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS dashboards (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL REFERENCES users(id),
            file_id      INTEGER NOT NULL REFERENCES uploaded_files(id),
            name         TEXT    NOT NULL,
            kpis         TEXT,    -- JSON string
            chart_config TEXT,    -- JSON string
            created_at   TEXT    DEFAULT (datetime('now')),
            updated_at   TEXT    DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized.")
