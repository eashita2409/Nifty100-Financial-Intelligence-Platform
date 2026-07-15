from pydantic import BaseModel, Field
from typing import List, Optional, Any

class HealthResponse(BaseModel):
    status: str
    database: str

class VersionResponse(BaseModel):
    version: str
    description: str

class CompanyBase(BaseModel):
    id: str
    name: str
    nse_ticker: Optional[str] = None
    bse_ticker: Optional[str] = None
    isin: Optional[str] = None
    broad_sector: Optional[str] = None
    sub_sector: Optional[str] = None
    market_cap_cr: Optional[float] = None
    current_price: Optional[float] = None

class CompanyListResponse(BaseModel):
    companies: List[CompanyBase]
    total: int

class FinancialRatio(BaseModel):
    year: Optional[int] = None
    return_on_equity_pct: Optional[float] = None
    return_on_capital_employed_pct: Optional[float] = None
    debt_to_equity: Optional[float] = None
    free_cash_flow_cr: Optional[float] = None
    revenue_cagr_5yr: Optional[float] = None
    pat_cagr_5yr: Optional[float] = None
    capital_allocation_pattern: Optional[str] = None

class RatiosResponse(BaseModel):
    company_id: str
    ratios: List[FinancialRatio]

class Valuation(BaseModel):
    year: Optional[int] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ev_to_ebitda: Optional[float] = None

class ValuationResponse(BaseModel):
    company_id: str
    valuations: List[Valuation]

class Cashflow(BaseModel):
    year: Optional[int] = None
    operating_cash_flow: Optional[float] = None
    capex: Optional[float] = None
    free_cash_flow: Optional[float] = None

class CashflowResponse(BaseModel):
    company_id: str
    cashflows: List[Cashflow]

class BalanceSheet(BaseModel):
    year: Optional[int] = None
    total_assets: Optional[float] = None
    equity_capital: Optional[float] = None
    reserves: Optional[float] = None
    borrowings: Optional[float] = None

class BalanceSheetResponse(BaseModel):
    company_id: str
    balance_sheets: List[BalanceSheet]

class ProfitLoss(BaseModel):
    year: Optional[int] = None
    sales: Optional[float] = None
    operating_profit: Optional[float] = None
    net_profit: Optional[float] = None

class ProfitLossResponse(BaseModel):
    company_id: str
    profit_loss: List[ProfitLoss]

class ProCon(BaseModel):
    type: str
    category: str
    text: str
    confidence: float

class ProsConsResponse(BaseModel):
    company_id: str
    pros: List[ProCon]
    cons: List[ProCon]

class PeerComparison(BaseModel):
    company_id: str
    market_cap_cr: Optional[float] = None
    pe_ratio: Optional[float] = None
    roe: Optional[float] = None

class PeerResponse(BaseModel):
    sector: str
    peers: List[PeerComparison]

class SectorSummary(BaseModel):
    sector: str
    company_count: int
    avg_pe: Optional[float] = None
    avg_roe: Optional[float] = None

class DashboardSummaryResponse(BaseModel):
    total_companies: int
    total_market_cap: float
    sectors_count: int

class ClusterResponse(BaseModel):
    company_id: str
    cluster: int
    risk_grade: str
    sharpe: float
    cagr: float

class RecommendRequest(BaseModel):
    risk_profile: str = Field(..., description="Risk profile: Low, Moderate, High")

class Recommendation(BaseModel):
    scheme: str
    sharpe: float
    cagr: float
    volatility: float
    risk_grade: str

class RecommendResponse(BaseModel):
    recommendations: List[Recommendation]

class ScreenerParams(BaseModel):
    min_market_cap: Optional[float] = None
    max_market_cap: Optional[float] = None
    min_pe: Optional[float] = None
    max_pe: Optional[float] = None
    min_roe: Optional[float] = None
    sector: Optional[str] = None
