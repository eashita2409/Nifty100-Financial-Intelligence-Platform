import sqlite3
import pandas as pd
from src.screener.engine import ScreenerEngine

engine = ScreenerEngine()
db_path = 'data/db/nifty100.db'
df = engine.fetch_data(db_path)

print("Columns in fetched data:", df.columns.tolist())
print("Null counts:")
print(df[['roe', 'roce', 'debt_equity', 'fcf', 'five_year_cagr', 'pat_cagr_5yr', 'eps_cagr', 'operating_margin', 'pe', 'pb']].isna().sum())

# Let's inspect raw values in financial_ratios table
conn = sqlite3.connect(db_path)
ratios = pd.read_sql_query("SELECT company_id, year, revenue_cagr_5yr, pat_cagr_5yr, eps_cagr_5yr FROM financial_ratios WHERE year = 2024.0 LIMIT 10", conn)
print("Raw CAGRs in DB for year 2024:")
print(ratios)
conn.close()
