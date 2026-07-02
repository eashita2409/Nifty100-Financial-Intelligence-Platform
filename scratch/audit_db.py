import sqlite3
import sys

conn = sqlite3.connect('data/db/nifty100.db')
cur = conn.cursor()

print("=" * 60)
print("STEP 2: DATABASE VERIFICATION")
print("=" * 60)

# 2a. Table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='financial_ratios'")
result = cur.fetchone()
print(f"\n[2a] financial_ratios table exists: {result is not None}")

# 2b. Row count
cur.execute("SELECT COUNT(*) FROM financial_ratios")
row_count = cur.fetchone()[0]
print(f"[2b] financial_ratios row count: {row_count} (requirement: >= 1100)")
print(f"     PASS: {row_count >= 1100}")

# 2c. Column listing
cur.execute("PRAGMA table_info(financial_ratios)")
columns = cur.fetchall()
col_names = [c[1] for c in columns]
print(f"\n[2c] Columns ({len(col_names)}):")
for c in col_names:
    print(f"     - {c}")

# 2d. Required KPI columns check
required_cols = [
    'company_id', 'year',
    'debt_to_equity', 'interest_coverage',
    'net_profit_margin_pct', 'operating_profit_margin_pct',
    'return_on_equity_pct', 'return_on_capital_employed_pct',
    'return_on_assets_pct', 'free_cash_flow_cr',
    'asset_turnover', 'current_ratio',
    'sector_relative_roce'
]
print(f"\n[2d] Required column check:")
for rc in required_cols:
    present = rc in col_names
    print(f"     {rc}: {'PRESENT' if present else 'MISSING'}")

# 2e. NULL check - is any column completely NULL?
print(f"\n[2e] NULL completeness check (column is 100% NULL = FAIL):")
kpi_cols = [c for c in col_names if c not in ('company_id', 'year')]
for col in kpi_cols:
    cur.execute(f"SELECT COUNT(*) FROM financial_ratios WHERE [{col}] IS NOT NULL")
    non_null = cur.fetchone()[0]
    status = "FAIL (ALL NULL)" if non_null == 0 else f"OK ({non_null}/{row_count} non-null)"
    print(f"     {col}: {status}")

# 2f. Sample data
print(f"\n[2f] Sample data (5 rows, latest year):")
cur.execute("""
    SELECT company_id, year, debt_to_equity, return_on_equity_pct, return_on_capital_employed_pct, net_profit_margin_pct
    FROM financial_ratios
    WHERE year = 2024
    LIMIT 5
""")
rows = cur.fetchall()
print(f"     {'company_id':<15} {'year':<6} {'D/E':<8} {'ROE%':<8} {'ROCE%':<8} {'NPM%':<8}")
for r in rows:
    print(f"     {str(r[0]):<15} {str(r[1]):<6} {str(r[2]):<8} {str(r[3]):<8} {str(r[4]):<8} {str(r[5]):<8}")

conn.close()
