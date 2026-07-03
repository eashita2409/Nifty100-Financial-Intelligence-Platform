import pytest
import sqlite3
import pandas as pd
import numpy as np
from src.analytics.peer import init_db_schema, clean_interest_coverage, calculate_peer_percentiles

@pytest.fixture
def mock_peer_db(tmp_path):
    db_path = tmp_path / "mock_peer.db"
    conn = sqlite3.connect(db_path)
    
    # Create required tables
    conn.execute("CREATE TABLE companies (id TEXT PRIMARY KEY, company_name TEXT)")
    conn.execute("CREATE TABLE peer_groups (company_id TEXT, peer_group_name TEXT)")
    
    conn.execute("""
    CREATE TABLE financial_ratios (
        company_id TEXT,
        year REAL,
        return_on_equity_pct REAL,
        return_on_capital_employed_pct REAL,
        net_profit_margin_pct REAL,
        debt_to_equity REAL,
        free_cash_flow_cr REAL,
        revenue_cagr_5yr REAL,
        pat_cagr_5yr REAL,
        eps_cagr_5yr REAL,
        interest_coverage TEXT,
        asset_turnover REAL,
        debt_free_label INTEGER
    )
    """)
    
    # Insert companies
    conn.execute("INSERT INTO companies VALUES ('C1', 'Company 1')")
    conn.execute("INSERT INTO companies VALUES ('C2', 'Company 2')")
    conn.execute("INSERT INTO companies VALUES ('C3', 'Company 3')")
    conn.execute("INSERT INTO companies VALUES ('C4', 'Company 4')") # No peer group
    
    # Insert peer groups
    conn.execute("INSERT INTO peer_groups VALUES ('C1', 'Group A')")
    conn.execute("INSERT INTO peer_groups VALUES ('C2', 'Group A')")
    conn.execute("INSERT INTO peer_groups VALUES ('C3', 'Group A')")
    # C4 has no peer group
    
    # Insert ratios for year 2024
    # ROEs: C1=10.0, C2=20.0, C3=30.0, C4=15.0
    # D/Es: C1=0.2, C2=0.8, C3=0.5, C4=0.1
    conn.execute("INSERT INTO financial_ratios VALUES ('C1', 2024, 10.0, 15.0, 12.0, 0.2, 50.0, 8.0, 10.0, 9.0, '5.0', 0.8, 0)")
    conn.execute("INSERT INTO financial_ratios VALUES ('C2', 2024, 20.0, 25.0, 18.0, 0.8, 150.0, 12.0, 15.0, 14.0, '2.0', 1.2, 0)")
    conn.execute("INSERT INTO financial_ratios VALUES ('C3', 2024, 30.0, 35.0, 22.0, 0.5, 200.0, 15.0, 20.0, 18.0, 'Debt Free', 1.5, 1)")
    conn.execute("INSERT INTO financial_ratios VALUES ('C4', 2024, 15.0, 18.0, 15.0, 0.1, 80.0, 9.0, 11.0, 10.0, '3.0', 0.9, 0)")
    
    conn.commit()
    conn.close()
    return db_path

def test_clean_interest_coverage():
    assert clean_interest_coverage('Debt Free', False) == float('inf')
    assert clean_interest_coverage('5.5', False) == 5.5
    assert clean_interest_coverage(None, True) == float('inf')
    assert clean_interest_coverage(None, False) is np.nan
    assert clean_interest_coverage('invalid', False) is np.nan

def test_init_db_schema(tmp_path):
    db_path = tmp_path / "test_init.db"
    conn = sqlite3.connect(db_path)
    init_db_schema(conn)
    
    # Check table exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='peer_percentiles'")
    assert cursor.fetchone() is not None
    conn.close()

def test_calculate_peer_percentiles(mock_peer_db):
    calculate_peer_percentiles(str(mock_peer_db))
    
    conn = sqlite3.connect(mock_peer_db)
    df = pd.read_sql_query("SELECT * FROM peer_percentiles", conn)
    conn.close()
    
    assert len(df) == 4
    
    # Check C1, C2, C3 (Group A)
    # ROE rankings for C1 (10.0), C2 (20.0), C3 (30.0) -> ranks should be 33.33, 66.67, 100.0
    c1 = df[df['company_id'] == 'C1'].iloc[0]
    c2 = df[df['company_id'] == 'C2'].iloc[0]
    c3 = df[df['company_id'] == 'C3'].iloc[0]
    
    assert c1['roe_rank'] == pytest.approx(33.33, abs=0.1)
    assert c2['roe_rank'] == pytest.approx(66.67, abs=0.1)
    assert c3['roe_rank'] == pytest.approx(100.0, abs=0.1)

    # Check inverse D/E rank
    # D/Es: C1=0.2 (rank 100.0), C3=0.5 (rank 66.67), C2=0.8 (rank 33.33)
    assert c1['debt_equity_rank'] == pytest.approx(100.0, abs=0.1)
    assert c3['debt_equity_rank'] == pytest.approx(66.67, abs=0.1)
    assert c2['debt_equity_rank'] == pytest.approx(33.33, abs=0.1)

    # Check C3 ICR rank is 100.0 because of 'Debt Free'
    assert c3['icr_rank'] == pytest.approx(100.0, abs=0.1)

def test_peer_fallback_logic(mock_peer_db):
    calculate_peer_percentiles(str(mock_peer_db))
    
    conn = sqlite3.connect(mock_peer_db)
    df = pd.read_sql_query("SELECT * FROM peer_percentiles", conn)
    conn.close()
    
    # C4 has no peer group, so it should be ranked globally against all companies (C1, C2, C3, C4)
    # ROEs: C1(10.0), C4(15.0), C2(20.0), C3(30.0)
    # Globally, C4's ROE rank should be 50.0% (2nd out of 4)
    c4 = df[df['company_id'] == 'C4'].iloc[0]
    assert c4['roe_rank'] == pytest.approx(50.0, abs=0.1)
