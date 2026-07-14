import sqlite3
conn = sqlite3.connect('data/db/nifty100.db')
print([description[0] for description in conn.execute('SELECT * FROM peer_groups').description])
