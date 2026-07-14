"""
Detailed validation: valuation outputs + company search + edge cases
"""
import sys, os, time, sqlite3
import pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from streamlit.testing.v1 import AppTest

# -------------------------------------------------------
# 1. Validate valuation outputs
# -------------------------------------------------------
print("="*60)
print("VALUATION OUTPUT VALIDATION")
print("="*60)

xlsx_path = 'output/valuation_summary.xlsx'
csv_path  = 'output/valuation_flags.csv'

# Excel check
try:
    df_xl = pd.read_excel(xlsx_path)
    print(f"valuation_summary.xlsx: {len(df_xl)} rows, {list(df_xl.columns)}")
    print(f"  Flags: {df_xl['flag'].value_counts().to_dict()}")
    # Show sample rows for test companies
    for name in ['Tata Consultancy', 'Infosys', 'Reliance', 'HDFC Bank', 'ITC']:
        row = df_xl[df_xl['company_name'].str.contains(name, case=False, na=False)]
        if not row.empty:
            r = row.iloc[0]
            print(f"  {r['company_name']}: PE={r['PE']}, Sector_median_PE={r['sector_median_PE']:.2f}, Flag={r['flag']}, FCF_yield={r.get('FCF_yield_pct','N/A')}")
except Exception as e:
    print(f"  ERROR reading xlsx: {e}")

# CSV check
try:
    df_csv = pd.read_csv(csv_path)
    print(f"\nvaluation_flags.csv: {len(df_csv)} rows")
    print(f"  Flags: {df_csv['flag'].value_counts().to_dict()}")
except Exception as e:
    print(f"  ERROR reading csv: {e}")

# -------------------------------------------------------
# 2. Validate Company Profile for 10 companies
# -------------------------------------------------------
print("\n" + "="*60)
print("COMPANY PROFILE - 10 COMPANIES")
print("="*60)

test_companies = [
    'Tata Consultancy',
    'Infosys',
    'Reliance Industries',
    'HDFC Bank',
    'ITC Ltd',
    'Bharat Electronics',
    'Hindustan Aeronautics',
    'NTPC Ltd',
    'Sun Pharmaceutical',
    'Asian Paints',
]

at_profile = AppTest.from_file('src/dashboard/pages/02_profile.py')
at_profile.run(timeout=15)
if at_profile.exception:
    print(f"  [FAIL] Page load error: {at_profile.exception}")
else:
    opts = at_profile.selectbox[0].options if at_profile.selectbox else []
    print(f"  Available companies count: {len(opts)}")
    for comp in test_companies:
        match = next((o for o in opts if comp.lower() in o.lower()), None)
        if match:
            t0 = time.time()
            at_p = AppTest.from_file('src/dashboard/pages/02_profile.py')
            at_p.run(timeout=10)
            at_p.selectbox[0].select(match).run(timeout=10)
            elapsed = time.time() - t0
            if at_p.exception:
                print(f"  [FAIL] {match}: {str(at_p.exception)[:80]}")
            else:
                # Check KPI values
                metrics = [m.value for m in at_p.metric[:3]] if at_p.metric else []
                print(f"  [PASS] {match} ({elapsed:.2f}s) KPIs: {metrics}")
        else:
            print(f"  [WARN] No match found for '{comp}'")

# -------------------------------------------------------
# 3. Trend Analysis - specific companies + multi-metric
# -------------------------------------------------------
print("\n" + "="*60)
print("TREND ANALYSIS - 10 COMPANIES")
print("="*60)

trend_companies = ['Tata Consultancy', 'Reliance Industries', 'HDFC Bank', 'ITC', 'Sun Pharmaceutical']
for comp in trend_companies:
    at = AppTest.from_file('src/dashboard/pages/05_trends.py')
    at.run(timeout=12)
    if at.exception:
        print(f"  [FAIL] Page load for {comp}: {str(at.exception)[:80]}")
        continue
    opts = at.selectbox[0].options if at.selectbox else []
    match = next((o for o in opts if comp.lower() in o.lower()), None)
    if match:
        at.selectbox[0].select(match).run(timeout=10)
        if at.exception:
            print(f"  [FAIL] {match}: {str(at.exception)[:80]}")
        else:
            # Check how many years of data
            infos = [i.value for i in at.info] if at.info else []
            print(f"  [PASS] {match}: {infos}")
    else:
        print(f"  [WARN] No match for '{comp}'")

# -------------------------------------------------------
# 4. Annual Reports - check multiple companies
# -------------------------------------------------------
print("\n" + "="*60)
print("ANNUAL REPORTS - COMPANIES WITH DATA")
print("="*60)

conn = sqlite3.connect('data/db/nifty100.db')
docs = pd.read_sql_query("SELECT DISTINCT company_id, COUNT(*) as cnt FROM documents GROUP BY company_id ORDER BY cnt DESC LIMIT 5", conn)
conn.close()
print(f"  Top 5 companies by report count:\n{docs.to_string()}")

at_r = AppTest.from_file('src/dashboard/pages/08_reports.py')
at_r.run(timeout=12)
if not at_r.exception:
    opts = at_r.selectbox[0].options if at_r.selectbox else []
    for comp in ['ITC', 'Reliance', 'Infosys']:
        match = next((o for o in opts if comp.lower() in o.lower()), None)
        if match:
            at_r.selectbox[0].select(match).run(timeout=10)
            dividers = len(at_r.markdown) if at_r.markdown else 0
            print(f"  {match}: {dividers} markdown elements rendered")
        else:
            print(f"  [WARN] No match for '{comp}'")

# -------------------------------------------------------
# 5. Edge case: company with missing data (financial sector)
# -------------------------------------------------------
print("\n" + "="*60)
print("EDGE CASE: FINANCIAL SECTOR COMPANIES (High D/E)")
print("="*60)
conn2 = sqlite3.connect('data/db/nifty100.db')
fin = pd.read_sql_query("""
    SELECT c.company_name, r.debt_to_equity
    FROM financial_ratios r
    JOIN companies c ON r.company_id = c.id
    JOIN sectors s ON s.company_id = c.id
    WHERE s.broad_sector = 'Financials'
    AND r.year = (SELECT MAX(year) FROM financial_ratios)
    LIMIT 5
""", conn2)
conn2.close()
print(fin.to_string())

print("\n  ALL EDGE CASE TESTS COMPLETE")
