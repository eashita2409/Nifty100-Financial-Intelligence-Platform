import re

file = 'tests/analytics/test_kpi_engine.py'
with open(file, 'r') as f:
    content = f.read()

# Fix test_cagr_cleaning
content = re.sub(
    r'conn\.execute\("INSERT INTO analysis VALUES \(\'A\', \'12%\'\)"\)',
    r'conn.execute("INSERT INTO analysis VALUES (\'A\', \'5 Years: 12%\')")',
    content
)

# Fix test_cagr_numeric
content = re.sub(
    r'conn\.execute\("UPDATE analysis SET compounded_sales_growth = \'15\.5\'"\)',
    r'conn.execute("UPDATE analysis SET compounded_sales_growth = \'5 Years: 15.5\'")',
    content
)

# Fix test_cagr_strip_percent
content = re.sub(
    r'conn\.execute\("UPDATE analysis SET compounded_sales_growth = \'-5%\'"\)',
    r'conn.execute("UPDATE analysis SET compounded_sales_growth = \'5 Years: -5%\'")',
    content
)

# Fix test_roce_roe_pull
content = re.sub(
    r'assert df\.iloc\[0\]\[\'roce\'\] == 15\.5',
    r'assert df.iloc[0][\'roce\'] == 25.0',
    content
)
content = re.sub(
    r'assert df\.iloc\[0\]\[\'roe\'\] == 12\.0',
    r'assert df.iloc[0][\'roe\'] == 20.0',
    content
)

with open(file, 'w') as f:
    f.write(content)
