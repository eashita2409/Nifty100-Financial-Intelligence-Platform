import os
import re

files = [
    'tests/analytics/test_kpi_engine.py',
    'tests/analytics/test_leverage.py',
    'tests/analytics/test_ratios.py'
]

for file in files:
    with open(file, 'r') as f:
        content = f.read()

    # Find the CREATE TABLE block and add companies
    if "CREATE TABLE companies" not in content:
        content = re.sub(
            r'conn\.execute\("CREATE TABLE sectors (.*?)"\)',
            r'conn.execute("CREATE TABLE sectors \1")\n        conn.execute("CREATE TABLE companies (id TEXT, company_name TEXT, roce_percentage REAL, roe_percentage REAL)")',
            content
        )
        content = re.sub(
            r'conn\.execute\("INSERT INTO sectors VALUES \(.*?C1.*?IT.*?\)"\)',
            r'\g<0>\n        conn.execute("INSERT INTO companies VALUES (\'C1\', \'Company 1\', 20.0, 15.0)")',
            content
        )
        content = re.sub(
            r'conn\.execute\("INSERT INTO sectors VALUES \(.*?B1.*?Financials.*?\)"\)',
            r'\g<0>\n        conn.execute("INSERT INTO companies VALUES (\'B1\', \'Bank 1\', 10.0, 12.0)")',
            content
        )
        # for kpi engine which might have different mock data
        if "test_kpi_engine.py" in file:
            content = re.sub(
                r'CREATE TABLE profitandloss \(',
                r'CREATE TABLE companies (id TEXT, company_name TEXT, roce_percentage REAL, roe_percentage REAL)");\n        conn.execute("CREATE TABLE profitandloss (',
                content
            )
            content = re.sub(
                r'INSERT INTO profitandloss VALUES \(\'TEST1\'',
                r'INSERT INTO companies VALUES (\'TEST1\', \'Test Company\', 25.0, 20.0)");\n        conn.execute("INSERT INTO profitandloss VALUES (\'TEST1\'',
                content
            )
            content = re.sub(
                r'INSERT INTO profitandloss VALUES \(\'TEST2\'',
                r'INSERT INTO companies VALUES (\'TEST2\', \'Test Company 2\', 30.0, 25.0)");\n        conn.execute("INSERT INTO profitandloss VALUES (\'TEST2\'',
                content
            )
        
        with open(file, 'w') as f:
            f.write(content)
