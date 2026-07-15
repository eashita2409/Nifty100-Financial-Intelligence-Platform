from fastapi import APIRouter, Depends, Query
import sqlite3
from typing import List, Optional
from ..database import get_db
from ..schemas import CompanyListResponse, CompanyBase, PeerResponse, SectorSummary, ScreenerParams
from ..services import companies as company_service
from ..utils import handle_db_error

router = APIRouter(tags=["Companies"])

@router.get("/companies", response_model=CompanyListResponse)
def get_companies(db: sqlite3.Connection = Depends(get_db)):
    try:
        companies = company_service.get_all_companies(db)
        return {"companies": companies, "total": len(companies)}
    except sqlite3.Error as e:
        handle_db_error(e)

@router.get("/company/{ticker}", response_model=CompanyBase)
def get_company(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        return company_service.get_company(db, ticker)
    except sqlite3.Error as e:
        handle_db_error(e)

@router.get("/peer/{ticker}", response_model=PeerResponse)
def get_peers(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        return company_service.get_peers(db, ticker)
    except sqlite3.Error as e:
        handle_db_error(e)

@router.get("/sector/{sector}", response_model=SectorSummary)
def get_sector_summary(sector: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        return company_service.get_sector_summary(db, sector)
    except sqlite3.Error as e:
        handle_db_error(e)

@router.get("/screener", response_model=List[CompanyBase])
def screener(
    min_market_cap: Optional[float] = None,
    max_market_cap: Optional[float] = None,
    min_pe: Optional[float] = None,
    max_pe: Optional[float] = None,
    min_roe: Optional[float] = None,
    sector: Optional[str] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    try:
        params = ScreenerParams(
            min_market_cap=min_market_cap,
            max_market_cap=max_market_cap,
            min_pe=min_pe,
            max_pe=max_pe,
            min_roe=min_roe,
            sector=sector
        )
        return company_service.screener(db, params)
    except sqlite3.Error as e:
        handle_db_error(e)
