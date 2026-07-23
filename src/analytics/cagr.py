import sqlite3
import pandas as pd
from typing import Optional, Tuple

from typing import Union
def calculate_cagr(start_val: Optional[float], end_val: Optional[float], years: int) -> Tuple[Union[float, str, None], Optional[str]]:
    """
    Calculate Compound Annual Growth Rate and return a tuple of (CAGR_pct, anomaly_flag).
    
    Handles:
    - Positive -> Positive
    - Positive -> Negative
    - Negative -> Positive
    - Negative -> Negative
    - Zero Base
    - Insufficient History
    """
    if years <= 0 or start_val is None or end_val is None:
        return None, "insufficient_history"
        
    if start_val == 0:
        return None, "zero_base"
        
    if start_val > 0 and end_val > 0:
        cagr = ((end_val / start_val) ** (1 / years)) - 1
        return round(cagr * 100, 2), None
        
    if start_val > 0 and end_val < 0:
        return None, "positive_to_negative"
        
    if start_val < 0 and end_val > 0:
        return 'TURNAROUND', "negative_to_positive"
        
    if start_val < 0 and end_val < 0:
        return None, "negative_to_negative"
        
    if start_val > 0 and end_val == 0:
        return -100.0, None # mathematically sound, 100% loss
        
    if start_val < 0 and end_val == 0:
        return None, "negative_to_zero"
        
    return None, "unknown"


def populate_cagr_metrics(db_path: str):
    """
    Computes 3, 5, and 10 year CAGRs for Revenue, PAT, and EPS.
    Updates the financial_ratios table.
    """
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT company_id, year, sales, net_profit, eps
    FROM profitandloss
    ORDER BY company_id, year
    """
    df = pd.read_sql_query(query, conn)
    
    # We will create a dictionary to look up historical values easily
    # Dict structure: (company_id, year) -> { 'sales': X, 'net_profit': Y, 'eps': Z }
    history = {}
    for _, row in df.iterrows():
        history[(row['company_id'], row['year'])] = {
            'sales': row['sales'],
            'net_profit': row['net_profit'],
            'eps': row['eps']
        }
    
    updates = []
    
    for _, row in df.iterrows():
        cid = row['company_id']
        curr_year = row['year']
        
        cagrs = {}
        for metric in ['sales', 'net_profit', 'eps']:
            curr_val = row[metric]
            
            for years in [3, 5, 10]:
                hist_year = curr_year - years
                hist_data = history.get((cid, hist_year))
                
                if hist_data is not None:
                    hist_val = hist_data[metric]
                    cagr_val, flag = calculate_cagr(hist_val, curr_val, years)
                else:
                    cagr_val, flag = calculate_cagr(None, curr_val, years)
                    
                cagrs[f"{metric}_{years}yr"] = cagr_val
                cagrs[f"{metric}_{years}yr_flag"] = flag
        
        # We need to consolidate flags per metric across the years, 
        # or we just store the most recent anomaly (or any anomaly if there's one).
        # Wait, we have one flag column per metric: revenue_cagr_anomaly, pat_cagr_anomaly, eps_cagr_anomaly
        # The prompt says: "Store flag columns". It implies one flag per metric or one per period.
        # Since I added `revenue_cagr_anomaly`, `pat_cagr_anomaly`, `eps_cagr_anomaly`, 
        # I'll store a combined string of anomalies for 3/5/10, or just the 3yr one, 
        # or if any of them is an anomaly, store it.
        # Let's combine them, e.g., "3yr:zero_base, 5yr:positive_to_negative"
        
        def combine_flags(metric_name):
            flags = []
            for y in [3, 5, 10]:
                f = cagrs[f"{metric_name}_{y}yr_flag"]
                if f is not None:
                    flags.append(f"{y}yr:{f}")
            return ", ".join(flags) if flags else None
            
        rev_anomaly = combine_flags('sales')
        pat_anomaly = combine_flags('net_profit')
        eps_anomaly = combine_flags('eps')
        
        updates.append((
            cagrs['sales_3yr'], cagrs['sales_5yr'], cagrs['sales_10yr'], rev_anomaly,
            cagrs['net_profit_3yr'], cagrs['net_profit_5yr'], cagrs['net_profit_10yr'], pat_anomaly,
            cagrs['eps_3yr'], cagrs['eps_5yr'], cagrs['eps_10yr'], eps_anomaly,
            cid, curr_year
        ))
        
    cursor = conn.cursor()
    cursor.executemany("""
        UPDATE financial_ratios
        SET revenue_cagr_3yr = ?, revenue_cagr_5yr = ?, revenue_cagr_10yr = ?, revenue_cagr_anomaly = ?,
            pat_cagr_3yr = ?, pat_cagr_5yr = ?, pat_cagr_10yr = ?, pat_cagr_anomaly = ?,
            eps_cagr_3yr = ?, eps_cagr_5yr = ?, eps_cagr_10yr = ?, eps_cagr_anomaly = ?
        WHERE company_id = ? AND year = ?
    """, updates)
    
    conn.commit()
    conn.close()
