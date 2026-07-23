import re
import os
from pathlib import Path
import sqlite3

def normalize_company_id(file_path, df_names):
    path = Path(file_path)
    if not path.exists(): return
    content = path.read_text(encoding="utf-8")
    
    # We want to add the normalization step before the first merge
    # E.g., `df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()`
    # For every dataframe in df_names, we find the first occurrence of its merge and prepend normalization.
    # Actually, a simpler way is to inject normalization right after the dataframe is loaded or passed.
    
    # Let's just create a utility in src.utils and call it, or just use string replacement on specific lines.
    pass

# For Rule 4: D/E filter skips Financials
# in src/screener/engine.py
screener_engine = Path("src/screener/engine.py")
content = screener_engine.read_text(encoding="utf-8")
if "def apply_filters" in content:
    # Modify debt_equity filter
    content = re.sub(
        r"if 'debt_equity_max' in filters and 'debt_equity' in df.columns:\n\s*df = df\[df\['debt_equity'\] <= filters\['debt_equity_max'\]\]",
        r"if 'debt_equity_max' in filters and 'debt_equity' in df.columns:\n            df = df[(df['debt_equity'] <= filters['debt_equity_max']) | (df['broad_sector'].str.upper() == 'FINANCIALS')]",
        content
    )
    screener_engine.write_text(content, encoding="utf-8")
    print("Rule 4 applied to screener/engine.py")

# Rule 5: CAGR Negative Base = TURNAROUND
cagr_file = Path("src/analytics/cagr.py")
if cagr_file.exists():
    content = cagr_file.read_text(encoding="utf-8")
    content = re.sub(
        r"def calculate_cagr\(base_val, current_val, years\):.*?(?=    try:)",
        r"def calculate_cagr(base_val, current_val, years):\n    if base_val < 0 and current_val > 0:\n        return 'TURNAROUND'\n",
        content, flags=re.DOTALL
    )
    # Actually wait, maybe it's in src/analytics/kpi_engine.py?
    
# Let's check kpi_engine.py
kpi = Path("src/analytics/kpi_engine.py")
if kpi.exists():
    content = kpi.read_text(encoding="utf-8")
    if "def _calculate_cagr" in content:
        content = re.sub(
            r"def _calculate_cagr\(self, start_val, end_val, years\):\n\s*if start_val <= 0:\n\s*return None",
            r"def _calculate_cagr(self, start_val, end_val, years):\n        if start_val < 0 and end_val > 0:\n            return 'TURNAROUND'\n        if start_val <= 0:\n            return None",
            content
        )
        kpi.write_text(content, encoding="utf-8")
        print("Rule 5 applied to kpi_engine.py")

# Rule 6: Interest Expense = 0 -> Debt Free
ratios = Path("src/analytics/ratios.py")
if ratios.exists():
    content = ratios.read_text(encoding="utf-8")
    # Usually interest coverage ratio = EBIT / Interest Expense
    content = re.sub(
        r"interest_expense = row.get\('interest_expense', 0\)\n\s*if interest_expense == 0:\n\s*coverage = None",
        r"interest_expense = row.get('interest_expense', 0)\n            if interest_expense == 0:\n                coverage = 'Debt Free'",
        content
    )
    ratios.write_text(content, encoding="utf-8")
    print("Rule 6 applied to ratios.py")
