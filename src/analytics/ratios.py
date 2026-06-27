import logging
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple

# Setup logging for OPM cross-checks
log_file_path = Path("output/opm_crosscheck.log")
log_file_path.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("ProfitabilityRatios")
logger.setLevel(logging.INFO)

# To avoid adding multiple handlers during testing, we clear existing ones
if logger.hasHandlers():
    logger.handlers.clear()

fh = logging.FileHandler(log_file_path)
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

edge_log_path = Path("output/ratio_edge_cases.log")
edge_logger = logging.getLogger("RatioEdgeCases")
edge_logger.setLevel(logging.INFO)
if edge_logger.hasHandlers():
    edge_logger.handlers.clear()
edge_fh = logging.FileHandler(edge_log_path)
edge_fh.setFormatter(formatter)
edge_logger.addHandler(edge_fh)

def calculate_net_profit_margin(net_profit: Optional[float], sales: Optional[float]) -> Optional[float]:
    """Calculate Net Profit Margin."""
    if not sales or sales == 0:
        return None
    return round(((net_profit or 0) / sales) * 100, 2)

def calculate_operating_profit_margin(operating_profit: Optional[float], sales: Optional[float], opm_percentage_source: Optional[float] = None, company_id: Optional[str] = None, year: Optional[float] = None) -> Optional[float]:
    """Calculate Operating Profit Margin and log mismatch against source."""
    if not sales or sales == 0:
        return None
    calculated = round(((operating_profit or 0) / sales) * 100, 2)
    
    if opm_percentage_source is not None:
        if abs(calculated - opm_percentage_source) > 1.0:
            logger.info(f"OPM Mismatch: {company_id} ({year}) - Calculated: {calculated}%, Source: {opm_percentage_source}%")
            
    return calculated

def calculate_return_on_equity(net_profit: Optional[float], equity_capital: Optional[float], reserves: Optional[float]) -> Optional[float]:
    """Calculate Return on Equity."""
    denominator = (equity_capital or 0) + (reserves or 0)
    if denominator <= 0:
        return None
    return round(((net_profit or 0) / denominator) * 100, 2)

def calculate_return_on_capital_employed(ebit: Optional[float], equity_capital: Optional[float], reserves: Optional[float], borrowings: Optional[float], is_financial_sector: bool = False, company_id: Optional[str] = None, year: Optional[float] = None) -> Tuple[Optional[float], bool]:
    """Calculate Return on Capital Employed."""
    if is_financial_sector:
        if company_id and year:
            edge_logger.info(f"Anomaly Category: ROCE_Financials | {company_id} ({year}) | Bank ROCE is not applicable. Skipped.")
        return None, True
        
    denominator = (equity_capital or 0) + (reserves or 0) + (borrowings or 0)
    if denominator == 0:
        return None, False
        
    return round(((ebit or 0) / denominator) * 100, 2), False

def calculate_return_on_assets(net_profit: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """Calculate Return on Assets."""
    if not total_assets or total_assets == 0:
        return None
    return round(((net_profit or 0) / total_assets) * 100, 2)

def populate_profitability_ratios(db_path: str):
    """Fetch base data, compute ratios, and update the financial_ratios table."""
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        p.company_id, p.year, p.sales, p.operating_profit, p.opm_percentage, 
        p.net_profit, p.profit_before_tax, p.interest,
        b.equity_capital, b.reserves, b.borrowings, b.total_assets,
        s.broad_sector
    FROM profitandloss p
    LEFT JOIN balancesheet b ON p.company_id = b.company_id AND p.year = b.year
    LEFT JOIN sectors s ON p.company_id = s.company_id
    """
    
    df = pd.read_sql_query(query, conn)
    updates = []
    
    for _, row in df.iterrows():
        npm = calculate_net_profit_margin(row['net_profit'], row['sales'])
        
        opm = calculate_operating_profit_margin(
            row['operating_profit'], row['sales'], row['opm_percentage'], 
            row['company_id'], row['year']
        )
        
        roe = calculate_return_on_equity(row['net_profit'], row['equity_capital'], row['reserves'])
        
        ebit = (row['profit_before_tax'] or 0) + (row['interest'] or 0)
        is_financial = row['broad_sector'] == 'Financials'
        
        roce, sector_rel = calculate_return_on_capital_employed(
            ebit, row['equity_capital'], row['reserves'], row['borrowings'], is_financial, row['company_id'], row['year']
        )
        
        roa = calculate_return_on_assets(row['net_profit'], row['total_assets'])
        
        updates.append((
            npm, opm, roe, roce, roa, sector_rel,
            row['company_id'], row['year']
        ))
        
    cursor = conn.cursor()
    cursor.executemany("""
        UPDATE financial_ratios 
        SET net_profit_margin_pct = ?,
            operating_profit_margin_pct = ?,
            return_on_equity_pct = ?,
            return_on_capital_employed_pct = ?,
            return_on_assets_pct = ?,
            sector_relative_roce = ?
        WHERE company_id = ? AND year = ?
    """, updates)
    
    conn.commit()
    conn.close()
