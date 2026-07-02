import glob
import re

file = 'tests/analytics/test_kpi_engine.py'
with open(file, 'r') as f:
    content = f.read()

content = re.sub(
    r'conn\.execute\("CREATE TABLE financial_ratios \(company_id TEXT, year REAL, debt_to_equity REAL, interest_coverage REAL, net_profit_margin_pct REAL, free_cash_flow_cr REAL\)"\)',
    r'conn.execute("CREATE TABLE financial_ratios (company_id TEXT, year REAL, debt_to_equity REAL, interest_coverage REAL, net_profit_margin_pct REAL, free_cash_flow_cr REAL, return_on_equity_pct REAL, return_on_capital_employed_pct REAL)")',
    content
)

content = re.sub(
    r'conn\.execute\("INSERT INTO financial_ratios VALUES \(\'TEST1\', 2023, 1\.5, 3\.0, 15\.0, 100\.0\)"\)',
    r'conn.execute("INSERT INTO financial_ratios VALUES (\'TEST1\', 2023, 1.5, 3.0, 15.0, 100.0, 20.0, 25.0)")',
    content
)

content = re.sub(
    r'conn\.execute\("INSERT INTO financial_ratios VALUES \(\'TEST2\', 2023, 0\.5, 10\.0, 25\.0, 500\.0\)"\)',
    r'conn.execute("INSERT INTO financial_ratios VALUES (\'TEST2\', 2023, 0.5, 10.0, 25.0, 500.0, 30.0, 35.0)")',
    content
)

with open(file, 'w') as f:
    f.write(content)
