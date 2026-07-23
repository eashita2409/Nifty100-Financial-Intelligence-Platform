from fastapi import APIRouter, Depends
import sqlite3
from ..database import get_db
from ..schemas import PortfolioStatsResponse
import pandas as pd

router = APIRouter(tags=["Portfolio"])

@router.get("/portfolio/stats", response_model=PortfolioStatsResponse)
def get_portfolio_stats(db: sqlite3.Connection = Depends(get_db)):
    # Example stat
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM companies")
    cnt = cursor.fetchone()['cnt']
    return PortfolioStatsResponse(stats={"total_companies": cnt})
