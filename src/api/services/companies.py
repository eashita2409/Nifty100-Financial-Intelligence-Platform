import sqlite3
from typing import List, Optional
from ..utils import check_company_exists
from ..schemas import CompanyBase, PeerComparison, SectorSummary, ScreenerParams

def get_all_companies(conn: sqlite3.Connection) -> List[dict]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.company_name as name, c.nse_profile as nse_ticker, c.bse_profile as bse_ticker,
               s.broad_sector, s.sub_sector,
               (SELECT market_cap_crore FROM market_cap WHERE company_id = c.id ORDER BY year DESC LIMIT 1) as market_cap_cr,
               (SELECT close_price FROM stock_prices WHERE company_id = c.id ORDER BY date DESC LIMIT 1) as current_price
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
    """)
    return [dict(row) for row in cursor.fetchall()]

def get_company(conn: sqlite3.Connection, ticker: str) -> dict:
    check_company_exists(conn, ticker)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.company_name as name, c.nse_profile as nse_ticker, c.bse_profile as bse_ticker,
               s.broad_sector, s.sub_sector,
               (SELECT market_cap_crore FROM market_cap WHERE company_id = c.id ORDER BY year DESC LIMIT 1) as market_cap_cr,
               (SELECT close_price FROM stock_prices WHERE company_id = c.id ORDER BY date DESC LIMIT 1) as current_price
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        WHERE c.id = ?
    """, (ticker,))
    return dict(cursor.fetchone())

def get_peers(conn: sqlite3.Connection, ticker: str) -> dict:
    check_company_exists(conn, ticker)
    cursor = conn.cursor()
    
    cursor.execute("SELECT broad_sector FROM sectors WHERE company_id = ?", (ticker,))
    row = cursor.fetchone()
    sector = row['broad_sector'] if row else ""
    
    query = """
    SELECT c.id as company_id, 
           (SELECT market_cap_crore FROM market_cap WHERE company_id = c.id ORDER BY year DESC LIMIT 1) as market_cap_cr,
           (SELECT pe_ratio FROM market_cap WHERE company_id = c.id ORDER BY year DESC LIMIT 1) as pe_ratio,
           (SELECT return_on_equity_pct FROM financial_ratios WHERE company_id = c.id ORDER BY year DESC LIMIT 1) as roe
    FROM companies c
    JOIN sectors s ON c.id = s.company_id
    WHERE s.broad_sector = ?
    """
    cursor.execute(query, (sector,))
    peers = [dict(r) for r in cursor.fetchall()]
    return {"sector": sector, "peers": peers}

def get_sector_summary(conn: sqlite3.Connection, sector: str) -> dict:
    cursor = conn.cursor()
    
    query = """
    SELECT COUNT(c.id) as company_count,
           AVG((SELECT pe_ratio FROM market_cap WHERE company_id = c.id ORDER BY year DESC LIMIT 1)) as avg_pe,
           AVG((SELECT return_on_equity_pct FROM financial_ratios WHERE company_id = c.id ORDER BY year DESC LIMIT 1)) as avg_roe
    FROM companies c
    JOIN sectors s ON c.id = s.company_id
    WHERE s.broad_sector = ? COLLATE NOCASE
    """
    cursor.execute(query, (sector,))
    row = cursor.fetchone()
    
    return {
        "sector": sector,
        "company_count": row['company_count'] if row and row['company_count'] else 0,
        "avg_pe": row['avg_pe'] if row else None,
        "avg_roe": row['avg_roe'] if row else None
    }

def screener(conn: sqlite3.Connection, params: ScreenerParams) -> List[dict]:
    cursor = conn.cursor()
    
    query = """
    SELECT c.id, c.company_name as name, c.nse_profile as nse_ticker, c.bse_profile as bse_ticker,
           s.broad_sector, s.sub_sector,
           (SELECT market_cap_crore FROM market_cap WHERE company_id = c.id ORDER BY year DESC LIMIT 1) as market_cap_cr,
           (SELECT close_price FROM stock_prices WHERE company_id = c.id ORDER BY date DESC LIMIT 1) as current_price
    FROM companies c
    LEFT JOIN sectors s ON c.id = s.company_id
    WHERE 1=1
    """
    
    sql_params = []
    
    if params.sector:
        query += " AND s.broad_sector = ? COLLATE NOCASE"
        sql_params.append(params.sector)
        
    if params.min_market_cap is not None:
        query += " AND (SELECT market_cap_crore FROM market_cap WHERE company_id = c.id ORDER BY year DESC LIMIT 1) >= ?"
        sql_params.append(params.min_market_cap)
        
    if params.max_market_cap is not None:
        query += " AND (SELECT market_cap_crore FROM market_cap WHERE company_id = c.id ORDER BY year DESC LIMIT 1) <= ?"
        sql_params.append(params.max_market_cap)
        
    if params.min_pe is not None or params.max_pe is not None:
        if params.min_pe is not None:
            query += " AND (SELECT pe_ratio FROM market_cap WHERE company_id = c.id ORDER BY year DESC LIMIT 1) >= ?"
            sql_params.append(params.min_pe)
        if params.max_pe is not None:
            query += " AND (SELECT pe_ratio FROM market_cap WHERE company_id = c.id ORDER BY year DESC LIMIT 1) <= ?"
            sql_params.append(params.max_pe)
            
    if params.min_roe is not None:
        query += " AND (SELECT return_on_equity_pct FROM financial_ratios WHERE company_id = c.id ORDER BY year DESC LIMIT 1) >= ?"
        sql_params.append(params.min_roe)
        
    cursor.execute(query, sql_params)
    return [dict(row) for row in cursor.fetchall()]
