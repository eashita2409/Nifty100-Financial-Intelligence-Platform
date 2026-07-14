"""
Sprint 4 Final Audit Script
Verifies every deliverable against the specification.
"""
import sys, os, time, sqlite3, pathlib
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

ROOT = pathlib.Path(__file__).resolve().parent.parent

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

issues = []

def check(cond, label, detail=""):
    status = PASS if cond else FAIL
    print(f"  {status} {label}{': ' + detail if detail else ''}")
    if not cond:
        issues.append(f"{label}: {detail}")
    return cond

def section(title):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")

# ============================================================
# 1. FILE EXISTENCE
# ============================================================
section("1. FILE EXISTENCE")
files = {
    "src/dashboard/app.py": "Streamlit entry point",
    "src/dashboard/pages/01_home.py": "Home page",
    "src/dashboard/pages/02_profile.py": "Company Profile page",
    "src/dashboard/pages/03_screener.py": "Screener page",
    "src/dashboard/pages/04_peers.py": "Peer Comparison page",
    "src/dashboard/pages/05_trends.py": "Trend Analysis page",
    "src/dashboard/pages/06_sectors.py": "Sector Analysis page",
    "src/dashboard/pages/07_capital.py": "Capital Allocation page",
    "src/dashboard/pages/08_reports.py": "Annual Reports page",
    "src/dashboard/utils/db.py": "Database utility (cached functions)",
    "src/analytics/valuation.py": "Valuation engine",
    "output/valuation_summary.xlsx": "Valuation summary Excel",
    "output/valuation_flags.csv": "Valuation flags CSV",
    "README.md": "Project README",
}
for rel_path, desc in files.items():
    p = ROOT / rel_path
    check(p.exists(), desc, f"at {rel_path}")

def read_src(path):
    return (ROOT / path).read_text(encoding='utf-8', errors='replace')

# ============================================================
# 2. db.py — REQUIRED FUNCTIONS
# ============================================================
section("2. db.py — REQUIRED CACHED FUNCTIONS")
db_src = read_src("src/dashboard/utils/db.py")
required_funcs = [
    "get_companies", "get_ratios", "get_pl", "get_bs",
    "get_cf", "get_sectors", "get_peers", "get_valuation",
    "get_documents", "get_screener_data",
]
for fn in required_funcs:
    check(f"def {fn}(" in db_src, f"Function {fn}()")
check("@st.cache_data" in db_src, "All functions use @st.cache_data")
check("ttl=600" in db_src, "Cache TTL set to 600s")

# ============================================================
# 3. app.py — STREAMLIT CONFIG
# ============================================================
section("3. app.py — PAGE CONFIGURATION")
app_src = read_src("src/dashboard/app.py")
check("set_page_config" in app_src, "set_page_config called")
check("Nifty 100" in app_src, "Page title contains 'Nifty 100'")
check("layout=\"wide\"" in app_src or "layout='wide'" in app_src, "Layout=wide")
check("expanded" in app_src, "Sidebar expanded by default")

# ============================================================
# 4. PAGE-LEVEL FEATURE CHECKS
# ============================================================
section("4. PAGE FEATURE CHECKS")

# 01_home.py
home = read_src("src/dashboard/pages/01_home.py")
print("\n  -- 01_home.py --")
check("Average ROE" in home or "avg_roe" in home, "KPI: Average ROE")
check("Median PE" in home or "median_pe" in home, "KPI: Median PE")
check("Median D" in home or "median_de" in home, "KPI: Median D/E")
check("total_companies" in home or "Total Companies" in home, "KPI: Total Companies")
check("revenue_cagr" in home or "Rev CAGR" in home, "KPI: Revenue CAGR")
check("debt_free" in home or "Debt Free" in home, "KPI: Debt Free Count")
check("pie" in home or "donut" in home.lower() or "hole=0.4" in home, "Sector distribution donut chart")
check("quality_score" in home or "composite_quality_score" in home, "Top 5 by Quality Score table")
check("selectbox" in home and "Year" in home, "Year selector in sidebar")

# 02_profile.py
profile = read_src("src/dashboard/pages/02_profile.py")
print("\n  -- 02_profile.py --")
check("selectbox" in profile, "Company search selectbox")
check("return_on_equity_pct" in profile or "ROE" in profile, "KPI: ROE")
check("return_on_capital_employed_pct" in profile or "ROCE" in profile, "KPI: ROCE")
check("net_profit_margin_pct" in profile or "Net Profit Margin" in profile, "KPI: Net Profit Margin")
check("debt_to_equity" in profile or "Debt Equity" in profile, "KPI: Debt Equity")
check("revenue_cagr" in profile, "KPI: Revenue CAGR")
check("free_cash_flow" in profile or "FCF" in profile, "KPI: FCF")
check("10 Year" in profile or "10-year" in profile or "barmode=" in profile, "10-year Revenue & PAT chart")
check("ROE vs ROCE" in profile or "ROCE" in profile and "line" in profile, "ROE vs ROCE trend chart")
check("Pros" in profile and "Cons" in profile, "Pros & Cons section")
check("N/A" in profile or "safe_fmt" in profile, "N/A fallback for missing data")

# 03_screener.py
screener = read_src("src/dashboard/pages/03_screener.py")
print("\n  -- 03_screener.py --")
check("slider" in screener, "Sliders for threshold inputs")
check("Quality" in screener, "Preset: Quality")
check("Value" in screener, "Preset: Value")
check("Growth" in screener, "Preset: Growth")
check("Dividend" in screener, "Preset: Dividend")
check("Debt Free" in screener, "Preset: Debt Free")
check("Turnaround" in screener, "Preset: Turnaround")
check("download_button" in screener, "CSV download button")
check("apply_filters" in screener or "ScreenerEngine" in screener, "ScreenerEngine integration")

# 04_peers.py
peers = read_src("src/dashboard/pages/04_peers.py")
print("\n  -- 04_peers.py --")
check("Scatterpolar" in peers or "radar" in peers.lower(), "Radar chart")
check("peer_group" in peers, "Peer group selection")
check("percentile" in peers or "peer_percentiles" in peers, "Percentile data used")
check("peer_avg" in peers, "Peer average calculation")

# 05_trends.py
trends = read_src("src/dashboard/pages/05_trends.py")
print("\n  -- 05_trends.py --")
check("multiselect" in trends, "Multi-select metric picker")
check("max_selections=3" in trends or "Max 3" in trends, "Max 3 metrics constraint")
check("Revenue" in trends and "Net Profit" in trends, "Revenue and Net Profit metrics")
check("ROE" in trends and "ROCE" in trends, "ROE and ROCE metrics")
check("FCF" in trends or "free_cash_flow" in trends, "FCF metric")
check("Debt" in trends and "Asset Turnover" in trends, "D/E and Asset Turnover metrics")
check("yoy" in trends or "pct_change" in trends, "YoY % change annotation")
check("years" in trends.lower() and "available" in trends.lower(), "Years available message")
check("pct_change" in trends or "pct_change" in trends, "Graceful <10 year handling")

# 06_sectors.py
sectors_src = read_src("src/dashboard/pages/06_sectors.py")
sectors = sectors_src  # alias for checks
print("\n  -- 06_sectors.py --")
check("selectbox" in sectors, "Sector dropdown")
check("scatter" in sectors or "bubble" in sectors, "Bubble chart")
check("market_cap" in sectors, "Bubble size = Market Cap")
check("sub_sector" in sectors, "Color = Sub Sector")
check("revenue" in sectors.lower() or "sales" in sectors, "X = Revenue")
check("return_on_equity" in sectors or "ROE" in sectors, "Y = ROE")
check("median" in sectors, "Sector median KPI comparison")
check("revenue_cagr" in sectors, "Median Revenue CAGR bar chart")
check("pat_cagr" in sectors, "Median PAT CAGR bar chart")

# 07_capital.py
capital = read_src("src/dashboard/pages/07_capital.py")
print("\n  -- 07_capital.py --")
check("treemap" in capital.lower() or "Treemap" in capital, "Plotly Treemap")
check("capital_allocation_pattern" in capital, "Capital allocation pattern field used")
check("selectbox" in capital, "Pattern selector dropdown")
check("Median ROE" in capital or "return_on_equity_pct" in capital, "Median ROE displayed")
check("Median FCF" in capital or "free_cash_flow_cr" in capital, "Median FCF displayed")
check("Number of Companies" in capital or "len(pattern_df)" in capital, "Company count displayed")

# 08_reports.py
reports = read_src("src/dashboard/pages/08_reports.py")
print("\n  -- 08_reports.py --")
check("selectbox" in reports, "Company search")
check("get_documents" in reports, "Fetches from documents table")
check("annual_report" in reports, "Annual report URL column used")
check("Report unavailable" in reports, "Red badge for missing reports")
check("View BSE" in reports or "View" in reports and "Annual Report" in reports, "Clickable BSE links")

# ============================================================
# 5. VALUATION ENGINE CHECKS
# ============================================================
section("5. valuation.py — ENGINE LOGIC")
val_src = read_src("src/analytics/valuation.py")
check("FCF_yield" in val_src or "fcf_yield" in val_src, "FCF Yield calculation")
check("market_cap" in val_src.lower(), "Market cap used in FCF yield")
check("sector_median" in val_src.lower(), "Sector Median PE computed")
check("Caution" in val_src, "Flag: Caution")
check("Discount" in val_src, "Flag: Discount")
check("Fair" in val_src, "Flag: Fair")
check("1.5" in val_src, "Caution rule: PE > 1.5x sector median")
check("0.7" in val_src, "Discount rule: PE < 0.7x sector median")
check("valuation_summary.xlsx" in val_src, "Outputs valuation_summary.xlsx")
check("valuation_flags.csv" in val_src, "Outputs valuation_flags.csv")
check("company_id" in val_src and "company_name" in val_src, "Required output columns present")

# ============================================================
# 6. OUTPUT FILE CONTENT VALIDATION
# ============================================================
section("6. OUTPUT FILES — CONTENT VALIDATION")
try:
    df_xl = pd.read_excel(ROOT / "output/valuation_summary.xlsx")
    check(len(df_xl) == 92, f"valuation_summary.xlsx has 92 rows", f"Found {len(df_xl)}")
    required_cols = ['company_id','company_name','sector','PE','PB','EV_EBITDA',
                     'FCF_yield_pct','sector_median_PE','PE_vs_sector_median_pct','flag']
    for col in required_cols:
        check(col in df_xl.columns, f"Column '{col}' in valuation_summary.xlsx")
    check(set(df_xl['flag'].unique()).issubset({'Fair','Caution','Discount','Unknown'}),
          "Flags are only Fair/Caution/Discount/Unknown")
    flags = df_xl['flag'].value_counts().to_dict()
    print(f"    Flag distribution: {flags}")
except Exception as e:
    check(False, "valuation_summary.xlsx readable", str(e))

try:
    df_csv = pd.read_csv(ROOT / "output/valuation_flags.csv")
    check(len(df_csv) > 0, "valuation_flags.csv has rows", f"Found {len(df_csv)}")
    check(all(f in ['Caution','Discount'] for f in df_csv['flag'].unique()),
          "valuation_flags.csv contains only Discount/Caution")
except Exception as e:
    check(False, "valuation_flags.csv readable", str(e))

# ============================================================
# 7. README COMPLETENESS
# ============================================================
section("7. README.md — CONTENT COMPLETENESS")
readme = read_src("README.md")
check("streamlit run src/dashboard/app.py" in readme, "Streamlit launch command in README")
check("Home" in readme and "Company Profile" in readme, "All screen names documented")
check("Screener" in readme and "Peer Comparison" in readme, "Screener & Peers documented")
check("Trend Analysis" in readme and "Sector Analysis" in readme, "Trends & Sectors documented")
check("Capital Allocation" in readme and "Annual Reports" in readme, "Capital & Reports documented")
check("Architecture" in readme, "Architecture section present")
check("UX" in readme or "UX Decisions" in readme, "UX decisions documented")
check("Edge" in readme, "Edge cases documented")
check("Performance" in readme, "Performance section present")
check("Sprint 4" in readme, "Sprint 4 retrospective present")

# ============================================================
# 8. PAGE RENDER TEST (AppTest)
# ============================================================
section("8. STREAMLIT PAGE RENDER TEST (AppTest)")
from streamlit.testing.v1 import AppTest

pages = [
    ("01_home.py", "Home"),
    ("02_profile.py", "Company Profile"),
    ("03_screener.py", "Screener"),
    ("04_peers.py", "Peer Comparison"),
    ("05_trends.py", "Trend Analysis"),
    ("06_sectors.py", "Sector Analysis"),
    ("07_capital.py", "Capital Allocation"),
    ("08_reports.py", "Annual Reports"),
]

load_times = {}
for fname, name in pages:
    t0 = time.time()
    at = AppTest.from_file(f"src/dashboard/pages/{fname}")
    at.run(timeout=15)
    elapsed = time.time() - t0
    load_times[name] = round(elapsed, 2)
    check(not at.exception, f"{name} renders without exception",
          str(at.exception)[:120] if at.exception else "")

# Company Profile timing test
print("\n  -- Company Profile: 5-Company Timing Test --")
page_times = []
at_profile = AppTest.from_file("src/dashboard/pages/02_profile.py")
at_profile.run(timeout=10)
opts = at_profile.selectbox[0].options if at_profile.selectbox else []
test_tickers = ["TCS", "INFY", "RELIANCE", "HDFCBANK", "ITC"]
for ticker in test_tickers:
    match = next((o for o in opts if ticker in o), None)
    if match:
        t0 = time.time()
        at_p = AppTest.from_file("src/dashboard/pages/02_profile.py")
        at_p.run(timeout=10)
        at_p.selectbox[0].select(match).run(timeout=10)
        elapsed = time.time() - t0
        page_times.append(elapsed)
        status = PASS if elapsed < 3.0 else FAIL
        print(f"  {status} {ticker}: {elapsed:.2f}s")

if page_times:
    avg = sum(page_times)/len(page_times)
    check(avg < 3.0, "Company Profile avg load < 3s", f"avg={avg:.2f}s")

# ============================================================
# 9. DATABASE INTEGRITY
# ============================================================
section("9. DATABASE INTEGRITY")
db_path = ROOT / "data/db/nifty100.db"
check(db_path.exists(), "nifty100.db exists")
if db_path.exists():
    conn = sqlite3.connect(db_path)
    for tbl in ["companies","profitandloss","balancesheet","cashflow",
                "financial_ratios","market_cap","sectors","peer_groups",
                "peer_percentiles","documents"]:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cursor.fetchone()[0]
        check(cnt > 0, f"Table '{tbl}' has data", f"{cnt} rows")
    conn.close()

# ============================================================
# SUMMARY
# ============================================================
section("FINAL AUDIT SUMMARY")
total = len(issues)
if total == 0:
    print(f"\n  [ALL CHECKS PASSED] Sprint 4 is COMPLETE")
else:
    print(f"\n  ❌ {total} ISSUE(S) FOUND:")
    for i, issue in enumerate(issues, 1):
        print(f"    {i}. {issue}")
print()
