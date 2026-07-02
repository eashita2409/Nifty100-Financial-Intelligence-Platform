import sqlite3
import pandas as pd

conn = sqlite3.connect('data/db/nifty100.db')

# Investigate BEL's extreme ROE
for cid in ['BEL', 'HAL', 'INDIGO']:
    print(f"\n=== {cid} ===")
    raw = pd.read_sql(f"""
        SELECT p.company_id, p.year, p.net_profit,
               b.equity_capital, b.reserves,
               (b.equity_capital + b.reserves) as total_equity
        FROM profitandloss p
        JOIN balancesheet b ON p.company_id = b.company_id AND p.year = b.year
        WHERE p.company_id = '{cid}' AND p.year = 2024
    """, conn)
    print(raw.to_string(index=False))
    
    ratio = pd.read_sql(f"""
        SELECT company_id, year, return_on_equity_pct, debt_to_equity
        FROM financial_ratios
        WHERE company_id = '{cid}' AND year = 2024
    """, conn)
    print(ratio.to_string(index=False))
    
    # Manual check
    if len(raw) > 0:
        r = raw.iloc[0]
        manual_roe = (r['net_profit'] / (r['equity_capital'] + r['reserves'])) * 100
        print(f"Manual ROE = {r['net_profit']} / ({r['equity_capital']} + {r['reserves']}) * 100 = {manual_roe:.2f}%")

conn.close()
