import re
import os
from pathlib import Path

# Rule 2: company_id normalization before merges
files_to_patch = [
    "src/screener/engine.py",
    "src/dashboard/pages/06_sectors.py",
    "src/dashboard/pages/07_capital.py",
    "src/dashboard/pages/04_peers.py",
    "src/dashboard/pages/05_trends.py",
    "src/dashboard/pages/08_reports.py",
    "src/analytics/valuation.py",
    "src/analytics/kpi_engine.py",
    "src/analytics/day32_allocation.py",
    "src/analytics/investor_behaviour.py",
    "src/analytics/risk_analytics.py",
    "src/reports/portfolio.py",
    "src/reports/tearsheet.py"
]

def normalize_in_file(path_str):
    path = Path(path_str)
    if not path.exists():
        return
    content = path.read_text(encoding="utf-8")
    
    # Simple strategy: find DataFrame names used with `.merge` or `.join` and ensure they are normalized before.
    # We can inject a utility at the top of these functions or just do a regex replace on the .merge lines
    # Actually, the safest way is to do it manually in the code where data is loaded, but there are 13 files.
    # Let's search for the first merge, find the left df and right df, and prepend normalization.
    # Because there are many merges, let's just write a generic normalization block at the start of functions that use merge.
    pass

# We will handle Rule 2 with a specialized run_command script using AST or regex, or just apply it globally where dataframes are loaded.
# Let's check src/etl/loader.py and database_loader.py for ETL merges.
# The rule: "Before joins/merges, company_id must always be normalized"

# Rule 4: D/E filter skips Financials
screener_engine = Path("src/screener/engine.py")
if screener_engine.exists():
    content = screener_engine.read_text(encoding="utf-8")
    content = re.sub(
        r"if 'debt_equity_max' in filters and 'debt_equity' in df.columns:\n\s*df = df\[df\['debt_equity'\] <= filters\['debt_equity_max'\]\]",
        r"if 'debt_equity_max' in filters and 'debt_equity' in df.columns:\n            df = df[(df['debt_equity'] <= filters['debt_equity_max']) | (df['broad_sector'].str.upper() == 'FINANCIALS')]",
        content
    )
    screener_engine.write_text(content, encoding="utf-8")
    print("Rule 4 applied.")

# Rule 5: CAGR Negative Base = TURNAROUND
cagr_file = Path("src/analytics/cagr.py")
if cagr_file.exists():
    content = cagr_file.read_text(encoding="utf-8")
    content = re.sub(
        r"def calculate_cagr\(start_val: Optional\[float\], end_val: Optional\[float\], years: int\) -> Tuple\[Optional\[float\], Optional\[str\]\]:",
        r"from typing import Union\ndef calculate_cagr(start_val: Optional[float], end_val: Optional[float], years: int) -> Tuple[Union[float, str, None], Optional[str]]:",
        content
    )
    content = re.sub(
        r"if start_val < 0 and end_val > 0:\n\s*return None, \"negative_to_positive\"",
        r"if start_val < 0 and end_val > 0:\n        return 'TURNAROUND', \"negative_to_positive\"",
        content
    )
    cagr_file.write_text(content, encoding="utf-8")
    print("Rule 5 applied.")

# Rule 6: Interest Expense = 0 -> Debt Free
ratios = Path("src/analytics/ratios.py")
if ratios.exists():
    content = ratios.read_text(encoding="utf-8")
    content = re.sub(
        r"interest_expense = row.get\('interest_expense', 0\)\n\s*if interest_expense == 0:\n\s*coverage = None",
        r"interest_expense = row.get('interest_expense', 0)\n            if interest_expense == 0:\n                coverage = 'Debt Free'",
        content
    )
    ratios.write_text(content, encoding="utf-8")
    print("Rule 6 applied.")
