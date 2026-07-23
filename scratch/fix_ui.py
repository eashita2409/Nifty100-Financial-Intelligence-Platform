import re
from pathlib import Path

# Fix Rule 2: Normalize company_id before joins
files = [
    "src/screener/engine.py",
    "src/dashboard/pages/06_sectors.py",
    "src/dashboard/pages/07_capital.py",
    "src/dashboard/pages/04_peers.py",
    "src/dashboard/pages/05_trends.py",
    "src/dashboard/pages/08_reports.py",
    "src/analytics/valuation.py",
    "src/analytics/kpi_engine.py",
    "src/reports/portfolio.py",
    "src/reports/tearsheet.py",
    "src/analytics/investor_behaviour.py"
]

for f in files:
    path = Path(f)
    if not path.exists(): continue
    content = path.read_text(encoding="utf-8")
    
    # We will just find unique df names that call .merge( on 'company_id' or are passed as arguments to merge
    # A simple but highly effective trick:
    # Just insert `if 'company_id' in df.columns: df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()` at the top of every major function in these files.
    # Actually, let's just do a blanket find for `.merge(` and `pd.merge(` and inject it right before the first merge.
    
    # Or, we can just patch `get_screener_data`, `get_all_companies`, etc. to return normalized data?
    pass

# For Rule 3 & 7: Streamlit Labels
# Rule 3: Monetary values -> INR Crore
# Rule 7: simulated label for stock_prices and market_cap

for p in Path("src/dashboard/pages").glob("*.py"):
    content = p.read_text(encoding="utf-8")
    
    # Rule 3: INR Crore
    content = content.replace("Market Cap", "Market Cap (INR Crore)")
    content = content.replace("Revenue", "Revenue (INR Crore)")
    content = content.replace("FCF", "FCF (INR Crore)")
    content = content.replace("PAT", "PAT (INR Crore)")
    content = content.replace("Free Cash Flow", "Free Cash Flow (INR Crore)")
    # Don't double replace
    content = content.replace("(INR Crore) (INR Crore)", "(INR Crore)")
    
    # Rule 7: SIMULATED label
    if 'market_cap' in content.lower() or 'stock_prices' in content.lower() or 'price' in content.lower() or 'valuation' in content.lower():
        if "SIMULATED" not in content:
            # Add a simulated warning below the title
            content = re.sub(
                r'(st\.title\(.*?\))',
                r'\1\nst.caption("⚠️ **Note**: Market Cap and Stock Price data displayed on this page is SIMULATED.")',
                content,
                count=1
            )
            
    p.write_text(content, encoding="utf-8")
    
# Do the same for app.py
app_py = Path("src/dashboard/app.py")
if app_py.exists():
    content = app_py.read_text(encoding="utf-8")
    if "SIMULATED" not in content:
        content = re.sub(
            r'(st\.title\(.*?\))',
            r'\1\nst.caption("⚠️ **Note**: Market Cap and Stock Price datasets used in this platform are SIMULATED for demonstration purposes.")',
            content,
            count=1
        )
    app_py.write_text(content, encoding="utf-8")

print("Rule 3 and 7 applied to dashboard.")
