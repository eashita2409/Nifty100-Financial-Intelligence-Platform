from fastapi import APIRouter, Depends, HTTPException, Query
import sqlite3
from typing import List, Optional
from ..database import get_db
from ..schemas import CompanyBase, CompanyListResponse, ProfitLossResponse, BalanceSheetResponse, CashflowResponse, RatiosResponse, TearsheetResponse, ScreenerParams
from ..utils import check_company_exists, handle_db_error
from pydantic import ValidationError

router = APIRouter(tags=["Companies"])

@router.get("/companies", response_model=CompanyListResponse)
def get_companies(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, company_name as name, nse_profile as nse_ticker, bse_profile as bse_ticker FROM companies")
    comps = [dict(r) for r in cursor.fetchall()]
    return CompanyListResponse(companies=comps, total=len(comps))

@router.get("/companies/{ticker}", response_model=CompanyBase)
def get_company(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    ticker = ticker.strip().upper()
    check_company_exists(db, ticker)
    cursor = db.cursor()
    cursor.execute("SELECT id, company_name as name, nse_profile as nse_ticker, bse_profile as bse_ticker FROM companies WHERE id = ?", (ticker,))
    return dict(cursor.fetchone())

@router.get("/companies/{ticker}/pl", response_model=ProfitLossResponse)
def get_pl(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    ticker = ticker.strip().upper()
    check_company_exists(db, ticker)
    cursor = db.cursor()
    cursor.execute("SELECT year, sales, operating_profit, net_profit FROM profitandloss WHERE company_id = ? ORDER BY year", (ticker,))
    return ProfitLossResponse(company_id=ticker, profit_loss=[dict(r) for r in cursor.fetchall()])

@router.get("/companies/{ticker}/bs", response_model=BalanceSheetResponse)
def get_bs(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    ticker = ticker.strip().upper()
    check_company_exists(db, ticker)
    cursor = db.cursor()
    cursor.execute("SELECT year, total_assets, equity_capital, borrowings FROM balancesheet WHERE company_id = ? ORDER BY year", (ticker,))
    return BalanceSheetResponse(company_id=ticker, balance_sheets=[dict(r) for r in cursor.fetchall()])

@router.get("/companies/{ticker}/cashflow", response_model=CashflowResponse)
def get_cashflow(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    ticker = ticker.strip().upper()
    check_company_exists(db, ticker)
    cursor = db.cursor()
    cursor.execute("SELECT c.year, c.operating_activity as operating_cash_flow, fr.capex_cr as capex, fr.free_cash_flow_cr as free_cash_flow FROM cashflow c LEFT JOIN financial_ratios fr ON c.company_id = fr.company_id AND c.year = fr.year WHERE c.company_id = ? ORDER BY c.year", (ticker,))
    return CashflowResponse(company_id=ticker, cashflows=[dict(r) for r in cursor.fetchall()])

@router.get("/companies/{ticker}/ratios", response_model=RatiosResponse)
def get_ratios(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    ticker = ticker.strip().upper()
    check_company_exists(db, ticker)
    cursor = db.cursor()
    cursor.execute("SELECT year, return_on_equity_pct, debt_to_equity, free_cash_flow_cr FROM financial_ratios WHERE company_id = ? ORDER BY year", (ticker,))
    return RatiosResponse(company_id=ticker, ratios=[dict(r) for r in cursor.fetchall()])

@router.get("/companies/{ticker}/tearsheet", response_model=TearsheetResponse)
def get_tearsheet(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    ticker = ticker.strip().upper()
    check_company_exists(db, ticker)
    # Return a basic summary
    cursor = db.cursor()
    cursor.execute("SELECT * FROM companies WHERE id = ?", (ticker,))
    return TearsheetResponse(company_id=ticker, summary=dict(cursor.fetchone()))

@router.get("/screener", response_model=List[CompanyBase])
def screener(
    min_market_cap: Optional[float] = Query(None),
    max_market_cap: Optional[float] = Query(None),
    sector: Optional[str] = Query(None),
    db: sqlite3.Connection = Depends(get_db)
):
    try:
        params = ScreenerParams(min_market_cap=min_market_cap, max_market_cap=max_market_cap, sector=sector)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    query = "SELECT c.id, c.company_name as name FROM companies c"
    conds = []
    vals = []
    
    if params.sector:
        query += " JOIN sectors s ON c.id = s.company_id"
        conds.append("s.broad_sector = ?")
        vals.append(params.sector)
        
    if params.min_market_cap is not None or params.max_market_cap is not None:
        query += " JOIN market_cap m ON c.id = m.company_id AND m.year = (SELECT MAX(year) FROM market_cap WHERE company_id = c.id)"
        if params.min_market_cap is not None:
            conds.append("m.market_cap_crore >= ?")
            vals.append(params.min_market_cap)
        if params.max_market_cap is not None:
            conds.append("m.market_cap_crore <= ?")
            vals.append(params.max_market_cap)
            
    if conds:
        query += " WHERE " + " AND ".join(conds)
        
    cursor = db.cursor()
    cursor.execute(query, vals)
    return [dict(r) for r in cursor.fetchall()]
