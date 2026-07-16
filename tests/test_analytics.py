import pytest
import os
from src.api.services import analytics
from src.api.schemas import RecommendRequest
from src.api.services import financials

def test_get_dashboard_summary(db_connection):
    summary = analytics.get_dashboard_summary(db_connection)
    assert 'total_companies' in summary
    assert 'total_market_cap' in summary
    assert 'sectors_count' in summary

def test_get_recommendations():
    # If the CSV exists, test it
    csv_path = 'data/processed/mutual_funds.csv'
    if os.path.exists(csv_path) or os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed', 'mutual_funds.csv')):
        req = RecommendRequest(risk_profile="Low")
        results = analytics.get_recommendations(req)
        assert isinstance(results, list)
        if len(results) > 0:
            assert 'scheme' in results[0]
            assert 'sharpe' in results[0]
            assert 'cagr' in results[0]

def test_financials_ratios(db_connection):
    ratios = financials.get_financial_ratios(db_connection, "RELIANCE")
    assert isinstance(ratios, list)
    if ratios:
        assert 'year' in ratios[0]
        assert 'return_on_equity_pct' in ratios[0]

def test_financials_cashflow(db_connection):
    cf = financials.get_cashflow(db_connection, "RELIANCE")
    assert isinstance(cf, list)
    if cf:
        assert 'operating_cash_flow' in cf[0]
        assert 'free_cash_flow' in cf[0]
