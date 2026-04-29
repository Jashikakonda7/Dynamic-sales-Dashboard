from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import init_db
from routers import auth, files, dashboard

app = FastAPI(title="Dynamic Sales Dashboard API", version="1.0.0")

# Allow frontend (running on any port) to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files as static (optional, for previewing raw files)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include all route modules
app.include_router(auth.router,      prefix="/api/auth",      tags=["Auth"])
app.include_router(files.router,     prefix="/api/files",     tags=["Files"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"message": "Dynamic Sales Dashboard API is running!"}
