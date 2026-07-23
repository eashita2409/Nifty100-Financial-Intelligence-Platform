from fastapi import APIRouter, Depends
import sqlite3
from ..database import get_db
from ..schemas import ValuationResponse
from ..utils import check_company_exists

router = APIRouter(tags=["Valuation"])

@router.get("/market-cap/{ticker}", response_model=ValuationResponse)
def get_market_cap(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    ticker = ticker.strip().upper()
    check_company_exists(db, ticker)
    cursor = db.cursor()
    cursor.execute("SELECT year, pe_ratio, pb_ratio, market_cap_crore FROM market_cap WHERE company_id = ? ORDER BY year", (ticker,))
    return ValuationResponse(company_id=ticker, valuations=[dict(r) for r in cursor.fetchall()])
