from fastapi import APIRouter, Depends, Request
import sqlite3
import time
from ..database import get_db
from ..schemas import HealthResponse

router = APIRouter(tags=["System"])

@router.get("/health", response_model=HealthResponse)
def get_health(request: Request, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r['name'] for r in cursor.fetchall()]
    counts = {}
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) as c FROM {t}")
        counts[t] = cursor.fetchone()['c']
        
    uptime = time.time() - request.app.state.START_TIME
    return HealthResponse(
        status="ok",
        db_row_counts=counts,
        uptime_seconds=uptime,
        version="1.0.0"
    )
