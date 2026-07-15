from fastapi import APIRouter, Depends
import sqlite3
from ..database import get_db
from ..schemas import RatiosResponse, ValuationResponse, CashflowResponse, BalanceSheetResponse, ProfitLossResponse
from ..services import financials as fin_service
from ..utils import handle_db_error

router = APIRouter(tags=["Financials"])

@router.get("/ratios/{ticker}", response_model=RatiosResponse)
def get_ratios(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        ratios = fin_service.get_financial_ratios(db, ticker)
        return {"company_id": ticker, "ratios": ratios}
    except sqlite3.Error as e:
        handle_db_error(e)

@router.get("/valuation/{ticker}", response_model=ValuationResponse)
def get_valuation(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        valuations = fin_service.get_valuation(db, ticker)
        return {"company_id": ticker, "valuations": valuations}
    except sqlite3.Error as e:
        handle_db_error(e)

@router.get("/cashflow/{ticker}", response_model=CashflowResponse)
def get_cashflow(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        cashflows = fin_service.get_cashflow(db, ticker)
        return {"company_id": ticker, "cashflows": cashflows}
    except sqlite3.Error as e:
        handle_db_error(e)

@router.get("/balance-sheet/{ticker}", response_model=BalanceSheetResponse)
def get_balance_sheet(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        balance_sheets = fin_service.get_balance_sheet(db, ticker)
        return {"company_id": ticker, "balance_sheets": balance_sheets}
    except sqlite3.Error as e:
        handle_db_error(e)

@router.get("/profit-loss/{ticker}", response_model=ProfitLossResponse)
def get_profit_loss(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        profit_loss = fin_service.get_profit_loss(db, ticker)
        return {"company_id": ticker, "profit_loss": profit_loss}
    except sqlite3.Error as e:
        handle_db_error(e)
