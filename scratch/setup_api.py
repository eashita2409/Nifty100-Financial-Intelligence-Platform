import os
import time
import sqlite3
import json
from pathlib import Path

# Paths
API_DIR = Path("src/api")
ROUTERS_DIR = API_DIR / "routers"
SERVICES_DIR = API_DIR / "services"

os.makedirs(ROUTERS_DIR, exist_ok=True)
os.makedirs(SERVICES_DIR, exist_ok=True)

# ----------------- database.py -----------------
with open(API_DIR / "database.py", "w") as f:
    f.write('''import sqlite3
from pathlib import Path
from typing import Generator
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path("data") / "db" / "nifty100.db"

def get_db_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = None
    try:
        conn = get_db_connection()
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()
''')

# ----------------- schemas.py -----------------
with open(API_DIR / "schemas.py", "w") as f:
    f.write('''from pydantic import BaseModel, Field, root_validator, model_validator
from typing import List, Optional, Any, Dict

class HealthResponse(BaseModel):
    status: str
    db_row_counts: Dict[str, int]
    uptime_seconds: float
    version: str

class CompanyBase(BaseModel):
    id: str
    name: str
    nse_ticker: Optional[str] = None
    bse_ticker: Optional[str] = None
    broad_sector: Optional[str] = None
    sub_sector: Optional[str] = None
    market_cap_cr: Optional[float] = None
    current_price: Optional[float] = None

class CompanyListResponse(BaseModel):
    companies: List[CompanyBase]
    total: int

class FinancialRatio(BaseModel):
    year: Optional[float] = None
    return_on_equity_pct: Optional[float] = None
    debt_to_equity: Optional[float] = None
    free_cash_flow_cr: Optional[float] = None

class RatiosResponse(BaseModel):
    company_id: str
    ratios: List[FinancialRatio]

class ProfitLoss(BaseModel):
    year: Optional[float] = None
    sales: Optional[float] = None
    operating_profit: Optional[float] = None
    net_profit: Optional[float] = None

class ProfitLossResponse(BaseModel):
    company_id: str
    profit_loss: List[ProfitLoss]

class BalanceSheet(BaseModel):
    year: Optional[float] = None
    total_assets: Optional[float] = None
    equity_capital: Optional[float] = None
    borrowings: Optional[float] = None

class BalanceSheetResponse(BaseModel):
    company_id: str
    balance_sheets: List[BalanceSheet]

class Cashflow(BaseModel):
    year: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    capex: Optional[float] = None
    free_cash_flow: Optional[float] = None

class CashflowResponse(BaseModel):
    company_id: str
    cashflows: List[Cashflow]

class TearsheetResponse(BaseModel):
    company_id: str
    summary: Dict[str, Any]
    
class SectorSummary(BaseModel):
    sector: str
    companies: List[CompanyBase]

class SectorListResponse(BaseModel):
    sectors: List[str]

class PeerComparison(BaseModel):
    company_id: str
    pe_ratio: Optional[float] = None
    roe: Optional[float] = None
    market_cap_cr: Optional[float] = None

class PeerResponse(BaseModel):
    group_name: str
    peers: List[PeerComparison]

class Valuation(BaseModel):
    year: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    market_cap_crore: Optional[float] = None

class ValuationResponse(BaseModel):
    company_id: str
    valuations: List[Valuation]
    
class PortfolioStatsResponse(BaseModel):
    stats: Dict[str, Any]

class Document(BaseModel):
    year: Optional[float] = None
    annual_report: Optional[str] = None

class DocumentsResponse(BaseModel):
    company_id: str
    documents: List[Document]

class ScreenerParams(BaseModel):
    min_market_cap: Optional[float] = Field(None, ge=0)
    max_market_cap: Optional[float] = Field(None, ge=0)
    sector: Optional[str] = None

    @model_validator(mode='after')
    def check_market_cap(self):
        if self.min_market_cap is not None and self.max_market_cap is not None:
            if self.min_market_cap > self.max_market_cap:
                raise ValueError('min_market_cap cannot be greater than max_market_cap')
        return self
''')

# ----------------- utils.py -----------------
with open(API_DIR / "utils.py", "w") as f:
    f.write('''from fastapi import HTTPException
import sqlite3

def check_company_exists(conn: sqlite3.Connection, ticker: str):
    ticker = ticker.strip().upper()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM companies WHERE id = ?", (ticker,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found")

def handle_db_error(e: Exception):
    raise HTTPException(status_code=500, detail="Database error occurred")
''')

# ----------------- main.py -----------------
with open(API_DIR / "main.py", "w") as f:
    f.write('''import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .routers import system, companies, sectors, peers, valuation, portfolio, documents
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(
    title="Nifty100 Financial Intelligence API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response

app.state.START_TIME = time.time()

app.include_router(system.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(peers.router, prefix="/api/v1")
app.include_router(valuation.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
''')

# ----------------- routers/system.py -----------------
with open(ROUTERS_DIR / "system.py", "w") as f:
    f.write('''from fastapi import APIRouter, Depends, Request
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
''')

# ----------------- routers/companies.py -----------------
with open(ROUTERS_DIR / "companies.py", "w") as f:
    f.write('''from fastapi import APIRouter, Depends, HTTPException, Query
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
''')

# ----------------- routers/sectors.py -----------------
with open(ROUTERS_DIR / "sectors.py", "w") as f:
    f.write('''from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from ..database import get_db
from ..schemas import SectorListResponse, SectorSummary

router = APIRouter(tags=["Sectors"])

@router.get("/sectors", response_model=SectorListResponse)
def get_sectors(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT DISTINCT broad_sector FROM sectors WHERE broad_sector IS NOT NULL")
    return SectorListResponse(sectors=[r['broad_sector'] for r in cursor.fetchall()])

@router.get("/sectors/{sector}/companies", response_model=SectorSummary)
def get_sector_companies(sector: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT c.id, c.company_name as name FROM companies c JOIN sectors s ON c.id = s.company_id WHERE s.broad_sector = ? COLLATE NOCASE", (sector,))
    comps = [dict(r) for r in cursor.fetchall()]
    if not comps:
        raise HTTPException(status_code=404, detail="Sector not found")
    return SectorSummary(sector=sector, companies=comps)
''')

# ----------------- routers/peers.py -----------------
with open(ROUTERS_DIR / "peers.py", "w") as f:
    f.write('''from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from ..database import get_db
from ..schemas import PeerResponse
from ..utils import check_company_exists

router = APIRouter(tags=["Peers"])

@router.get("/peers/{group_name}", response_model=PeerResponse)
def get_peers_by_group(group_name: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT company_id as id, company_name as name FROM peer_groups JOIN companies ON peer_groups.company_id = companies.id WHERE peer_group_name = ? COLLATE NOCASE", (group_name,))
    peers = [dict(r) for r in cursor.fetchall()]
    if not peers:
        raise HTTPException(status_code=404, detail="Peer group not found")
    # For simplicity, returning just basic IDs in the response
    return PeerResponse(group_name=group_name, peers=[{"company_id": p['id']} for p in peers])

@router.get("/companies/{ticker}/peers/compare", response_model=PeerResponse)
def get_company_peers(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    ticker = ticker.strip().upper()
    check_company_exists(db, ticker)
    cursor = db.cursor()
    
    # get sector
    cursor.execute("SELECT broad_sector FROM sectors WHERE company_id = ?", (ticker,))
    row = cursor.fetchone()
    sector = row['broad_sector'] if row else ""
    
    cursor.execute("""
        SELECT c.id as company_id, 
               m.pe_ratio, 
               f.return_on_equity_pct as roe,
               m.market_cap_crore as market_cap_cr
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        LEFT JOIN market_cap m ON c.id = m.company_id AND m.year = (SELECT MAX(year) FROM market_cap WHERE company_id = c.id)
        LEFT JOIN financial_ratios f ON c.id = f.company_id AND f.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
        WHERE s.broad_sector = ?
    """, (sector,))
    
    peers = [dict(r) for r in cursor.fetchall()]
    return PeerResponse(group_name=sector, peers=peers)
''')

# ----------------- routers/valuation.py -----------------
with open(ROUTERS_DIR / "valuation.py", "w") as f:
    f.write('''from fastapi import APIRouter, Depends
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
''')

# ----------------- routers/portfolio.py -----------------
with open(ROUTERS_DIR / "portfolio.py", "w") as f:
    f.write('''from fastapi import APIRouter, Depends
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
''')

# ----------------- routers/documents.py -----------------
with open(ROUTERS_DIR / "documents.py", "w") as f:
    f.write('''from fastapi import APIRouter, Depends
import sqlite3
from ..database import get_db
from ..schemas import DocumentsResponse
from ..utils import check_company_exists

router = APIRouter(tags=["Documents"])

@router.get("/companies/{ticker}/documents", response_model=DocumentsResponse)
def get_documents(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    ticker = ticker.strip().upper()
    check_company_exists(db, ticker)
    cursor = db.cursor()
    cursor.execute("SELECT year, annual_report FROM documents WHERE company_id = ? ORDER BY year", (ticker,))
    return DocumentsResponse(company_id=ticker, documents=[dict(r) for r in cursor.fetchall()])
''')
