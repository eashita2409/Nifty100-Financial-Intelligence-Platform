from fastapi import APIRouter, Depends
import sqlite3
from ..database import get_db
from ..schemas import HealthResponse, VersionResponse

router = APIRouter(tags=["System"])

@router.get("/health", response_model=HealthResponse)
def get_health(db: sqlite3.Connection = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "error", "database": "disconnected"}

@router.get("/version", response_model=VersionResponse)
def get_version():
    return {"version": "1.0.0", "description": "Nifty100 Financial Intelligence API"}
