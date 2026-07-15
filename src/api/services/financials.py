import sqlite3
from typing import List, Dict, Any
from ..utils import check_company_exists

def get_financial_ratios(conn: sqlite3.Connection, ticker: str) -> List[Dict[str, Any]]:
    check_company_exists(conn, ticker)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT year, return_on_equity_pct, return_on_capital_employed_pct, 
               debt_to_equity, free_cash_flow_cr, revenue_cagr_5yr, 
               pat_cagr_5yr, capital_allocation_pattern 
        FROM financial_ratios 
        WHERE company_id = ? ORDER BY year
    """, (ticker,))
    return [dict(row) for row in cursor.fetchall()]

def get_valuation(conn: sqlite3.Connection, ticker: str) -> List[Dict[str, Any]]:
    check_company_exists(conn, ticker)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT year, pe_ratio, pb_ratio, ev_ebitda as ev_to_ebitda 
        FROM market_cap 
        WHERE company_id = ? ORDER BY year
    """, (ticker,))
    return [dict(row) for row in cursor.fetchall()]

def get_cashflow(conn: sqlite3.Connection, ticker: str) -> List[Dict[str, Any]]:
    check_company_exists(conn, ticker)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.year, c.operating_activity as operating_cash_flow, 
               f.capex_cr as capex, f.free_cash_flow_cr as free_cash_flow
        FROM cashflow c
        LEFT JOIN financial_ratios f ON c.company_id = f.company_id AND c.year = f.year
        WHERE c.company_id = ? ORDER BY c.year
    """, (ticker,))
    return [dict(row) for row in cursor.fetchall()]

def get_balance_sheet(conn: sqlite3.Connection, ticker: str) -> List[Dict[str, Any]]:
    check_company_exists(conn, ticker)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT year, total_assets, equity_capital, reserves, borrowings 
        FROM balancesheet 
        WHERE company_id = ? ORDER BY year
    """, (ticker,))
    return [dict(row) for row in cursor.fetchall()]

def get_profit_loss(conn: sqlite3.Connection, ticker: str) -> List[Dict[str, Any]]:
    check_company_exists(conn, ticker)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT year, sales, operating_profit, net_profit 
        FROM profitandloss 
        WHERE company_id = ? ORDER BY year
    """, (ticker,))
    return [dict(row) for row in cursor.fetchall()]
