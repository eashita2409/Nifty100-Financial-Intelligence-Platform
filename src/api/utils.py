from fastapi import HTTPException
import sqlite3

def check_company_exists(conn: sqlite3.Connection, ticker: str):
    ticker = ticker.strip().upper()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM companies WHERE id = ?", (ticker,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found")

def handle_db_error(e: Exception):
    raise HTTPException(status_code=500, detail="Database error occurred")
