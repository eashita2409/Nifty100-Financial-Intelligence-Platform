import sqlite3
from typing import Generator
import os

# Base path for database
DB_PATH = 'data/db/nifty100.db'

def get_db_connection():
    """
    Establish a connection to the SQLite database.
    Sets row_factory to sqlite3.Row for dict-like access.
    """
    if not os.path.exists(DB_PATH):
        # Fallback if running from a different directory
        fallback_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'db', 'nifty100.db')
        conn = sqlite3.connect(fallback_path, check_same_thread=False)
    else:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        
    conn.row_factory = sqlite3.Row
    return conn

def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    FastAPI dependency that yields a database connection and ensures
    it is closed after the request is complete.
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()
