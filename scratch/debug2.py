import pandas as pd
import sqlite3
conn = sqlite3.connect('data/db/nifty100.db')
pnl = pd.read_sql_query("SELECT company_id, year, sales, net_profit, eps, opm_percentage as operating_margin FROM profitandloss", conn)
ratios = pd.read_sql_query("SELECT company_id, year, debt_to_equity, interest_coverage, net_profit_margin_pct as net_margin, free_cash_flow_cr as fcf, return_on_equity_pct as roe, return_on_capital_employed_pct as roce FROM financial_ratios", conn)
merged = pnl.merge(ratios, on=['company_id', 'year'], how='outer')
print("merged rows for INFY 2024:", merged[(merged['company_id']=='INFY') & (merged['year']==2024)][['company_id', 'year', 'sales', 'roe', 'roce']])
