from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from ..database import get_db
from ..schemas import SectorListResponse, SectorSummary

router = APIRouter(tags=["Sectors"])

@router.get("/sectors", response_model=SectorListResponse)
def get_sectors(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT DISTINCT broad_sector FROM sectors WHERE broad_sector IS NOT NULL")
    return SectorListResponse(sectors=[r['broad_sector'] for r in cursor.fetchall()])

@router.get("/sectors/{sector}/companies", response_model=SectorSummary)
def get_sector_companies(sector: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT c.id, c.company_name as name FROM companies c JOIN sectors s ON c.id = s.company_id WHERE s.broad_sector = ? COLLATE NOCASE", (sector,))
    comps = [dict(r) for r in cursor.fetchall()]
    if not comps:
        raise HTTPException(status_code=404, detail="Sector not found")
    return SectorSummary(sector=sector, companies=comps)
