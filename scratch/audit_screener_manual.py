import sqlite3
import pandas as pd
import math

conn = sqlite3.connect('data/db/nifty100.db')

print("=" * 60)
print("STEP 5: SCREENER VALIDATION (ROE > 15 AND D/E < 1)")
print("=" * 60)

query = """
SELECT c.company_name, f.company_id, f.return_on_equity_pct as roe, f.debt_to_equity as de
FROM financial_ratios f
JOIN companies c ON f.company_id = c.id
WHERE f.year = 2024
  AND f.return_on_equity_pct > 15
  AND f.debt_to_equity < 1
ORDER BY f.return_on_equity_pct DESC
"""
screener_df = pd.read_sql(query, conn)
print(f"\nResult count: {len(screener_df)}")
print(f"\nFirst 10 companies:")
print(screener_df.head(10).to_string(index=False))

# Cross-check against saved CSV
saved = pd.read_csv('output/screener_preview.csv')
print(f"\nSaved screener_preview.csv row count: {len(saved)}")

print("\n" + "=" * 60)
print("STEP 6: MANUAL VALIDATION")
print("=" * 60)

companies = ['TCS', 'INFY', 'RELIANCE']

for cid in companies:
    print(f"\n--- {cid} ---")
    
    # Get raw financial data
    raw = pd.read_sql(f"""
        SELECT p.company_id, p.year, p.net_profit, p.sales,
               b.equity_capital, b.reserves
        FROM profitandloss p
        JOIN balancesheet b ON p.company_id = b.company_id AND p.year = b.year
        WHERE p.company_id = '{cid}' AND p.year IN (2019, 2024)
        ORDER BY p.year
    """, conn)
    
    # Get database computed values
    db_vals = pd.read_sql(f"""
        SELECT company_id, year, return_on_equity_pct as roe
        FROM financial_ratios
        WHERE company_id = '{cid}' AND year = 2024
    """, conn)
    
    # Get KPI summary values
    kpi = pd.read_csv('output/kpi_summary.csv')
    kpi_row = kpi[kpi['company_id'] == cid]
    
    if len(raw) >= 2:
        row_2024 = raw[raw['year'] == 2024.0].iloc[0]
        row_2019 = raw[raw['year'] == 2019.0].iloc[0]
        
        # Manual ROE calc
        equity = row_2024['equity_capital'] + row_2024['reserves']
        manual_roe = round((row_2024['net_profit'] / equity) * 100, 2)
        db_roe = db_vals.iloc[0]['roe'] if len(db_vals) > 0 else None
        roe_diff = abs(manual_roe - db_roe) if db_roe else None
        
        # Manual 5-year revenue CAGR
        sales_2024 = row_2024['sales']
        sales_2019 = row_2019['sales']
        if sales_2019 and sales_2019 > 0:
            manual_cagr = round(((sales_2024 / sales_2019) ** (1/5) - 1) * 100, 2)
        else:
            manual_cagr = None
        
        kpi_cagr = kpi_row.iloc[0]['five_year_cagr'] if len(kpi_row) > 0 else None
        
        print(f"  Net Profit 2024:     {row_2024['net_profit']:,.0f}")
        print(f"  Equity 2024:         {equity:,.0f} (Cap: {row_2024['equity_capital']:,.0f} + Res: {row_2024['reserves']:,.0f})")
        print(f"  Sales 2019:          {sales_2019:,.0f}")
        print(f"  Sales 2024:          {sales_2024:,.0f}")
        print(f"")
        print(f"  Manual ROE:          {manual_roe}%")
        print(f"  DB ROE:              {db_roe}%")
        print(f"  ROE Difference:      {roe_diff}pp {'PASS' if roe_diff and roe_diff < 0.1 else 'CHECK' if roe_diff else 'N/A'}")
        print(f"")
        print(f"  Manual 5yr CAGR:     {manual_cagr}%")
        print(f"  KPI 5yr CAGR:        {kpi_cagr}%")
        if manual_cagr and kpi_cagr and not math.isnan(kpi_cagr):
            cagr_diff = abs(manual_cagr - kpi_cagr)
            print(f"  CAGR Difference:     {cagr_diff:.2f}pp {'PASS' if cagr_diff < 1.0 else 'INVESTIGATE'}")
            print(f"  NOTE: CAGR in KPI comes from analysis table (integer-rounded source)")
        else:
            print(f"  CAGR Difference:     N/A (source data missing for this company)")

conn.close()
