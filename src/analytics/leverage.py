import sqlite3
import pandas as pd
from typing import Optional
from pathlib import Path
import logging

edge_log_path = Path("output/ratio_edge_cases.log")
edge_log_path.parent.mkdir(parents=True, exist_ok=True)
edge_logger = logging.getLogger("LeverageEdgeCases")
edge_logger.setLevel(logging.INFO)
if edge_logger.hasHandlers():
    edge_logger.handlers.clear()
edge_fh = logging.FileHandler(edge_log_path)
edge_fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
edge_logger.addHandler(edge_fh)

def calculate_debt_to_equity(borrowings: Optional[float], equity_capital: Optional[float], reserves: Optional[float]) -> Optional[float]:
    """Calculate Debt to Equity Ratio."""
    denominator = (equity_capital or 0) + (reserves or 0)
    if denominator <= 0:
        return None
    return round((borrowings or 0) / denominator, 2)

def is_high_leverage(debt_to_equity: Optional[float], threshold: float = 2.0, is_financial: bool = False, company_id: Optional[str] = None, year: Optional[float] = None) -> bool:
    """Flag if Debt to Equity exceeds threshold."""
    if is_financial:
        if company_id and year and debt_to_equity and debt_to_equity > threshold:
            edge_logger.info(f"Anomaly Category: Leverage_Financials | {company_id} ({year}) | High Leverage warning suppressed for Financial sector (D/E: {debt_to_equity}).")
        return False
    if debt_to_equity is None:
        return False
    return debt_to_equity > threshold

def calculate_interest_coverage_ratio(ebit: Optional[float], interest: Optional[float]) -> Optional[float]:
    """Calculate Interest Coverage Ratio."""
    if not interest or interest <= 0:
        return None
    return round((ebit or 0) / interest, 2)

def is_icr_warning(icr: Optional[float], threshold: float = 1.5, is_financial: bool = False, company_id: Optional[str] = None, year: Optional[float] = None) -> bool:
    """Flag if Interest Coverage Ratio is below safe threshold."""
    if is_financial:
        if company_id and year and icr is not None and icr < threshold:
            edge_logger.info(f"Anomaly Category: Leverage_Financials | {company_id} ({year}) | ICR warning suppressed for Financial sector (ICR: {icr}).")
        return False
    if icr is None:
        # If ICR is None (e.g., zero interest), it's not a warning by default.
        return False
    return icr < threshold

def is_debt_free(borrowings: Optional[float], threshold: float = 0.5) -> bool:
    """Label as Debt Free if borrowings are strictly negligible."""
    if borrowings is None:
        return True
    return borrowings <= threshold

def calculate_net_debt(borrowings: Optional[float], cash_equivalents: Optional[float] = 0.0) -> float:
    """Calculate Net Debt (Borrowings - Cash & Equivalents)."""
    return max((borrowings or 0) - (cash_equivalents or 0), 0.0)

def calculate_asset_turnover(sales: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """Calculate Asset Turnover Ratio."""
    if not total_assets or total_assets <= 0:
        return None
    return round((sales or 0) / total_assets, 2)

def populate_leverage_ratios(db_path: str):
    """Fetch base data, compute leverage & efficiency ratios, and update financial_ratios."""
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        p.company_id, p.year, p.sales, p.profit_before_tax, p.interest,
        b.equity_capital, b.reserves, b.borrowings, b.total_assets,
        s.broad_sector
    FROM profitandloss p
    LEFT JOIN balancesheet b ON p.company_id = b.company_id AND p.year = b.year
    LEFT JOIN sectors s ON p.company_id = s.company_id
    """
    
    df = pd.read_sql_query(query, conn)
    updates = []
    
    for _, row in df.iterrows():
        is_financial = row['broad_sector'] == 'Financials'
        
        dte = calculate_debt_to_equity(row['borrowings'], row['equity_capital'], row['reserves'])
        hl_flag = is_high_leverage(dte, is_financial=is_financial, company_id=row['company_id'], year=row['year'])
        
        ebit = (row['profit_before_tax'] or 0) + (row['interest'] or 0)
        icr = calculate_interest_coverage_ratio(ebit, row['interest'])
        icr_warn = is_icr_warning(icr, is_financial=is_financial, company_id=row['company_id'], year=row['year'])
        
        df_label = is_debt_free(row['borrowings'])
        
        # We assume 0 for cash equivalents as it's not explicitly available in standard balancesheet
        nd = calculate_net_debt(row['borrowings'], 0.0)
        
        at = calculate_asset_turnover(row['sales'], row['total_assets'])
        
        updates.append((
            dte, hl_flag, icr, df_label, icr_warn, nd, at,
            row['company_id'], row['year']
        ))
        
    cursor = conn.cursor()
    cursor.executemany("""
        UPDATE financial_ratios 
        SET debt_to_equity = ?,
            high_leverage_flag = ?,
            interest_coverage = ?,
            debt_free_label = ?,
            icr_warning_flag = ?,
            net_debt_cr = ?,
            asset_turnover = ?
        WHERE company_id = ? AND year = ?
    """, updates)
    
    conn.commit()
    conn.close()
