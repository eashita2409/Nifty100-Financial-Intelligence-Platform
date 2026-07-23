from fastapi import APIRouter, Depends
import sqlite3
from ..database import get_db
from ..schemas import DocumentsResponse
from ..utils import check_company_exists

router = APIRouter(tags=["Documents"])

@router.get("/companies/{ticker}/documents", response_model=DocumentsResponse)
def get_documents(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    ticker = ticker.strip().upper()
    check_company_exists(db, ticker)
    cursor = db.cursor()
    cursor.execute("SELECT year, annual_report FROM documents WHERE company_id = ? ORDER BY year", (ticker,))
    return DocumentsResponse(company_id=ticker, documents=[dict(r) for r in cursor.fetchall()])
