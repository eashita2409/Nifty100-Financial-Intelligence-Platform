import re
from pathlib import Path

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

norm_str = "    if '{var}' in locals() and hasattr({var}, 'columns') and 'company_id' in {var}.columns:\n        {var}['company_id'] = {var}['company_id'].astype(str).str.strip().str.upper()\n"

for f in files:
    path = Path(f)
    if not path.exists(): continue
    content = path.read_text(encoding="utf-8")
    
    # We will find every dataframe calling .merge and its argument
    # E.g. `df = df.merge(other, ...)` -> `df` and `other`
    # A simple regex to find `(\w+)\.merge\((\w+)`
    matches = set(re.findall(r'(\w+)\.merge\((\w+)', content))
    
    # Prepend normalization before the first merge in the file, or just at the top of the file after imports? No, the dataframes don't exist globally.
    # Instead, we will replace `(\w+)\.merge\((\w+)` with the normalization and the merge.
    # But doing this for every merge line will duplicate normalization. 
    # Let's just do it inline where the merge happens.
    
    new_content = []
    lines = content.split('\n')
    for line in lines:
        m = re.search(r'(\w+)\.merge\((\w+)', line)
        if m:
            left_df = m.group(1)
            right_df = m.group(2)
            indent = line[:len(line) - len(line.lstrip())]
            norm1 = f"{indent}if '{left_df}' in locals() and hasattr({left_df}, 'columns') and 'company_id' in {left_df}.columns: {left_df}['company_id'] = {left_df}['company_id'].astype(str).str.strip().str.upper()"
            norm2 = f"{indent}if '{right_df}' in locals() and hasattr({right_df}, 'columns') and 'company_id' in {right_df}.columns: {right_df}['company_id'] = {right_df}['company_id'].astype(str).str.strip().str.upper()"
            new_content.append(norm1)
            new_content.append(norm2)
            new_content.append(line)
        else:
            new_content.append(line)
            
    path.write_text('\n'.join(new_content), encoding="utf-8")
    print(f"Patched merges in {f}")

