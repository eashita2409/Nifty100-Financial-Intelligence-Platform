from pydantic import BaseModel, Field, root_validator, model_validator
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


class RecommendRequest(BaseModel):
    risk_profile: str = Field(..., description='Risk profile: Low, Moderate, High')

class Recommendation(BaseModel):
    scheme: str
    sharpe: float
    cagr: float
    volatility: float
    risk_grade: str

class RecommendResponse(BaseModel):
    recommendations: List[Recommendation]

class ProsConsResponse(BaseModel):
    company_id: str
    pros: List[Any]
    cons: List[Any]

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
