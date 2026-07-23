from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from ..database import get_db
from ..schemas import PeerResponse
from ..utils import check_company_exists

router = APIRouter(tags=["Peers"])

@router.get("/peers/{group_name}", response_model=PeerResponse)
def get_peers_by_group(group_name: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT company_id as id, company_name as name FROM peer_groups JOIN companies ON peer_groups.company_id = companies.id WHERE peer_group_name = ? COLLATE NOCASE", (group_name,))
    peers = [dict(r) for r in cursor.fetchall()]
    if not peers:
        raise HTTPException(status_code=404, detail="Peer group not found")
    # For simplicity, returning just basic IDs in the response
    return PeerResponse(group_name=group_name, peers=[{"company_id": p['id']} for p in peers])

@router.get("/companies/{ticker}/peers/compare", response_model=PeerResponse)
def get_company_peers(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    ticker = ticker.strip().upper()
    check_company_exists(db, ticker)
    cursor = db.cursor()
    
    # get sector
    cursor.execute("SELECT broad_sector FROM sectors WHERE company_id = ?", (ticker,))
    row = cursor.fetchone()
    sector = row['broad_sector'] if row else ""
    
    cursor.execute("""
        SELECT c.id as company_id, 
               m.pe_ratio, 
               f.return_on_equity_pct as roe,
               m.market_cap_crore as market_cap_cr
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        LEFT JOIN market_cap m ON c.id = m.company_id AND m.year = (SELECT MAX(year) FROM market_cap WHERE company_id = c.id)
        LEFT JOIN financial_ratios f ON c.id = f.company_id AND f.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
        WHERE s.broad_sector = ?
    """, (sector,))
    
    peers = [dict(r) for r in cursor.fetchall()]
    return PeerResponse(group_name=sector, peers=peers)
