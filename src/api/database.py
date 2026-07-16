import sqlite3
from typing import Generator
from pathlib import Path

# Base path for database
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'db' / 'nifty100.db'

def get_db_connection():
    """
    Establish a connection to the SQLite database.
    Sets row_factory to sqlite3.Row for dict-like access.
    """
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
