import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import os

def run_valuation():
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    db_path = project_root / "data" / "db" / "nifty100.db"
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    
    companies = pd.read_sql_query("SELECT id as company_id, company_name FROM companies", conn)
    sectors = pd.read_sql_query("SELECT company_id, broad_sector as sector FROM sectors", conn)
    
    mc_df = pd.read_sql_query("SELECT * FROM market_cap", conn)
    latest_year_mc = mc_df['year'].max()
    mc_latest = mc_df[mc_df['year'] == latest_year_mc]
    
    ratios_df = pd.read_sql_query("SELECT company_id, year, free_cash_flow_cr FROM financial_ratios", conn)
    ratios_df = ratios_df.dropna(subset=['year'])
    latest_year_ratios = ratios_df['year'].max()
    ratios_latest = ratios_df[ratios_df['year'] == latest_year_ratios]
    
    conn.close()
    
    df = companies.merge(sectors, on='company_id', how='left')
    df = df.merge(mc_latest[['company_id', 'market_cap_crore', 'pe_ratio', 'pb_ratio', 'ev_ebitda']], on='company_id', how='left')
    df = df.merge(ratios_latest[['company_id', 'free_cash_flow_cr']], on='company_id', how='left')
    
    df['FCF_yield_pct'] = np.where(
        (df['market_cap_crore'].isna()) | (df['market_cap_crore'] <= 0) | (df['free_cash_flow_cr'].isna()),
        np.nan,
        (df['free_cash_flow_cr'] / df['market_cap_crore']) * 100
    )
    
    sector_medians = df.groupby('sector')['pe_ratio'].median().reset_index()
    sector_medians.rename(columns={'pe_ratio': 'sector_median_PE'}, inplace=True)
    
    df = df.merge(sector_medians, on='sector', how='left')
    
    df['PE_vs_sector_median_pct'] = np.where(
        (df['pe_ratio'].isna()) | (df['sector_median_PE'].isna()) | (df['sector_median_PE'] <= 0),
        np.nan,
        ((df['pe_ratio'] / df['sector_median_PE']) - 1) * 100
    )
    
    def get_flag(pe, median_pe):
        if pd.isna(pe) or pd.isna(median_pe) or median_pe <= 0:
            return "Unknown"
        if pe > 1.5 * median_pe:
            return "Caution"
        elif pe < 0.7 * median_pe:
            return "Discount"
        else:
            return "Fair"
            
    df['flag'] = df.apply(lambda row: get_flag(row['pe_ratio'], row['sector_median_PE']), axis=1)
    
    df.rename(columns={'pe_ratio': 'PE', 'pb_ratio': 'PB', 'ev_ebitda': 'EV_EBITDA'}, inplace=True)
    
    columns_to_export = [
        'company_id', 'company_name', 'sector', 'PE', 'PB', 'EV_EBITDA', 
        'FCF_yield_pct', 'sector_median_PE', 'PE_vs_sector_median_pct', 'flag'
    ]
    summary_df = df[columns_to_export]
    
    excel_path = output_dir / "valuation_summary.xlsx"
    summary_df.to_excel(excel_path, index=False)
    print(f"Generated {excel_path}")
    
    flags_df = summary_df[summary_df['flag'].isin(['Caution', 'Discount'])]
    csv_path = output_dir / "valuation_flags.csv"
    flags_df.to_csv(csv_path, index=False)
    print(f"Generated {csv_path}")

if __name__ == "__main__":
    run_valuation()
