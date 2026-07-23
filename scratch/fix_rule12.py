import re
import os
from pathlib import Path

# Rule 1
etl_loader = Path("src/etl/loader.py")
content = etl_loader.read_text(encoding="utf-8")
content = re.sub(r'header_row = 1 if has_banner else 0', 'header_row = 1', content)
content = re.sub(r'header=header_row,', 'header=1,', content)
etl_loader.write_text(content, encoding="utf-8")
print("Rule 1 fixed in loader.py")

# Rule 2
# Add normalization before merges
normalization_line = "    {var}['company_id'] = {var}['company_id'].astype(str).str.strip().str.upper()\n"

files_to_patch = [
    "src/screener/engine.py",
    "src/dashboard/pages/06_sectors.py",
    "src/dashboard/pages/07_capital.py",
    "src/dashboard/pages/04_peers.py",
    "src/dashboard/pages/05_trends.py",
    "src/dashboard/pages/08_reports.py",
    "src/analytics/valuation.py",
    "src/analytics/kpi_engine.py",
    "src/analytics/cagr.py",
    "src/analytics/day32_allocation.py",
    "src/analytics/investor_behaviour.py",
    "src/analytics/risk_analytics.py",
    "src/reports/portfolio.py",
    "src/reports/tearsheet.py"
]

for f in files_to_patch:
    path = Path(f)
    if not path.exists():
        continue
    content = path.read_text(encoding="utf-8")
    
    # Simple heuristic: inject normalization before the first .merge call for dataframes commonly used
    # A safer approach is to replace occurrences like `df = df.merge` with a normalized block
    # Or just inject it globally near the top of the function where `merge` happens.
    # To be very precise, let's inject it whenever a dataframe is loaded. 
    # Let's just find `.merge` and prefix the normalization for the left and right DFs.
    # Actually, a simple regex to catch the common variable names `df`, `pnl`, `merged`, `companies_df` etc.
    # Let's replace the first merge in the file with normalization of common vars in that scope.
    
    # Or I can just write a quick script that replaces exact strings if I know them.
    # Let's just manually fix them using multi_replace_file_content for precision.
print("Rule 1 executed.")
