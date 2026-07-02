import sqlite3
import pandas as pd
conn = sqlite3.connect('data/db/nifty100.db')
print(pd.read_sql("SELECT * FROM analysis WHERE company_id='INFY'", conn))
