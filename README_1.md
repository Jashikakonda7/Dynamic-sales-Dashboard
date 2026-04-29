# Dynamic Sales Dashboard – Backend API

A **FastAPI + SQLite** backend for the Dynamic Sales Analysis Dashboard project.  
Built for the B.Tech CSE Field Project at Vignan's Foundation for Science, Technology and Research.

---

## Tech Stack

| Layer       | Technology              |
|-------------|-------------------------|
| Framework   | FastAPI (Python)        |
| Database    | SQLite (built-in, zero setup) |
| Auth        | JWT (PyJWT) + bcrypt    |
| Data Engine | Pandas + OpenPyXL       |
| Server      | Uvicorn                 |

---

## Project Structure

```
sales-dashboard-backend/
├── main.py           # FastAPI app, CORS, router registration
├── database.py       # SQLite setup, table creation
├── auth_utils.py     # Password hashing (bcrypt) + JWT helpers
├── dependencies.py   # get_current_user() dependency
├── requirements.txt  # All Python packages
└── routers/
    ├── auth.py       # /api/auth  – register, login, me
    ├── files.py      # /api/files – upload, list, get, delete
    └── dashboard.py  # /api/dashboard – save, list, get, update, delete, chart-data
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the server
```bash
uvicorn main:app --reload
```

The API will be live at: **http://127.0.0.1:8000**  
Interactive docs (Swagger UI): **http://127.0.0.1:8000/docs**

---

## API Reference

### Auth Endpoints

#### Register
```
POST /api/auth/register
Content-Type: application/json

{
  "username": "john",
  "email": "john@example.com",
  "password": "mypassword"
}
```

#### Login
```
POST /api/auth/login
Content-Type: application/json

{
  "username": "john",
  "password": "mypassword"
}

Response:
{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer",
  "user": { "id": 1, "username": "john", "email": "john@example.com" }
}
```

#### Get Current User
```
GET /api/auth/me
Authorization: Bearer <JWT_TOKEN>
```

---

### File Endpoints

All file endpoints require: `Authorization: Bearer <JWT_TOKEN>`

#### Upload File (Excel or CSV)
```
POST /api/files/upload
Content-Type: multipart/form-data
Body: file=<your_excel_or_csv_file>

Response:
{
  "file_id": 1,
  "filename": "sales_data.xlsx",
  "rows": 5000,
  "columns": 8,
  "file_size_kb": 420.5,
  "analysis": {
    "columns": [
      { "name": "Product",  "type": "text",    "unique_values": 12 },
      { "name": "Sales",    "type": "numeric", "unique_values": 4980 },
      { "name": "Date",     "type": "date",    "unique_values": 365 }
    ],
    "numeric_columns": ["Sales", "Quantity"],
    "kpis": {
      "primary_column": "Sales",
      "total": 482350.0,
      "average": 96.47,
      "maximum": 12500.0,
      "minimum": 50.0,
      "growth_rate_pct": 14.2
    }
  }
}
```

#### List My Files
```
GET /api/files/
```

#### Get File Details + Re-Analysis
```
GET /api/files/{file_id}
```

#### Delete File
```
DELETE /api/files/{file_id}
```

---

### Dashboard Endpoints

All dashboard endpoints require: `Authorization: Bearer <JWT_TOKEN>`

#### Save Dashboard
```
POST /api/dashboard/
{
  "file_id": 1,
  "name": "Q1 Sales Dashboard",
  "kpis": { "total": 482350, "average": 96.47 },
  "chart_config": { "bar_column": "Sales", "pie_column": "Region" }
}
```

#### List My Dashboards
```
GET /api/dashboard/
```

#### Get Dashboard
```
GET /api/dashboard/{dash_id}
```

#### Update Dashboard
```
PUT /api/dashboard/{dash_id}
{ "name": "Updated Name" }
```

#### Delete Dashboard
```
DELETE /api/dashboard/{dash_id}
```

#### Get Chart-Ready Data
```
GET /api/dashboard/{dash_id}/chart-data

Response:
{
  "bar":     { "labels": [...], "values": [...], "column": "Sales" },
  "pie":     { "labels": [...], "values": [...], "column": "Region" },
  "line":    { "labels": [...], "datasets": [ { "column": "Sales", "values": [...] } ] },
  "scatter": { "x_column": "Sales", "y_column": "Quantity", "points": [{x,y}, ...] }
}
```
This endpoint is what your **frontend calls** to render Chart.js charts from saved dashboards.

---

## Connecting to Your Existing Frontend

In your `app.js`, replace the local file processing with API calls:

```javascript
// 1. Login and store token
const res = await fetch('http://127.0.0.1:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'john', password: 'mypassword' })
});
const { access_token } = await res.json();
localStorage.setItem('token', access_token);

// 2. Upload a file
const formData = new FormData();
formData.append('file', selectedFile);
const uploadRes = await fetch('http://127.0.0.1:8000/api/files/upload', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
  body: formData
});
const { analysis, file_id } = await uploadRes.json();
// analysis.kpis and analysis.columns are ready to render!
```

---

## Database Schema

```
users              uploaded_files          dashboards
──────────────     ──────────────────────  ──────────────────
id                 id                      id
username           user_id  ──────────►    user_id
email              filename                file_id ──────────►
password (hash)    stored_name             name
created_at         rows                    kpis (JSON)
                   columns                 chart_config (JSON)
                   file_size_kb            created_at
                   uploaded_at             updated_at
```

---

## Authors

Banif Kasim (241FA04318), Ragavendra Sai (241FA04589),  
Tabrez Ahmad (241FA04C38), Jashika (241FA04F07)  

Guide: Shaik Khadersha, Teaching Associate, CSE  
Vignan's Foundation for Science, Technology and Research – April 2026
