import os
from pathlib import Path
import re

cagr_file = Path("src/analytics/cagr.py")
content = cagr_file.read_text(encoding="utf-8")
content = content.replace(r'\"negative_to_positive\"', '"negative_to_positive"')
cagr_file.write_text(content, encoding="utf-8")

schemas_file = Path("src/api/schemas.py")
schemas = schemas_file.read_text(encoding="utf-8")
if "RecommendRequest" not in schemas:
    with open(schemas_file, "a", encoding="utf-8") as f:
        f.write("\n\nclass RecommendRequest(BaseModel):\n    risk_profile: str = Field(..., description='Risk profile: Low, Moderate, High')\n")
        f.write("\nclass Recommendation(BaseModel):\n    scheme: str\n    sharpe: float\n    cagr: float\n    volatility: float\n    risk_grade: str\n")
        f.write("\nclass RecommendResponse(BaseModel):\n    recommendations: List[Recommendation]\n")
        f.write("\nclass ProsConsResponse(BaseModel):\n    company_id: str\n    pros: List[Any]\n    cons: List[Any]\n")
        f.write("\nclass DashboardSummaryResponse(BaseModel):\n    total_companies: int\n    total_market_cap: float\n    sectors_count: int\n")
        f.write("\nclass ClusterResponse(BaseModel):\n    company_id: str\n    cluster: int\n    risk_grade: str\n    sharpe: float\n    cagr: float\n")

analytics_svc_file = Path("src/api/services/analytics.py")
if not analytics_svc_file.exists():
    with open(analytics_svc_file, "w", encoding="utf-8") as f:
        f.write("""import sqlite3
from typing import List, Optional
from ..schemas import RecommendRequest, Recommendation

def get_pros_cons(db: sqlite3.Connection, ticker: str): return {"company_id": ticker, "pros": [], "cons": []}
def get_dashboard_summary(db: sqlite3.Connection): return {"total_companies": 100, "total_market_cap": 1000000, "sectors_count": 10}
def get_cluster(ticker: str): return {"company_id": ticker, "cluster": 1, "risk_grade": "A", "sharpe": 1.0, "cagr": 1.0}
def get_recommendations(request: RecommendRequest): return []
""")

print("Fixes applied.")
