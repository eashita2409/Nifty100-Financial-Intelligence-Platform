import sqlite3
import pandas as pd

conn = sqlite3.connect('data/db/nifty100.db')
query = """
SELECT r.company_id, r.return_on_equity_pct, a.compounded_sales_growth
FROM financial_ratios r
JOIN analysis a ON r.company_id = a.company_id
WHERE r.company_id IN ('TCS', 'INFY', 'RELIANCE') AND r.year = 2024
"""
df = pd.read_sql(query, conn)
print(df)
