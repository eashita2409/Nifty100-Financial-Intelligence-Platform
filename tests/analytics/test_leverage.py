import pytest
import sqlite3
import pandas as pd
from pathlib import Path

from src.analytics.leverage import (
    calculate_debt_to_equity,
    is_high_leverage,
    calculate_interest_coverage_ratio,
    is_icr_warning,
    is_debt_free,
    calculate_net_debt,
    calculate_asset_turnover,
    populate_leverage_ratios
)

def test_debt_to_equity_normal():
    assert calculate_debt_to_equity(100, 200, 300) == 0.2

def test_debt_to_equity_zero_denom():
    assert calculate_debt_to_equity(100, -100, 100) is None

def test_high_leverage_flag():
    assert is_high_leverage(2.5) is True
    assert is_high_leverage(1.5) is False
    assert is_high_leverage(None) is False

def test_interest_coverage_ratio():
    assert calculate_interest_coverage_ratio(500, 100) == 5.0
    assert calculate_interest_coverage_ratio(500, 0) is None

def test_icr_warning():
    assert is_icr_warning(1.0) is True
    assert is_icr_warning(3.0) is False
    assert is_icr_warning(None) is False

def test_debt_free_label():
    assert is_debt_free(0) is True
    assert is_debt_free(0.4) is True
    assert is_debt_free(10) is False
    assert is_debt_free(None) is True

def test_net_debt():
    assert calculate_net_debt(100, 20) == 80.0
    assert calculate_net_debt(50, 100) == 0.0 # floor at 0

def test_asset_turnover():
    assert calculate_asset_turnover(1000, 500) == 2.0
    assert calculate_asset_turnover(1000, 0) is None

def test_populate_leverage_ratios(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    
    conn.execute("CREATE TABLE profitandloss (company_id TEXT, year REAL, sales REAL, profit_before_tax REAL, interest REAL)")
    conn.execute("CREATE TABLE balancesheet (company_id TEXT, year REAL, equity_capital REAL, reserves REAL, borrowings REAL, total_assets REAL)")
    conn.execute("CREATE TABLE financial_ratios (company_id TEXT, year REAL, debt_to_equity REAL, high_leverage_flag BOOLEAN, interest_coverage REAL, debt_free_label BOOLEAN, icr_warning_flag BOOLEAN, net_debt_cr REAL, asset_turnover REAL)")
    conn.execute("CREATE TABLE sectors (company_id TEXT, broad_sector TEXT)")
    
    # Insert dummy data
    conn.execute("INSERT INTO profitandloss VALUES ('C1', 2023, 1000, 200, 50)")
    conn.execute("INSERT INTO balancesheet VALUES ('C1', 2023, 200, 300, 1000, 2000)")
    conn.execute("INSERT INTO sectors VALUES ('C1', 'IT')")
    conn.execute("INSERT INTO financial_ratios (company_id, year) VALUES ('C1', 2023)")
    
    conn.commit()
    conn.close()
    
    populate_leverage_ratios(str(db_path))
    
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    conn.close()
    
    row = df.iloc[0]
    assert row['debt_to_equity'] == 2.0  # 1000 / 500
    assert bool(row['high_leverage_flag']) is False  # threshold is > 2.0
    assert row['interest_coverage'] == 5.0 # (200 + 50) / 50
    assert bool(row['debt_free_label']) is False
    assert bool(row['icr_warning_flag']) is False
    assert row['net_debt_cr'] == 1000.0
    assert row['asset_turnover'] == 0.5 # 1000 / 2000
