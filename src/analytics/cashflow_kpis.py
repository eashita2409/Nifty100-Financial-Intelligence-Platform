import pandas as pd
import sqlite3
from typing import Optional
import numpy as np

def calculate_free_cash_flow(cfo: Optional[float], capex: Optional[float]) -> float:
    """
    Calculate Free Cash Flow.
    Assume CapEx is given as a positive number here (capital expenditures).
    FCF = CFO - CapEx
    """
    return (cfo or 0) - abs(capex or 0)

def calculate_cfo_quality_score(cfo: Optional[float], net_profit: Optional[float]) -> Optional[float]:
    """
    Calculate CFO Quality Score (CFO / Net Profit).
    """
    if not net_profit or net_profit == 0:
        return None
    return round((cfo or 0) / net_profit, 2)

def calculate_capex_intensity(capex: Optional[float], sales: Optional[float]) -> Optional[float]:
    """
    Calculate CapEx Intensity (CapEx / Sales).
    """
    if not sales or sales == 0:
        return None
    return round(abs(capex or 0) / sales, 2)

def calculate_fcf_conversion(fcf: Optional[float], net_profit: Optional[float]) -> Optional[float]:
    """
    Calculate FCF Conversion (FCF / Net Profit).
    """
    if not net_profit or net_profit == 0:
        return None
    return round((fcf or 0) / net_profit, 2)

def classify_capital_allocation(cfo: Optional[float], capex: Optional[float], fcf: Optional[float], financing_activity: Optional[float]) -> str:
    """
    Classify the Capital Allocation Pattern.
    """
    if cfo is None or cfo < 0:
        return "Cash Burn"
    
    _capex = abs(capex or 0)
    
    if _capex > (cfo or 0):
        return "Aggressive Expansion"
        
    if fcf is not None and fcf > 0 and financing_activity is not None and financing_activity < 0:
        return "Cash Cow / Returner"
        
    return "Stable / Moderate Reinvestment"

def generate_capital_allocation_report(db_path: str, output_csv: str):
    conn = sqlite3.connect(db_path)
    
    # We need cash_from_operations_cr and capex_cr from financial_ratios
    # financing_activity from cashflow
    # net_profit and sales from profitandloss
    
    query = """
    SELECT 
        fr.company_id, fr.year,
        fr.cash_from_operations_cr as cfo,
        fr.capex_cr as capex,
        c.financing_activity,
        p.net_profit,
        p.sales
    FROM financial_ratios fr
    LEFT JOIN cashflow c ON fr.company_id = c.company_id AND fr.year = c.year
    LEFT JOIN profitandloss p ON fr.company_id = p.company_id AND fr.year = p.year
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    results = []
    
    for _, row in df.iterrows():
        cfo = row['cfo']
        capex = row['capex']
        fin_act = row['financing_activity']
        np_val = row['net_profit']
        sales = row['sales']
        
        # Free Cash Flow
        fcf = calculate_free_cash_flow(cfo, capex)
        
        # CFO Quality Score
        cfo_quality = calculate_cfo_quality_score(cfo, np_val)
        
        # CapEx Intensity
        capex_int = calculate_capex_intensity(capex, sales)
        
        # FCF Conversion
        fcf_conv = calculate_fcf_conversion(fcf, np_val)
        
        # Classification
        pattern = classify_capital_allocation(cfo, capex, fcf, fin_act)
        
        results.append({
            'company_id': row['company_id'],
            'year': row['year'],
            'fcf': fcf,
            'cfo_quality_score': cfo_quality,
            'capex_intensity': capex_int,
            'fcf_conversion': fcf_conv,
            'capital_allocation_pattern': pattern
        })
        
    res_df = pd.DataFrame(results)
    
    import os
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    res_df.to_csv(output_csv, index=False)
    
def populate_cashflow_kpis(db_path: str):
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        fr.company_id, fr.year,
        fr.cash_from_operations_cr as cfo,
        fr.capex_cr as capex,
        c.financing_activity,
        p.net_profit,
        p.sales
    FROM financial_ratios fr
    LEFT JOIN cashflow c ON fr.company_id = c.company_id AND fr.year = c.year
    LEFT JOIN profitandloss p ON fr.company_id = p.company_id AND fr.year = p.year
    """
    
    df = pd.read_sql_query(query, conn)
    updates = []
    
    for _, row in df.iterrows():
        cfo = row['cfo']
        capex = row['capex']
        fin_act = row['financing_activity']
        np_val = row['net_profit']
        sales = row['sales']
        
        cfo_quality = calculate_cfo_quality_score(cfo, np_val)
        capex_int = calculate_capex_intensity(capex, sales)
        fcf = calculate_free_cash_flow(cfo, capex)
        fcf_conv = calculate_fcf_conversion(fcf, np_val)
        pattern = classify_capital_allocation(cfo, capex, fcf, fin_act)
        
        updates.append((
            cfo_quality, capex_int, fcf_conv, pattern,
            row['company_id'], row['year']
        ))
        
    cursor = conn.cursor()
    cursor.executemany("""
        UPDATE financial_ratios 
        SET cfo_quality_score = ?,
            capex_intensity = ?,
            fcf_conversion = ?,
            capital_allocation_pattern = ?
        WHERE company_id = ? AND year = ?
    """, updates)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    generate_capital_allocation_report('data/db/nifty100.db', 'output/capital_allocation.csv')
