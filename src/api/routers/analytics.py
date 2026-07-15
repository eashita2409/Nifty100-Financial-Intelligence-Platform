from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from ..database import get_db
from ..schemas import ProsConsResponse, DashboardSummaryResponse, ClusterResponse, RecommendRequest, RecommendResponse
from ..services import analytics as analytics_service
from ..utils import handle_db_error

router = APIRouter(tags=["Analytics"])

@router.get("/pros-cons/{ticker}", response_model=ProsConsResponse)
def get_pros_cons(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        return analytics_service.get_pros_cons(db, ticker)
    except sqlite3.Error as e:
        handle_db_error(e)

@router.get("/dashboard-summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: sqlite3.Connection = Depends(get_db)):
    try:
        return analytics_service.get_dashboard_summary(db)
    except sqlite3.Error as e:
        handle_db_error(e)

@router.get("/cluster/{ticker}", response_model=ClusterResponse)
def get_cluster(ticker: str):
    cluster_data = analytics_service.get_cluster(ticker)
    if not cluster_data:
        raise HTTPException(status_code=404, detail=f"Cluster data for {ticker} not found")
    return cluster_data

@router.post("/recommend", response_model=RecommendResponse)
def recommend_funds(request: RecommendRequest):
    recs = analytics_service.get_recommendations(request)
    return {"recommendations": recs}
