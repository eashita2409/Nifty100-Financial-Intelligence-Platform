import pytest
import sqlite3
import pandas as pd
from pathlib import Path

from src.analytics.cagr import calculate_cagr, populate_cagr_metrics

def test_cagr_positive_to_positive():
    # start=100, end=133.1, years=3 -> 10% CAGR
    val, flag = calculate_cagr(100, 133.1, 3)
    assert val == 10.0
    assert flag is None

def test_cagr_positive_to_negative():
    val, flag = calculate_cagr(100, -50, 3)
    assert val is None
    assert flag == "positive_to_negative"

def test_cagr_negative_to_positive():
    val, flag = calculate_cagr(-100, 50, 3)
    assert val is None
    assert flag == "negative_to_positive"

def test_cagr_negative_to_negative():
    val, flag = calculate_cagr(-100, -50, 3)
    assert val is None
    assert flag == "negative_to_negative"

def test_cagr_zero_base():
    val, flag = calculate_cagr(0, 50, 3)
    assert val is None
    assert flag == "zero_base"

def test_cagr_insufficient_history():
    val, flag = calculate_cagr(None, 50, 3)
    assert val is None
    assert flag == "insufficient_history"

def test_cagr_zero_years():
    val, flag = calculate_cagr(100, 150, 0)
    assert val is None
    assert flag == "insufficient_history"

def test_cagr_positive_to_zero():
    val, flag = calculate_cagr(100, 0, 3)
    assert val == -100.0
    assert flag is None

def test_cagr_negative_to_zero():
    val, flag = calculate_cagr(-100, 0, 3)
    assert val is None
    assert flag == "negative_to_zero"

def test_populate_cagr_metrics(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    
    conn.execute("CREATE TABLE profitandloss (company_id TEXT, year REAL, sales REAL, net_profit REAL, eps REAL)")
    conn.execute("CREATE TABLE financial_ratios (company_id TEXT, year REAL, revenue_cagr_3yr REAL, revenue_cagr_5yr REAL, revenue_cagr_10yr REAL, revenue_cagr_anomaly TEXT, pat_cagr_3yr REAL, pat_cagr_5yr REAL, pat_cagr_10yr REAL, pat_cagr_anomaly TEXT, eps_cagr_3yr REAL, eps_cagr_5yr REAL, eps_cagr_10yr REAL, eps_cagr_anomaly TEXT)")
    
    # 2020 Data
    conn.execute("INSERT INTO profitandloss VALUES ('C1', 2020, 100, -50, 5)")
    conn.execute("INSERT INTO financial_ratios (company_id, year) VALUES ('C1', 2020)")
    
    # 2023 Data (3 years later)
    conn.execute("INSERT INTO profitandloss VALUES ('C1', 2023, 133.1, 50, 0)")
    conn.execute("INSERT INTO financial_ratios (company_id, year) VALUES ('C1', 2023)")
    
    conn.commit()
    conn.close()
    
    populate_cagr_metrics(str(db_path))
    
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM financial_ratios WHERE year = 2023", conn)
    conn.close()
    
    row = df.iloc[0]
    
    # Sales: 100 -> 133.1 (Positive to Positive) -> 10%
    assert row['revenue_cagr_3yr'] == 10.0
    assert "3yr:insufficient_history" not in str(row['revenue_cagr_anomaly'])
    
    # PAT: -50 -> 50 (Negative to Positive) -> anomaly
    assert pd.isna(row['pat_cagr_3yr']) or row['pat_cagr_3yr'] is None
    assert "3yr:negative_to_positive" in str(row['pat_cagr_anomaly'])
    
    # EPS: 5 -> 0 (Positive to Zero) -> -100%
    assert row['eps_cagr_3yr'] == -100.0
    
    # 5yr and 10yr should be insufficient history
    assert "5yr:insufficient_history" in str(row['revenue_cagr_anomaly'])
    assert "10yr:insufficient_history" in str(row['revenue_cagr_anomaly'])
