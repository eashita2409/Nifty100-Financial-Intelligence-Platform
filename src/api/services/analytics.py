import sqlite3
import pandas as pd
import os
from typing import Dict, Any, List
from ..utils import check_company_exists
from ..schemas import RecommendRequest, Recommendation

def get_pros_cons(conn: sqlite3.Connection, ticker: str) -> Dict[str, Any]:
    check_company_exists(conn, ticker)
    
    # Pros & Cons with confidence are in the CSV generated during Sprint 5
    csv_path = 'output/pros_cons_generated.csv'
    if not os.path.exists(csv_path):
        fallback_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'output', 'pros_cons_generated.csv')
        if os.path.exists(fallback_path):
            csv_path = fallback_path
        else:
            return {"company_id": ticker, "pros": [], "cons": []}
            
    df = pd.read_csv(csv_path)
    matching = df[df['company_id'] == ticker]
    
    pros = []
    cons = []
    for _, row in matching.iterrows():
        item = {
            "type": str(row['type']),
            "category": str(row['rule_id']),
            "text": str(row['text']),
            "confidence": float(row['confidence_pct']) if pd.notnull(row['confidence_pct']) else 0.0
        }
        if row['type'].upper() == 'PRO':
            pros.append(item)
        else:
            cons.append(item)
            
    return {"company_id": ticker, "pros": pros, "cons": cons}

def get_dashboard_summary(conn: sqlite3.Connection) -> Dict[str, Any]:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(id) as total_companies FROM companies")
    row = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(DISTINCT broad_sector) as sectors_count FROM sectors")
    sec_row = cursor.fetchone()
    
    # Get total market cap from the latest year available
    cursor.execute("""
        SELECT SUM(market_cap_crore) as total_market_cap 
        FROM market_cap 
        WHERE year = (SELECT MAX(year) FROM market_cap)
    """)
    mc_row = cursor.fetchone()
    
    return {
        "total_companies": row['total_companies'] if row else 0,
        "total_market_cap": mc_row['total_market_cap'] if (mc_row and mc_row['total_market_cap']) else 0.0,
        "sectors_count": sec_row['sectors_count'] if sec_row else 0
    }

def get_cluster(ticker: str) -> Dict[str, Any]:
    # Cluster labels were generated and saved in output/cluster_labels.csv
    csv_path = 'output/cluster_labels.csv'
    if not os.path.exists(csv_path):
        fallback_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'output', 'cluster_labels.csv')
        if os.path.exists(fallback_path):
            csv_path = fallback_path
        else:
            return None
            
    df = pd.read_csv(csv_path)
    matching = df[df['Scheme'] == ticker]
    if matching.empty:
        return None
        
    row = matching.iloc[0]
    return {
        "company_id": ticker,
        "cluster": int(row['Cluster']),
        "risk_grade": str(row['Risk Grade']),
        "sharpe": float(row['Sharpe']),
        "cagr": float(row['CAGR'])
    }

def get_recommendations(req: RecommendRequest) -> List[Dict[str, Any]]:
    csv_path = 'data/processed/mutual_funds.csv'
    if not os.path.exists(csv_path):
        fallback_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data', 'processed', 'mutual_funds.csv')
        if os.path.exists(fallback_path):
            csv_path = fallback_path
        else:
            return []
            
    df = pd.read_csv(csv_path)
    filtered = df[df['risk_grade'].str.lower() == req.risk_profile.lower()]
    if filtered.empty:
        return []
        
    recommended = filtered.sort_values(by='Sharpe', ascending=False).head(3)
    results = []
    for _, row in recommended.iterrows():
        results.append({
            "scheme": str(row['scheme_name']),
            "sharpe": float(row['Sharpe']),
            "cagr": float(row['CAGR']),
            "volatility": float(row['Volatility']),
            "risk_grade": str(row['risk_grade'])
        })
    return results
