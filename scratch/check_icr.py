import sqlite3
conn = sqlite3.connect('data/db/nifty100.db')
cur = conn.cursor()
cur.execute("SELECT DISTINCT interest_coverage FROM financial_ratios WHERE typeof(interest_coverage) = 'text'")
print("Text values in interest_coverage:", cur.fetchall())
cur.execute("SELECT DISTINCT interest_coverage FROM financial_ratios LIMIT 10")
print("Sample interest_coverage values:", cur.fetchall())
conn.close()
