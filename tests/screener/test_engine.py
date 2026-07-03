import pytest
import sqlite3
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from src.screener.engine import ScreenerEngine

@pytest.fixture
def mock_db(tmp_path):
    db_path = tmp_path / "test_screener.db"
    conn = sqlite3.connect(db_path)
    
    # Create schema
    conn.execute("CREATE TABLE companies (id TEXT PRIMARY KEY, company_name TEXT, roce_percentage REAL, roe_percentage REAL)")
    conn.execute("CREATE TABLE sectors (company_id TEXT, broad_sector TEXT)")
    conn.execute("CREATE TABLE profitandloss (company_id TEXT, year REAL, sales REAL, net_profit REAL, eps REAL, opm_percentage REAL)")
    conn.execute("CREATE TABLE financial_ratios (company_id TEXT, year REAL, return_on_equity_pct REAL, return_on_capital_employed_pct REAL, debt_to_equity REAL, free_cash_flow_cr REAL, revenue_cagr_5yr REAL, pat_cagr_5yr REAL, operating_profit_margin_pct REAL, interest_coverage TEXT, eps_cagr_5yr REAL, asset_turnover REAL, debt_free_label INTEGER, cfo_quality_score REAL, net_profit_margin_pct REAL)")
    conn.execute("CREATE TABLE market_cap (company_id TEXT, year REAL, market_cap_crore REAL, pe_ratio REAL, pb_ratio REAL, dividend_yield_pct REAL, enterprise_value_crore REAL)")
    conn.execute("CREATE TABLE balancesheet (company_id TEXT, year REAL, other_asset REAL, other_liabilities REAL)")
    conn.execute("CREATE TABLE cashflow (company_id TEXT, year REAL, net_cash_flow REAL)")
    conn.execute("CREATE TABLE analysis (company_id TEXT, compounded_sales_growth TEXT)")
    
    # Company 1: Financials, High D/E, High ROE
    conn.execute("INSERT INTO companies VALUES ('FIN1', 'Financial Corp 1', 12.0, 18.0)")
    conn.execute("INSERT INTO sectors VALUES ('FIN1', 'Financials')")
    conn.execute("INSERT INTO profitandloss VALUES ('FIN1', 2024, 1000.0, 200.0, 10.0, 25.0)")
    conn.execute("INSERT INTO financial_ratios VALUES ('FIN1', 2024, 20.0, 18.0, 8.5, 50.0, 12.0, 15.0, 25.0, '1.2', 10.0, 0.8, 0, 1.0, 20.0)")
    conn.execute("INSERT INTO market_cap VALUES ('FIN1', 2024, 8000.0, 15.0, 2.5, 2.0, 9000.0)")
    conn.execute("INSERT INTO balancesheet VALUES ('FIN1', 2024, 100.0, 50.0)")
    conn.execute("INSERT INTO cashflow VALUES ('FIN1', 2024, 300.0)")
    conn.execute("INSERT INTO analysis VALUES ('FIN1', '5 Years: 12%')")

    # Company 2: IT, Low D/E, High ROE, Debt Free (ICR text 'Debt Free')
    conn.execute("INSERT INTO companies VALUES ('IT1', 'IT Services 1', 25.0, 30.0)")
    conn.execute("INSERT INTO sectors VALUES ('IT1', 'Technology')")
    conn.execute("INSERT INTO profitandloss VALUES ('IT1', 2024, 1500.0, 350.0, 20.0, 30.0)")
    conn.execute("INSERT INTO financial_ratios VALUES ('IT1', 2024, 30.0, 35.0, 0.0, 200.0, 15.0, 18.0, 30.0, 'Debt Free', 14.0, 1.2, 1, 1.2, 23.3)")
    conn.execute("INSERT INTO market_cap VALUES ('IT1', 2024, 12000.0, 25.0, 4.5, 1.5, 11000.0)")
    conn.execute("INSERT INTO balancesheet VALUES ('IT1', 2024, 200.0, 100.0)")
    conn.execute("INSERT INTO cashflow VALUES ('IT1', 2024, 500.0)")
    conn.execute("INSERT INTO analysis VALUES ('IT1', '5 Years: 15%')")

    # Company 3: Auto, Medium D/E, Low ROE
    conn.execute("INSERT INTO companies VALUES ('AUTO1', 'Auto Maker 1', 8.0, 9.0)")
    conn.execute("INSERT INTO sectors VALUES ('AUTO1', 'Consumer Cyclical')")
    conn.execute("INSERT INTO profitandloss VALUES ('AUTO1', 2024, 2000.0, 80.0, 5.0, 8.0)")
    conn.execute("INSERT INTO financial_ratios VALUES ('AUTO1', 2024, 8.0, 9.0, 1.2, -20.0, 4.0, 5.0, 8.0, '2.5', 2.0, 0.6, 0, 0.8, 4.0)")
    conn.execute("INSERT INTO market_cap VALUES ('AUTO1', 2024, 4000.0, 40.0, 6.0, 0.5, 4500.0)")
    conn.execute("INSERT INTO balancesheet VALUES ('AUTO1', 2024, 150.0, 120.0)")
    conn.execute("INSERT INTO cashflow VALUES ('AUTO1', 2024, 100.0)")
    conn.execute("INSERT INTO analysis VALUES ('AUTO1', '5 Years: 8%')")

    conn.commit()
    conn.close()
    return db_path

@pytest.fixture
def mock_config(tmp_path):
    config_path = tmp_path / "screener_config.yaml"
    config_data = {
        'screener': {
            'roe_min': 10.0,
            'roce_min': 10.0,
            'debt_equity_max': 1.5,
            'fcf_min': 0.0,
            'revenue_cagr_5y_min': 5.0,
            'pat_cagr_5y_min': 5.0,
            'opm_min': 10.0,
            'pe_max': 30.0,
            'pb_max': 5.0,
            'dividend_yield_min': 1.0,
            'interest_coverage_min': 3.0,
            'market_cap_min': 5000.0,
            'net_profit_min': 100.0,
            'eps_cagr_min': 5.0,
            'asset_turnover_min': 0.5,
            'sales_min': 500.0
        }
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(config_data, f)
    return config_path

# 1. Load config successfully
def test_load_config(mock_config):
    engine = ScreenerEngine()
    engine.load_config(str(mock_config))
    assert engine.config['roe_min'] == 10.0
    assert engine.config['pe_max'] == 30.0

# 2. Database data fetch successfully
def test_fetch_data(mock_db):
    engine = ScreenerEngine()
    df = engine.fetch_data(str(mock_db))
    assert len(df) == 3
    assert set(df['company_id']) == {'FIN1', 'IT1', 'AUTO1'}

# 3. Financial sector D/E filter bypass
def test_financial_de_bypass(mock_db, mock_config):
    engine = ScreenerEngine(str(mock_config))
    # Clear other filters so they don't affect FIN1
    engine.config = {'debt_equity_max': 1.0}
    df = engine.fetch_data(str(mock_db))
    filtered_df = engine.apply_filters(df, engine.config)
    # FIN1 (Financials) and IT1 (D/E = 0.0) should pass. AUTO1 (D/E = 1.2 > 1.0) should fail.
    assert 'FIN1' in filtered_df['company_id'].values
    assert 'IT1' in filtered_df['company_id'].values
    assert 'AUTO1' not in filtered_df['company_id'].values

# 4. Debt Free ICR behaves as infinity
def test_debt_free_icr_infinity(mock_db, mock_config):
    engine = ScreenerEngine(str(mock_config))
    # Set high interest coverage minimum (e.g. 50.0). Only IT1 (Debt Free = inf) should pass.
    engine.config['interest_coverage_min'] = 50.0
    df = engine.fetch_data(str(mock_db))
    filtered_df = engine.apply_filters(df, engine.config)
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['company_id'] == 'IT1'

# 5. Apply minimum filters correctly
def test_min_filters(mock_db, mock_config):
    engine = ScreenerEngine(str(mock_config))
    df = engine.fetch_data(str(mock_db))
    # Filter by market cap min 10000.0. Only IT1 should pass.
    engine.config = {'market_cap_min': 10000.0}
    filtered_df = engine.apply_filters(df, engine.config)
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['company_id'] == 'IT1'

# 6. Apply maximum filters correctly
def test_max_filters(mock_db, mock_config):
    engine = ScreenerEngine(str(mock_config))
    df = engine.fetch_data(str(mock_db))
    # Filter by pe max 20.0. Only FIN1 should pass.
    engine.config = {'pe_max': 20.0}
    filtered_df = engine.apply_filters(df, engine.config)
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['company_id'] == 'FIN1'

# 7. Composite quality score calculation
def test_composite_quality_score(mock_db):
    engine = ScreenerEngine()
    df = engine.fetch_data(str(mock_db))
    df_scored = engine.calculate_composite_quality_score(df)
    # Check that score ranges from 0 to 100
    scores = df_scored['composite_quality_score'].values
    assert all(0.0 <= s <= 100.0 for s in scores)
    # IT1 should have higher score than AUTO1
    it1_score = df_scored[df_scored['company_id'] == 'IT1'].iloc[0]['composite_quality_score']
    auto1_score = df_scored[df_scored['company_id'] == 'AUTO1'].iloc[0]['composite_quality_score']
    assert it1_score > auto1_score

# 8. Return sorted by composite_quality_score descending
def test_run_screener_sorting(mock_db, mock_config):
    engine = ScreenerEngine(str(mock_config))
    # Turn off filters so all 3 companies return
    engine.config = {}
    res = engine.run_screener(str(mock_db))
    assert len(res) == 3
    # Check sorting order
    scores = res['composite_quality_score'].values
    assert scores[0] >= scores[1] >= scores[2]

# 9. Handle subset of config thresholds missing/null
def test_missing_config_keys(mock_db, mock_config):
    engine = ScreenerEngine(str(mock_config))
    # Use config with most keys null
    engine.config = {'roe_min': 10.0, 'pe_max': None, 'market_cap_min': None}
    df = engine.fetch_data(str(mock_db))
    filtered_df = engine.apply_filters(df, engine.config)
    # FIN1 (20) and IT1 (30) pass roe_min=10. AUTO1 (8) fails.
    assert len(filtered_df) == 2
    assert set(filtered_df['company_id']) == {'FIN1', 'IT1'}

# 10. End-to-end execution on mock database
def test_e2e_screener(mock_db, mock_config):
    engine = ScreenerEngine(str(mock_config))
    res = engine.run_screener(str(mock_db))
    # With default config:
    # FIN1: roe=20, roce=18, dte=8.5 (Financials, passes de_max=1.0), fcf=50, rev_cagr=12, pat_cagr=15, opm=25, pe=15, pb=2.5, div=2.0, icr=1.2 (fails icr_min=3.0) -> FAILS E2E
    # IT1: roe=30, roce=35, dte=0.0, fcf=200, rev_cagr=15, pat_cagr=18, opm=30, pe=25, pb=4.5, div=1.5, icr=inf -> PASSES ALL
    # AUTO1: roe=8 (fails roe_min=10) -> FAILS E2E
    assert len(res) == 1
    assert res.iloc[0]['company_id'] == 'IT1'
