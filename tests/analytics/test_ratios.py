import pytest
import sqlite3
import pandas as pd
from pathlib import Path
import logging

from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_return_on_equity,
    calculate_return_on_capital_employed,
    calculate_return_on_assets,
    populate_profitability_ratios
)

def test_net_profit_margin_normal():
    # Normal calculation
    assert calculate_net_profit_margin(150, 1000) == 15.0

def test_net_profit_margin_zero_denominator():
    # Zero denominator
    assert calculate_net_profit_margin(150, 0) is None

def test_return_on_equity_normal():
    assert calculate_return_on_equity(200, 500, 300) == 25.0

def test_return_on_equity_negative_equity():
    # Negative equity + reserves <= 0
    assert calculate_return_on_equity(200, -200, 100) is None

def test_roce_bank():
    # Bank ROCE should return None for value and True for flag
    roce, flag = calculate_return_on_capital_employed(500, 1000, 500, 2000, is_financial_sector=True)
    assert roce is None
    assert flag is True

def test_roce_normal():
    roce, flag = calculate_return_on_capital_employed(350, 1000, 500, 500, is_financial_sector=False)
    assert roce == 17.5
    assert flag is False

def test_roa_zero_assets():
    # ROA assets=0
    assert calculate_return_on_assets(100, 0) is None

def test_opm_mismatch_logging(caplog):
    # OPM mismatch logging
    with caplog.at_level(logging.INFO):
        calculate_operating_profit_margin(200, 1000, opm_percentage_source=15.0, company_id="TEST", year=2023)
        assert "OPM Mismatch: TEST (2023) - Calculated: 20.0%, Source: 15.0%" in caplog.text

def test_populate_profitability_ratios(tmp_path):
    # Setup in-memory like db on disk for testing
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    
    conn.execute("CREATE TABLE profitandloss (company_id TEXT, year REAL, sales REAL, operating_profit REAL, opm_percentage REAL, net_profit REAL, profit_before_tax REAL, interest REAL)")
    conn.execute("CREATE TABLE balancesheet (company_id TEXT, year REAL, equity_capital REAL, reserves REAL, borrowings REAL, total_assets REAL)")
    conn.execute("CREATE TABLE sectors (company_id TEXT, broad_sector TEXT)")
    conn.execute("CREATE TABLE companies (id TEXT, company_name TEXT, roce_percentage REAL, roe_percentage REAL)")
    conn.execute("CREATE TABLE financial_ratios (company_id TEXT, year REAL, net_profit_margin_pct REAL, operating_profit_margin_pct REAL, return_on_equity_pct REAL, return_on_capital_employed_pct REAL, return_on_assets_pct REAL, sector_relative_roce BOOLEAN)")
    
    conn.execute("INSERT INTO profitandloss VALUES ('C1', 2023, 1000, 200, 20.0, 150, 180, 20)")
    conn.execute("INSERT INTO balancesheet VALUES ('C1', 2023, 500, 300, 200, 1200)")
    conn.execute("INSERT INTO sectors VALUES ('C1', 'IT')")
    conn.execute("INSERT INTO companies VALUES (\'C1\', \'Company 1\', 20.0, 15.0)")
    conn.execute("INSERT INTO financial_ratios (company_id, year) VALUES ('C1', 2023)")
    
    # Financial sector company
    conn.execute("INSERT INTO profitandloss VALUES ('B1', 2023, 2000, 400, 20.0, 300, 350, 50)")
    conn.execute("INSERT INTO balancesheet VALUES ('B1', 2023, 1000, 500, 3000, 5000)")
    conn.execute("INSERT INTO sectors VALUES ('B1', 'Financials')")
    conn.execute("INSERT INTO companies VALUES (\'B1\', \'Bank 1\', 10.0, 12.0)")
    conn.execute("INSERT INTO financial_ratios (company_id, year) VALUES ('B1', 2023)")
    
    conn.commit()
    conn.close()
    
    populate_profitability_ratios(str(db_path))
    
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    conn.close()
    
    # Check C1
    c1 = df[df['company_id'] == 'C1'].iloc[0]
    assert c1['net_profit_margin_pct'] == 15.0
    assert c1['operating_profit_margin_pct'] == 20.0
    assert c1['return_on_equity_pct'] == 18.75 # 150 / 800 * 100
    assert c1['return_on_capital_employed_pct'] == 20.0 # 200 / 1000 * 100
    assert c1['return_on_assets_pct'] == 12.5 # 150 / 1200 * 100
    assert not c1['sector_relative_roce']
    
    # Check B1
    b1 = df[df['company_id'] == 'B1'].iloc[0]
    assert pd.isna(b1['return_on_capital_employed_pct']) or b1['return_on_capital_employed_pct'] is None
    assert b1['sector_relative_roce']
