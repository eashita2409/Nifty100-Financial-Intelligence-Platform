import pandas as pd
import sqlite3
conn = sqlite3.connect('data/db/nifty100.db')
ratios = pd.read_sql_query('SELECT company_id, year, return_on_equity_pct as roe, return_on_capital_employed_pct as roce FROM financial_ratios WHERE company_id="INFY" AND year=2024', conn)
print(ratios)
df = pd.read_csv('output/kpi_summary.csv')
print(df[df['company_id'] == 'INFY'][['company_id', 'roe', 'roce']])
