import sqlite3
import pandas as pd

conn = sqlite3.connect('data/db/nifty100.db')
peers = pd.read_sql_query("SELECT * FROM peer_groups LIMIT 20", conn)
print("Sample peer groups:")
print(peers)
print("\nUnique peer group names:")
print(pd.read_sql_query("SELECT DISTINCT peer_group_name, COUNT(*) FROM peer_groups GROUP BY peer_group_name", conn))
conn.close()
