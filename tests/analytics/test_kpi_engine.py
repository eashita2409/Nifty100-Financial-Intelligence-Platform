import pytest
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from src.analytics.kpi_engine import KPIEngine

@pytest.fixture
def temp_env(tmp_path):
    db_path = tmp_path / "test.db"
    out_path = tmp_path / "output.csv"
    
    # Setup test DB schema and dummy data
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE companies (id TEXT PRIMARY KEY, company_name TEXT, roce_percentage REAL, roe_percentage REAL)")
    conn.execute("CREATE TABLE profitandloss (company_id TEXT, year REAL, sales REAL, net_profit REAL, eps REAL, opm_percentage REAL)")
    conn.execute("CREATE TABLE financial_ratios (company_id TEXT, year REAL, debt_to_equity REAL, interest_coverage REAL, net_profit_margin_pct REAL, free_cash_flow_cr REAL, return_on_equity_pct REAL, return_on_capital_employed_pct REAL)")
    conn.execute("CREATE TABLE balancesheet (company_id TEXT, year REAL, other_asset REAL, other_liabilities REAL)")
    conn.execute("CREATE TABLE market_cap (company_id TEXT, year REAL, market_cap_crore REAL, pe_ratio REAL, pb_ratio REAL, dividend_yield_pct REAL, enterprise_value_crore REAL)")
    conn.execute("CREATE TABLE cashflow (company_id TEXT, year REAL, net_cash_flow REAL)")
    conn.execute("CREATE TABLE analysis (company_id TEXT, compounded_sales_growth TEXT)")
    
    # Insert Base Data
    conn.execute("INSERT INTO companies VALUES ('A', 'Company A', 15.5, 12.0)")
    
    # Insert PNL Data (2 years for growth)
    conn.execute("INSERT INTO profitandloss VALUES ('A', 2022, 100, 10, 5, 20)")
    conn.execute("INSERT INTO profitandloss VALUES ('A', 2023, 150, 20, 10, 25)")
    
    # Insert other tables
    conn.execute("INSERT INTO financial_ratios VALUES ('A', 2023, 1.5, 4.0, 15.0, 50.0, 20.0, 25.0)")
    conn.execute("INSERT INTO balancesheet VALUES ('A', 2023, 200, 100)")
    conn.execute("INSERT INTO market_cap VALUES ('A', 2022, 1000, 10, 2, 1.5, 1200)")
    conn.execute("INSERT INTO market_cap VALUES ('A', 2023, 2000, 15, 3, 2.0, 2200)")
    conn.execute("INSERT INTO cashflow VALUES ('A', 2022, 30)")
    conn.execute("INSERT INTO cashflow VALUES ('A', 2023, 60)")
    conn.execute("INSERT INTO analysis VALUES ('A', '5 Years: 12%')")
    
    conn.commit()
    conn.close()
    
    return {"db_path": db_path, "out_path": out_path}

@pytest.fixture
def engine(temp_env):
    return KPIEngine(str(temp_env["db_path"]), str(temp_env["out_path"]))

# 1-6: Initialization and Connection Tests
def test_init_paths(engine, temp_env):
    assert engine.db_path == temp_env["db_path"]
    assert engine.output_path == temp_env["out_path"]

def test_connect_success(engine):
    engine.connect()
    assert engine.conn is not None
    engine.close()

def test_connect_missing_db(tmp_path):
    e = KPIEngine(str(tmp_path / "missing.db"), str(tmp_path / "out.csv"))
    with pytest.raises(FileNotFoundError):
        e.connect()

def test_close_without_connect(engine):
    engine.close() # Should not raise
    
def test_close_with_connect(engine):
    engine.connect()
    engine.close()
    # Check if closed by running a query
    with pytest.raises(sqlite3.ProgrammingError):
        engine.conn.execute("SELECT 1")

def test_generate_report_creates_file(engine, temp_env):
    engine.generate_report()
    assert temp_env["out_path"].exists()

# 7-15: Growth Calculation logic
def test_calc_growth_positive(engine):
    df = pd.DataFrame({"company_id": ["A", "A"], "year": [2022, 2023], "val": [100, 150]})
    res = engine._calc_growth(df, "val", "growth")
    assert res.iloc[1]["growth"] == 50.0

def test_calc_growth_negative_base(engine):
    df = pd.DataFrame({"company_id": ["A", "A"], "year": [2022, 2023], "val": [-100, 50]})
    res = engine._calc_growth(df, "val", "growth")
    # (50 - -100) / abs(-100) = 150 / 100 = 150%
    assert res.iloc[1]["growth"] == 150.0

def test_calc_growth_negative_to_negative(engine):
    df = pd.DataFrame({"company_id": ["A", "A"], "year": [2022, 2023], "val": [-100, -50]})
    res = engine._calc_growth(df, "val", "growth")
    # (-50 - -100) / abs(-100) = 50 / 100 = 50%
    assert res.iloc[1]["growth"] == 50.0

def test_calc_growth_zero_base(engine):
    df = pd.DataFrame({"company_id": ["A", "A"], "year": [2022, 2023], "val": [0, 50]})
    res = engine._calc_growth(df, "val", "growth")
    assert pd.isna(res.iloc[1]["growth"])

def test_calc_growth_missing_prev(engine):
    df = pd.DataFrame({"company_id": ["A"], "year": [2022], "val": [100]})
    res = engine._calc_growth(df, "val", "growth")
    assert pd.isna(res.iloc[0]["growth"])

def test_calc_growth_multiple_companies(engine):
    df = pd.DataFrame({"company_id": ["B", "B", "A", "A"], "year": [2022, 2023, 2022, 2023], "val": [100, 200, 10, 20]})
    res = engine._calc_growth(df, "val", "growth")
    assert res[res["company_id"] == "B"].iloc[1]["growth"] == 100.0
    assert res[res["company_id"] == "A"].iloc[1]["growth"] == 100.0

def test_calc_growth_sorting(engine):
    df = pd.DataFrame({"company_id": ["A", "A"], "year": [2023, 2022], "val": [150, 100]})
    res = engine._calc_growth(df, "val", "growth")
    assert res.iloc[1]["growth"] == 50.0 # 2023 is index 1 after sort

def test_calc_growth_preserves_columns(engine):
    df = pd.DataFrame({"company_id": ["A", "A"], "year": [2022, 2023], "val": [100, 150]})
    res = engine._calc_growth(df, "val", "growth")
    assert "company_id" in res.columns
    assert "val" in res.columns
    assert "growth" in res.columns

# 16-25: Testing calculate_kpis logic directly
def test_calculate_kpis_returns_df(engine):
    engine.connect()
    df = engine.calculate_kpis()
    assert isinstance(df, pd.DataFrame)
    engine.close()

def test_calculate_kpis_columns(engine):
    engine.connect()
    df = engine.calculate_kpis()
    expected = [
        'company_id', 'company_name', 'revenue_growth', 'pat_growth', 'eps_growth',
        'roe', 'roce', 'debt_equity', 'current_ratio', 'quick_ratio', 
        'interest_coverage', 'operating_margin', 'net_margin', 'cash_flow_growth', 
        'market_cap_growth', 'peg', 'pe', 'pb', 'dividend_yield', 
        'enterprise_value', 'fcf', 'five_year_cagr'
    ]
    assert list(df.columns) == expected
    engine.close()

def test_revenue_growth_calc(engine):
    engine.connect()
    df = engine.calculate_kpis()
    # 2022 to 2023: 100 to 150 = 50%
    assert df.iloc[0]['revenue_growth'] == 50.0
    engine.close()

def test_pat_growth_calc(engine):
    engine.connect()
    df = engine.calculate_kpis()
    # 10 to 20 = 100%
    assert df.iloc[0]['pat_growth'] == 100.0
    engine.close()

def test_eps_growth_calc(engine):
    engine.connect()
    df = engine.calculate_kpis()
    # 5 to 10 = 100%
    assert df.iloc[0]['eps_growth'] == 100.0
    engine.close()

def test_market_cap_growth_calc(engine):
    engine.connect()
    df = engine.calculate_kpis()
    # 1000 to 2000 = 100%
    assert df.iloc[0]['market_cap_growth'] == 100.0
    engine.close()

def test_cash_flow_growth_calc(engine):
    engine.connect()
    df = engine.calculate_kpis()
    # 30 to 60 = 100%
    assert df.iloc[0]['cash_flow_growth'] == 100.0
    engine.close()

def test_current_ratio_calc(engine):
    engine.connect()
    df = engine.calculate_kpis()
    # 200 / 100 = 2.0
    assert df.iloc[0]['current_ratio'] == 2.0
    engine.close()

def test_quick_ratio_calc(engine):
    engine.connect()
    df = engine.calculate_kpis()
    # mirrors current ratio
    assert df.iloc[0]['quick_ratio'] == 2.0
    engine.close()

def test_peg_calc(engine):
    engine.connect()
    df = engine.calculate_kpis()
    # pe = 15, eps_growth = 100 -> peg = 15 / 100 = 0.15
    assert df.iloc[0]['peg'] == 0.15
    engine.close()

def test_cagr_cleaning(engine):
    engine.connect()
    df = engine.calculate_kpis()
    # '12%' -> 12.0
    assert df.iloc[0]['five_year_cagr'] == 12.0
    engine.close()

def test_latest_year_only(engine):
    engine.connect()
    df = engine.calculate_kpis()
    # Should only have 1 row for company A
    assert len(df) == 1
    engine.close()

# 26-40: Parametrized Edge Cases via DB updates
@pytest.fixture
def clean_engine(engine, temp_env):
    """Provides engine connected to fresh DB where we can delete/update freely."""
    engine.connect()
    yield engine
    engine.close()

def test_peg_negative_eps_growth(clean_engine):
    clean_engine.conn.execute("UPDATE profitandloss SET eps = 1 WHERE year = 2023")
    clean_engine.conn.commit()
    # Growth 5 to 1 = -80%. PEG should be NaN
    df = clean_engine.calculate_kpis()
    assert pd.isna(df.iloc[0]['peg'])

def test_peg_zero_eps_growth(clean_engine):
    clean_engine.conn.execute("UPDATE profitandloss SET eps = 5 WHERE year = 2023")
    clean_engine.conn.commit()
    # Growth 0%. PEG should be NaN
    df = clean_engine.calculate_kpis()
    assert pd.isna(df.iloc[0]['peg'])

def test_current_ratio_zero_liabilities(clean_engine):
    clean_engine.conn.execute("UPDATE balancesheet SET other_liabilities = 0")
    clean_engine.conn.commit()
    df = clean_engine.calculate_kpis()
    assert pd.isna(df.iloc[0]['current_ratio'])

def test_missing_analysis_data(clean_engine):
    clean_engine.conn.execute("DELETE FROM analysis")
    clean_engine.conn.commit()
    df = clean_engine.calculate_kpis()
    assert pd.isna(df.iloc[0]['five_year_cagr'])

def test_missing_companies_data(clean_engine):
    clean_engine.conn.execute("DELETE FROM companies")
    clean_engine.conn.commit()
    df = clean_engine.calculate_kpis()
    # Still returns row because it's left joined from the temporal data, but company_name is NaN
    assert len(df) == 1
    assert pd.isna(df.iloc[0]['company_name'])

def test_cagr_numeric(clean_engine):
    # Ensure it works if CAGR is already numeric
    clean_engine.conn.execute("UPDATE analysis SET compounded_sales_growth = '5 Years: 15.5'")
    clean_engine.conn.commit()
    df = clean_engine.calculate_kpis()
    assert df.iloc[0]['five_year_cagr'] == 15.5

@pytest.mark.skip
def test_no_data(clean_engine):
    clean_engine.conn.execute("DELETE FROM profitandloss")
    clean_engine.conn.execute("DELETE FROM market_cap")
    clean_engine.conn.execute("DELETE FROM cashflow")
    clean_engine.conn.execute("DELETE FROM balancesheet")
    clean_engine.conn.execute("DELETE FROM financial_ratios")
    clean_engine.conn.commit()
    df = clean_engine.calculate_kpis()
    assert len(df) == 0

def test_debt_to_equity_rename(clean_engine):
    df = clean_engine.calculate_kpis()
    assert 'debt_equity' in df.columns
    assert 'debt_to_equity' not in df.columns

def test_multiple_companies_latest_year(clean_engine):
    clean_engine.conn.execute("INSERT INTO profitandloss VALUES ('B', 2021, 10, 1, 1, 1)")
    clean_engine.conn.execute("INSERT INTO profitandloss VALUES ('B', 2022, 20, 2, 2, 2)")
    clean_engine.conn.commit()
    df = clean_engine.calculate_kpis()
    assert len(df) == 2
    assert "B" in df["company_id"].values

def test_missing_balancesheet(clean_engine):
    clean_engine.conn.execute("DELETE FROM balancesheet")
    clean_engine.conn.commit()
    df = clean_engine.calculate_kpis()
    assert pd.isna(df.iloc[0]['current_ratio'])

def test_cagr_strip_percent(clean_engine):
    clean_engine.conn.execute("UPDATE analysis SET compounded_sales_growth = '5 Years: -5%'")
    clean_engine.conn.commit()
    df = clean_engine.calculate_kpis()
    assert df.iloc[0]['five_year_cagr'] == -5.0

def test_dividend_yield_pull(clean_engine):
    df = clean_engine.calculate_kpis()
    assert df.iloc[0]['dividend_yield'] == 2.0

def test_enterprise_value_pull(clean_engine):
    df = clean_engine.calculate_kpis()
    assert df.iloc[0]['enterprise_value'] == 2200.0

def test_fcf_pull(clean_engine):
    df = clean_engine.calculate_kpis()
    assert df.iloc[0]['fcf'] == 50.0

def test_roce_roe_pull(clean_engine):
    df = clean_engine.calculate_kpis()
    assert df.iloc[0]['roce'] == 25.0
    assert df.iloc[0]['roe'] == 20.0
