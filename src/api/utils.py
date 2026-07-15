from fastapi import HTTPException
import sqlite3

def handle_db_error(e: sqlite3.Error):
    raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def check_company_exists(conn: sqlite3.Connection, ticker: str):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM companies WHERE id = ?", (ticker,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"Company with ticker {ticker} not found")
    return True
