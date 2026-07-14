import sqlite3
import pandas as pd
import streamlit as st
from pathlib import Path
import os
import sys

# Ensure src is in the python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

def get_db_path():
    # Resolve the project root assuming this file is in src/dashboard/utils/
    # Project Root -> src -> dashboard -> utils -> db.py
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent.parent
    return project_root / "data" / "db" / "nifty100.db"

@st.cache_data(ttl=600)
def get_companies():
    db_path = get_db_path()
    if not db_path.exists():
        return pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query("SELECT * FROM companies", conn)

@st.cache_data(ttl=600)
def get_ratios():
    db_path = get_db_path()
    if not db_path.exists():
        return pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
        return df.dropna(subset=['year'])

@st.cache_data(ttl=600)
def get_pl():
    db_path = get_db_path()
    if not db_path.exists():
        return pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
        return df.dropna(subset=['year'])

@st.cache_data(ttl=600)
def get_bs():
    db_path = get_db_path()
    if not db_path.exists():
        return pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT * FROM balancesheet", conn)
        return df.dropna(subset=['year'])

@st.cache_data(ttl=600)
def get_cf():
    db_path = get_db_path()
    if not db_path.exists():
        return pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query("SELECT * FROM cashflow", conn)

@st.cache_data(ttl=600)
def get_sectors():
    db_path = get_db_path()
    if not db_path.exists():
        return pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query("SELECT * FROM sectors", conn)

@st.cache_data(ttl=600)
def get_peers():
    db_path = get_db_path()
    if not db_path.exists():
        return pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query("SELECT * FROM peer_groups", conn)

@st.cache_data(ttl=600)
def get_peer_percentiles():
    db_path = get_db_path()
    if not db_path.exists():
        return pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        # Check if table exists, it was added in peer.py
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='peer_percentiles'")
        if not cursor.fetchone():
            return pd.DataFrame()
        return pd.read_sql_query("SELECT * FROM peer_percentiles", conn)

@st.cache_data(ttl=600)
def get_valuation():
    db_path = get_db_path()
    if not db_path.exists():
        return pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query("SELECT * FROM market_cap", conn)

@st.cache_data(ttl=600)
def get_screener_data(target_year=None):
    from src.screener.engine import ScreenerEngine
    ratios = get_ratios()
    if ratios.empty:
        return pd.DataFrame()
    latest_year = ratios['year'].max()
    engine = ScreenerEngine()
    db_path = get_db_path()
    df = engine.fetch_data(str(db_path), target_year=latest_year)
    return engine.calculate_composite_quality_score(df).fillna(0)
