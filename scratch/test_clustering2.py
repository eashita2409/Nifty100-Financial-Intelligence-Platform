import pandas as pd
import sqlite3
conn = sqlite3.connect('data/db/nifty100.db')
query = """
SELECT 
    fr.company_id,
    s.broad_sector as sector,
    fr.year,
    fr.return_on_equity_pct,
    fr.debt_to_equity,
    fr.revenue_cagr_5yr,
    fr.operating_profit_margin_pct,
    fr.free_cash_flow_cr
FROM financial_ratios fr
LEFT JOIN sectors s ON fr.company_id = s.company_id
ORDER BY fr.company_id, fr.year
"""
df = pd.read_sql_query(query, conn)
df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()

latest = df.sort_values('year').groupby('company_id').tail(1).copy()
print("Sectors missing:", latest['sector'].isna().sum())
print("NaNs before impute:", latest[['return_on_equity_pct', 'debt_to_equity', 'revenue_cagr_5yr', 'operating_profit_margin_pct']].isna().sum())

print("Unique sectors:", latest['sector'].unique())

