import pytest
import sqlite3
import pandas as pd
from pathlib import Path
import os

from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_cfo_quality_score,
    calculate_capex_intensity,
    calculate_fcf_conversion,
    classify_capital_allocation,
    generate_capital_allocation_report
)

def test_calculate_free_cash_flow():
    assert calculate_free_cash_flow(100, 40) == 60
    assert calculate_free_cash_flow(100, -40) == 60 # handles negative capex
    assert calculate_free_cash_flow(100, None) == 100
    assert calculate_free_cash_flow(None, 40) == -40

def test_calculate_cfo_quality_score():
    assert calculate_cfo_quality_score(150, 100) == 1.5
    assert calculate_cfo_quality_score(150, 0) is None
    assert calculate_cfo_quality_score(None, 100) == 0.0

def test_calculate_capex_intensity():
    assert calculate_capex_intensity(50, 500) == 0.1
    assert calculate_capex_intensity(-50, 500) == 0.1
    assert calculate_capex_intensity(50, 0) is None

def test_calculate_fcf_conversion():
    assert calculate_fcf_conversion(60, 100) == 0.6
    assert calculate_fcf_conversion(60, 0) is None

def test_classify_capital_allocation():
    assert classify_capital_allocation(-10, 5, -15, 0) == "Cash Burn"
    assert classify_capital_allocation(50, 60, -10, 0) == "Aggressive Expansion"
    assert classify_capital_allocation(100, 20, 80, -50) == "Cash Cow / Returner"
    assert classify_capital_allocation(100, 20, 80, 50) == "Stable / Moderate Reinvestment"

def test_generate_capital_allocation_report(tmp_path):
    db_path = tmp_path / "test.db"
    out_csv = tmp_path / "output.csv"
    
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE financial_ratios (company_id TEXT, year REAL, cash_from_operations_cr REAL, capex_cr REAL)")
    conn.execute("CREATE TABLE cashflow (company_id TEXT, year REAL, financing_activity REAL)")
    conn.execute("CREATE TABLE profitandloss (company_id TEXT, year REAL, net_profit REAL, sales REAL)")
    
    # C1: Cash Cow
    conn.execute("INSERT INTO financial_ratios VALUES ('C1', 2023, 100, 20)")
    conn.execute("INSERT INTO cashflow VALUES ('C1', 2023, -50)")
    conn.execute("INSERT INTO profitandloss VALUES ('C1', 2023, 80, 1000)")
    
    # C2: Aggressive Expansion
    conn.execute("INSERT INTO financial_ratios VALUES ('C2', 2023, 50, 60)")
    conn.execute("INSERT INTO cashflow VALUES ('C2', 2023, 10)")
    conn.execute("INSERT INTO profitandloss VALUES ('C2', 2023, 40, 500)")
    
    # C3: Cash Burn
    conn.execute("INSERT INTO financial_ratios VALUES ('C3', 2023, -20, 10)")
    conn.execute("INSERT INTO cashflow VALUES ('C3', 2023, 30)")
    conn.execute("INSERT INTO profitandloss VALUES ('C3', 2023, -10, 200)")
    
    conn.commit()
    conn.close()
    
    generate_capital_allocation_report(str(db_path), str(out_csv))
    
    assert os.path.exists(out_csv)
    
    df = pd.read_csv(out_csv)
    
    c1 = df[df['company_id'] == 'C1'].iloc[0]
    assert c1['fcf'] == 80
    assert c1['cfo_quality_score'] == 1.25
    assert c1['capex_intensity'] == 0.02
    assert c1['fcf_conversion'] == 1.0
    assert c1['capital_allocation_pattern'] == "Cash Cow / Returner"
    
    c2 = df[df['company_id'] == 'C2'].iloc[0]
    assert c2['capital_allocation_pattern'] == "Aggressive Expansion"
    
    c3 = df[df['company_id'] == 'C3'].iloc[0]
    assert c3['capital_allocation_pattern'] == "Cash Burn"
