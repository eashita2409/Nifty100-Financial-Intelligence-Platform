import re

file = 'tests/analytics/test_kpi_engine.py'
with open(file, 'r') as f:
    content = f.read()

# Replace all INSERT INTO financial_ratios that only have 6 values with 8 values.
# The regex finds 6 values like ('A', 2023, 1.5, 4.0, 15.0, 50.0)
content = re.sub(
    r'conn\.execute\("INSERT INTO financial_ratios VALUES \(\'([^\']+)\', (\d+), ([^,]+), ([^,]+), ([^,]+), ([^,]+)\)"\)',
    r'conn.execute("INSERT INTO financial_ratios VALUES (\'\1\', \2, \3, \4, \5, \6, 20.0, 25.0)")',
    content
)

with open(file, 'w') as f:
    f.write(content)
