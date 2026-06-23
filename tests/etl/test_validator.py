"""
tests/etl/test_validator.py
============================
Nifty100 Financial Intelligence Platform — Sprint 1, Day 3
Bluestock Fintech

Unit and integration tests for src.etl.validator.

Covers all 16 DQ rules with at least 35 tests total:
  - Happy path (clean data passes)
  - Failure cases (bad data detected)
  - TTM exemption
  - Edge cases (empty DataFrames, missing columns, missing datasets)
  - Output structure (failures/summary CSV columns)
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict

import pandas as pd
import pytest

from src.etl.validator import (
    DQFailure,
    DQResult,
    FAILURES_COLUMNS,
    SUMMARY_COLUMNS,
    _is_ttm,
    _valid_company_ids,
    dq01_primary_key_uniqueness,
    dq02_composite_key_uniqueness,
    dq03_foreign_key_integrity,
    dq04_balance_sheet_equation,
    dq05_opm_cross_check,
    dq06_positive_sales,
    dq07_missing_company_ids,
    dq08_missing_ticker_symbols,
    dq09_duplicate_records,
    dq10_year_range_validation,
    dq11_positive_market_cap,
    dq12_positive_stock_prices,
    dq13_financial_ratio_range_checks,
    dq14_sector_mapping_validation,
    dq15_peer_group_mapping_validation,
    dq16_critical_null_field_validation,
    run_validation,
    write_failures,
    write_summary,
)


# =============================================================================
# Fixtures
# =============================================================================

def _companies() -> pd.DataFrame:
    return pd.DataFrame({
        "id": ["HDFCBANK", "TCS", "INFY", "RELIANCE"],
        "company_name": ["HDFC Bank", "Tata Consultancy", "Infosys", "Reliance Ind"],
        "face_value": [1.0, 1.0, 5.0, 10.0],
        "book_value": [200.0, 300.0, 150.0, 400.0],
        "roce_percentage": [15.0, 40.0, 35.0, 12.0],
        "roe_percentage": [16.0, 45.0, 30.0, 11.0],
    })


def _balancesheet(n: int = 4) -> pd.DataFrame:
    return pd.DataFrame({
        "id": range(1, n + 1),
        "company_id": ["HDFCBANK", "TCS", "INFY", "RELIANCE"][:n],
        "year": [2022, 2022, 2022, 2022][:n],
        "equity_capital": [100.0] * n,
        "reserves": [500.0] * n,
        "borrowings": [200.0] * n,
        "other_liabilities": [200.0] * n,
        "total_liabilities": [1000.0] * n,
        "fixed_assets": [300.0] * n,
        "cwip": [50.0] * n,
        "investments": [150.0] * n,
        "other_asset": [500.0] * n,
        "total_assets": [1000.0] * n,
    })


def _profitandloss() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 3, 4],
        "company_id": ["HDFCBANK", "TCS", "INFY", "RELIANCE"],
        "year": [2022.0, 2022.0, 2022.0, 2022.0],
        "sales": [10000, 20000, 15000, 25000],
        "expenses": [8000, 14000, 11000, 20000],
        "operating_profit": [2000.0, 6000.0, 4000.0, 5000.0],
        "opm_percentage": [20.0, 30.0, 26.7, 20.0],
        "other_income": [100, 200, 150, 300],
        "interest": [50, 20, 10, 100],
        "depreciation": [200, 300, 250, 400],
        "profit_before_tax": [1850, 5880, 3890, 4800],
        "tax_percentage": [25.0, 25.0, 25.0, 25.0],
        "net_profit": [1400, 4400, 2900, 3600],
        "eps": [20.0, 120.0, 80.0, 52.0],
        "dividend_payout": [20.0, 40.0, 35.0, 15.0],
    })


def _market_cap() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 3, 4],
        "company_id": ["HDFCBANK", "TCS", "INFY", "RELIANCE"],
        "year": [2022, 2022, 2022, 2022],
        "market_cap_crore": [800000.0, 1200000.0, 600000.0, 1500000.0],
        "enterprise_value_crore": [820000.0, 1180000.0, 580000.0, 1520000.0],
        "pe_ratio": [22.5, 30.0, 25.0, 28.0],
        "pb_ratio": [3.5, 12.0, 7.0, 2.8],
        "ev_ebitda": [18.0, 22.0, 20.0, 15.0],
        "dividend_yield_pct": [1.2, 1.0, 2.5, 0.8],
    })


def _financial_ratios() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 3, 4],
        "company_id": ["HDFCBANK", "TCS", "INFY", "RELIANCE"],
        "year": [2022, 2022, 2022, 2022],
        "net_profit_margin_pct": [14.0, 22.0, 19.0, 14.4],
        "operating_profit_margin_pct": [20, 30, 27, 20],
        "return_on_equity_pct": [16.0, 45.0, 30.0, 11.0],
        "debt_to_equity": [0.5, 0.0, 0.0, 0.8],
        "interest_coverage": [5.0, None, None, 3.0],
        "asset_turnover": [0.1, 1.5, 1.2, 0.4],
        "free_cash_flow_cr": [2000, 5000, 4000, 3000],
        "capex_cr": [500, 1000, 800, 2000],
        "earnings_per_share": [50, 120, 80, 52],
        "book_value_per_share": [300, 200, 150, 400],
        "dividend_payout_ratio_pct": [20, 40, 35, 15],
        "total_debt_cr": [5000, 0, 0, 20000],
        "cash_from_operations_cr": [4000, 8000, 6000, 5000],
    })


def _sectors() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 3, 4],
        "company_id": ["HDFCBANK", "TCS", "INFY", "RELIANCE"],
        "broad_sector": ["Financials", "IT", "IT", "Energy"],
        "sub_sector": ["Banking", "Software", "Software", "Oil & Gas"],
        "index_weight_pct": [9.0, 8.5, 5.0, 10.0],
        "market_cap_category": ["Large Cap"] * 4,
    })


def _peer_groups() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 3, 4],
        "peer_group_name": ["Banks", "IT", "IT", "Energy"],
        "company_id": ["HDFCBANK", "TCS", "INFY", "RELIANCE"],
        "is_benchmark": [True, True, False, True],
    })


def _stock_prices() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 3, 4],
        "company_id": ["HDFCBANK", "TCS", "INFY", "RELIANCE"],
        "date": ["2022-01-01"] * 4,
        "open_price": [1500.0, 3500.0, 1800.0, 2400.0],
        "high_price": [1550.0, 3600.0, 1850.0, 2450.0],
        "low_price": [1480.0, 3450.0, 1780.0, 2380.0],
        "close_price": [1520.0, 3550.0, 1820.0, 2420.0],
        "volume": [1000000, 500000, 750000, 1200000],
        "adjusted_close": [1520.0, 3550.0, 1820.0, 2420.0],
    })


@pytest.fixture()
def clean_datasets() -> Dict[str, pd.DataFrame]:
    return {
        "companies":        _companies(),
        "balancesheet":     _balancesheet(),
        "profitandloss":    _profitandloss(),
        "market_cap":       _market_cap(),
        "financial_ratios": _financial_ratios(),
        "sectors":          _sectors(),
        "peer_groups":      _peer_groups(),
        "stock_prices":     _stock_prices(),
        "cashflow": pd.DataFrame({
            "id": [1, 2],
            "company_id": ["HDFCBANK", "TCS"],
            "year": [2022, 2022],
            "operating_activity": [5000.0, 8000.0],
            "investing_activity": [-2000.0, -3000.0],
            "financing_activity": [-1000.0, -2000.0],
            "net_cash_flow": [2000.0, 3000.0],
        }),
    }


# =============================================================================
# Helper: _is_ttm
# =============================================================================

class TestIsTtm:
    def test_ttm_string_detected(self):
        assert _is_ttm("TTM") is True

    def test_ttm_lowercase(self):
        assert _is_ttm("ttm") is True

    def test_ttm_with_spaces(self):
        assert _is_ttm("  TTM  ") is True

    def test_numeric_year_not_ttm(self):
        assert _is_ttm(2023) is False

    def test_nan_not_ttm(self):
        assert _is_ttm(float("nan")) is False

    def test_none_not_ttm(self):
        assert _is_ttm(None) is False


# =============================================================================
# DQ-01  Primary Key Uniqueness
# =============================================================================

class TestDQ01:
    def test_clean_data_passes(self, clean_datasets):
        r = dq01_primary_key_uniqueness(clean_datasets)
        assert r.total_failed == 0

    def test_duplicate_id_detected(self, clean_datasets):
        df = clean_datasets["balancesheet"].copy()
        df.loc[3, "id"] = df.loc[0, "id"]  # Force duplicate id
        clean_datasets["balancesheet"] = df
        r = dq01_primary_key_uniqueness(clean_datasets)
        assert r.total_failed > 0

    def test_result_severity_is_critical(self, clean_datasets):
        r = dq01_primary_key_uniqueness(clean_datasets)
        assert r.severity == "CRITICAL"

    def test_total_checked_covers_all_rows(self, clean_datasets):
        r = dq01_primary_key_uniqueness(clean_datasets)
        # Should have checked all rows across tables that have an 'id' column
        assert r.total_checked > 0


# =============================================================================
# DQ-02  Composite Key Uniqueness
# =============================================================================

class TestDQ02:
    def test_clean_data_passes(self, clean_datasets):
        r = dq02_composite_key_uniqueness(clean_datasets)
        assert r.total_failed == 0

    def test_duplicate_composite_key_detected(self, clean_datasets):
        df = clean_datasets["balancesheet"].copy()
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)  # Duplicate first row
        clean_datasets["balancesheet"] = df
        r = dq02_composite_key_uniqueness(clean_datasets)
        assert r.total_failed > 0

    def test_ttm_rows_are_exempt(self, clean_datasets):
        df = clean_datasets["profitandloss"].copy()
        # Add two TTM rows for the same company — should NOT be flagged
        ttm_row = df.iloc[0].copy()
        ttm_row["year"] = None  # TTM is stored as null after normalisation
        df = pd.concat([df, ttm_row.to_frame().T, ttm_row.to_frame().T], ignore_index=True)
        clean_datasets["profitandloss"] = df
        r = dq02_composite_key_uniqueness(clean_datasets)
        # TTM rows excluded, no new failures from them
        assert r.total_failed == 0

    def test_rule_id_correct(self, clean_datasets):
        r = dq02_composite_key_uniqueness(clean_datasets)
        assert r.rule_id == "DQ-02"


# =============================================================================
# DQ-03  Foreign Key Integrity
# =============================================================================

class TestDQ03:
    def test_clean_data_passes(self, clean_datasets):
        r = dq03_foreign_key_integrity(clean_datasets)
        assert r.total_failed == 0

    def test_orphan_company_id_detected(self, clean_datasets):
        df = clean_datasets["balancesheet"].copy()
        df.loc[0, "company_id"] = "GHOST_CO"
        clean_datasets["balancesheet"] = df
        r = dq03_foreign_key_integrity(clean_datasets)
        assert r.total_failed >= 1

    def test_failure_message_contains_company_id(self, clean_datasets):
        df = clean_datasets["balancesheet"].copy()
        df.loc[0, "company_id"] = "UNKNOWN"
        clean_datasets["balancesheet"] = df
        r = dq03_foreign_key_integrity(clean_datasets)
        assert any("UNKNOWN" in f.issue_description for f in r.failures)

    def test_missing_companies_table_returns_empty(self):
        datasets = {"balancesheet": _balancesheet()}
        r = dq03_foreign_key_integrity(datasets)
        assert r.total_failed == 0  # Can't check without reference table


# =============================================================================
# DQ-04  Balance Sheet Equation
# =============================================================================

class TestDQ04:
    def test_clean_data_passes(self, clean_datasets):
        r = dq04_balance_sheet_equation(clean_datasets)
        assert r.total_failed == 0

    def test_imbalance_detected(self, clean_datasets):
        df = clean_datasets["balancesheet"].copy()
        df.loc[0, "total_assets"] = df.loc[0, "total_liabilities"] + 500  # Imbalance
        clean_datasets["balancesheet"] = df
        r = dq04_balance_sheet_equation(clean_datasets)
        assert r.total_failed >= 1

    def test_rounding_tolerance_respected(self, clean_datasets):
        df = clean_datasets["balancesheet"].copy()
        df.loc[0, "total_assets"] = df.loc[0, "total_liabilities"] + 0.5  # Within ±1 tolerance
        clean_datasets["balancesheet"] = df
        r = dq04_balance_sheet_equation(clean_datasets)
        assert r.total_failed == 0

    def test_severity_is_critical(self, clean_datasets):
        r = dq04_balance_sheet_equation(clean_datasets)
        assert r.severity == "CRITICAL"


# =============================================================================
# DQ-05  OPM Cross-Check
# =============================================================================

class TestDQ05:
    def test_clean_data_passes(self, clean_datasets):
        r = dq05_opm_cross_check(clean_datasets)
        assert r.total_failed == 0

    def test_opm_mismatch_detected(self, clean_datasets):
        df = clean_datasets["profitandloss"].copy()
        df.loc[0, "opm_percentage"] = 99.0  # Wildly wrong
        clean_datasets["profitandloss"] = df
        r = dq05_opm_cross_check(clean_datasets)
        assert r.total_failed >= 1

    def test_severity_is_warning(self, clean_datasets):
        r = dq05_opm_cross_check(clean_datasets)
        assert r.severity == "WARNING"

    def test_zero_sales_row_skipped(self, clean_datasets):
        df = clean_datasets["profitandloss"].copy()
        df.loc[0, "sales"] = 0
        clean_datasets["profitandloss"] = df
        # Should not crash or produce division-by-zero failure
        r = dq05_opm_cross_check(clean_datasets)
        assert isinstance(r, DQResult)


# =============================================================================
# DQ-06  Positive Sales
# =============================================================================

class TestDQ06:
    def test_clean_data_passes(self, clean_datasets):
        r = dq06_positive_sales(clean_datasets)
        assert r.total_failed == 0

    def test_zero_sales_detected(self, clean_datasets):
        df = clean_datasets["profitandloss"].copy()
        df.loc[0, "sales"] = 0
        clean_datasets["profitandloss"] = df
        r = dq06_positive_sales(clean_datasets)
        assert r.total_failed >= 1

    def test_negative_sales_detected(self, clean_datasets):
        df = clean_datasets["profitandloss"].copy()
        df.loc[1, "sales"] = -500
        clean_datasets["profitandloss"] = df
        r = dq06_positive_sales(clean_datasets)
        assert r.total_failed >= 1


# =============================================================================
# DQ-07  Missing Company IDs
# =============================================================================

class TestDQ07:
    def test_clean_data_passes(self, clean_datasets):
        r = dq07_missing_company_ids(clean_datasets)
        assert r.total_failed == 0

    def test_null_company_id_detected(self, clean_datasets):
        df = clean_datasets["balancesheet"].copy()
        df.loc[0, "company_id"] = None
        clean_datasets["balancesheet"] = df
        r = dq07_missing_company_ids(clean_datasets)
        assert r.total_failed >= 1

    def test_empty_string_company_id_detected(self, clean_datasets):
        df = clean_datasets["balancesheet"].copy()
        df.loc[0, "company_id"] = "   "
        clean_datasets["balancesheet"] = df
        r = dq07_missing_company_ids(clean_datasets)
        assert r.total_failed >= 1

    def test_severity_critical(self, clean_datasets):
        r = dq07_missing_company_ids(clean_datasets)
        assert r.severity == "CRITICAL"


# =============================================================================
# DQ-08  Missing Ticker Symbols
# =============================================================================

class TestDQ08:
    def test_clean_data_passes(self, clean_datasets):
        r = dq08_missing_ticker_symbols(clean_datasets)
        assert r.total_failed == 0

    def test_null_ticker_detected(self, clean_datasets):
        df = clean_datasets["companies"].copy()
        df.loc[0, "id"] = None
        clean_datasets["companies"] = df
        r = dq08_missing_ticker_symbols(clean_datasets)
        assert r.total_failed >= 1

    def test_missing_companies_table_no_crash(self):
        r = dq08_missing_ticker_symbols({})
        assert r.total_failed == 0


# =============================================================================
# DQ-09  Duplicate Records
# =============================================================================

class TestDQ09:
    def test_clean_data_passes(self, clean_datasets):
        r = dq09_duplicate_records(clean_datasets)
        assert r.total_failed == 0

    def test_exact_duplicate_detected(self, clean_datasets):
        df = clean_datasets["sectors"].copy()
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        clean_datasets["sectors"] = df
        r = dq09_duplicate_records(clean_datasets)
        assert r.total_failed >= 1

    def test_severity_is_warning(self, clean_datasets):
        r = dq09_duplicate_records(clean_datasets)
        assert r.severity == "WARNING"


# =============================================================================
# DQ-10  Year Range Validation
# =============================================================================

class TestDQ10:
    def test_clean_data_passes(self, clean_datasets):
        r = dq10_year_range_validation(clean_datasets)
        assert r.total_failed == 0

    def test_out_of_range_year_detected(self, clean_datasets):
        df = clean_datasets["balancesheet"].copy()
        df.loc[0, "year"] = 1800  # Way out of range
        clean_datasets["balancesheet"] = df
        r = dq10_year_range_validation(clean_datasets)
        assert r.total_failed >= 1

    def test_ttm_null_rows_are_exempt(self, clean_datasets):
        """TTM rows (stored as null after normalisation) must not be flagged."""
        df = clean_datasets["profitandloss"].copy()
        df.loc[0, "year"] = None  # TTM → null
        clean_datasets["profitandloss"] = df
        r = dq10_year_range_validation(clean_datasets)
        assert r.total_failed == 0

    def test_boundary_years_pass(self, clean_datasets):
        df = clean_datasets["balancesheet"].copy()
        df.loc[0, "year"] = 1990
        df.loc[1, "year"] = 2030
        clean_datasets["balancesheet"] = df
        r = dq10_year_range_validation(clean_datasets)
        assert r.total_failed == 0


# =============================================================================
# DQ-11  Positive Market Cap
# =============================================================================

class TestDQ11:
    def test_clean_data_passes(self, clean_datasets):
        r = dq11_positive_market_cap(clean_datasets)
        assert r.total_failed == 0

    def test_zero_market_cap_detected(self, clean_datasets):
        df = clean_datasets["market_cap"].copy()
        df.loc[0, "market_cap_crore"] = 0.0
        clean_datasets["market_cap"] = df
        r = dq11_positive_market_cap(clean_datasets)
        assert r.total_failed >= 1

    def test_negative_market_cap_detected(self, clean_datasets):
        df = clean_datasets["market_cap"].copy()
        df.loc[0, "market_cap_crore"] = -1000.0
        clean_datasets["market_cap"] = df
        r = dq11_positive_market_cap(clean_datasets)
        assert r.total_failed >= 1


# =============================================================================
# DQ-12  Positive Stock Prices
# =============================================================================

class TestDQ12:
    def test_clean_data_passes(self, clean_datasets):
        r = dq12_positive_stock_prices(clean_datasets)
        assert r.total_failed == 0

    def test_zero_close_price_detected(self, clean_datasets):
        df = clean_datasets["stock_prices"].copy()
        df.loc[0, "close_price"] = 0.0
        clean_datasets["stock_prices"] = df
        r = dq12_positive_stock_prices(clean_datasets)
        assert r.total_failed >= 1

    def test_negative_price_detected(self, clean_datasets):
        df = clean_datasets["stock_prices"].copy()
        df.loc[1, "open_price"] = -50.0
        clean_datasets["stock_prices"] = df
        r = dq12_positive_stock_prices(clean_datasets)
        assert r.total_failed >= 1

    def test_severity_critical(self, clean_datasets):
        r = dq12_positive_stock_prices(clean_datasets)
        assert r.severity == "CRITICAL"


# =============================================================================
# DQ-13  Financial Ratio Range Checks
# =============================================================================

class TestDQ13:
    def test_clean_data_passes(self, clean_datasets):
        r = dq13_financial_ratio_range_checks(clean_datasets)
        assert r.total_failed == 0

    def test_extreme_pe_ratio_detected(self, clean_datasets):
        df = clean_datasets["market_cap"].copy()
        df.loc[0, "pe_ratio"] = 9999.0  # Beyond upper bound
        clean_datasets["market_cap"] = df
        r = dq13_financial_ratio_range_checks(clean_datasets)
        assert r.total_failed >= 1

    def test_severity_is_warning(self, clean_datasets):
        r = dq13_financial_ratio_range_checks(clean_datasets)
        assert r.severity == "WARNING"


# =============================================================================
# DQ-14  Sector Mapping Validation
# =============================================================================

class TestDQ14:
    def test_clean_data_passes(self, clean_datasets):
        r = dq14_sector_mapping_validation(clean_datasets)
        assert r.total_failed == 0

    def test_missing_sector_detected(self, clean_datasets):
        # Remove one company from sectors
        df = clean_datasets["sectors"].copy()
        df = df[df["company_id"] != "HDFCBANK"]
        clean_datasets["sectors"] = df
        r = dq14_sector_mapping_validation(clean_datasets)
        assert r.total_failed >= 1

    def test_failure_identifies_company(self, clean_datasets):
        df = clean_datasets["sectors"].copy()
        df = df[df["company_id"] != "TCS"]
        clean_datasets["sectors"] = df
        r = dq14_sector_mapping_validation(clean_datasets)
        assert any("TCS" in f.row_identifier for f in r.failures)


# =============================================================================
# DQ-15  Peer Group Mapping Validation
# =============================================================================

class TestDQ15:
    def test_clean_data_passes(self, clean_datasets):
        r = dq15_peer_group_mapping_validation(clean_datasets)
        assert r.total_failed == 0

    def test_company_without_peer_group_detected(self, clean_datasets):
        df = clean_datasets["peer_groups"].copy()
        df = df[df["company_id"] != "INFY"]
        clean_datasets["peer_groups"] = df
        r = dq15_peer_group_mapping_validation(clean_datasets)
        assert r.total_failed >= 1

    def test_severity_is_warning(self, clean_datasets):
        r = dq15_peer_group_mapping_validation(clean_datasets)
        assert r.severity == "WARNING"


# =============================================================================
# DQ-16  Critical Null Field Validation
# =============================================================================

class TestDQ16:
    def test_clean_data_passes(self, clean_datasets):
        r = dq16_critical_null_field_validation(clean_datasets)
        assert r.total_failed == 0

    def test_null_sales_detected(self, clean_datasets):
        df = clean_datasets["profitandloss"].copy()
        df.loc[0, "sales"] = None
        clean_datasets["profitandloss"] = df
        r = dq16_critical_null_field_validation(clean_datasets)
        assert r.total_failed >= 1

    def test_null_total_assets_detected(self, clean_datasets):
        df = clean_datasets["balancesheet"].copy()
        df.loc[0, "total_assets"] = None
        clean_datasets["balancesheet"] = df
        r = dq16_critical_null_field_validation(clean_datasets)
        assert r.total_failed >= 1

    def test_null_close_price_detected(self, clean_datasets):
        df = clean_datasets["stock_prices"].copy()
        df.loc[0, "close_price"] = None
        clean_datasets["stock_prices"] = df
        r = dq16_critical_null_field_validation(clean_datasets)
        assert r.total_failed >= 1

    def test_severity_critical(self, clean_datasets):
        r = dq16_critical_null_field_validation(clean_datasets)
        assert r.severity == "CRITICAL"


# =============================================================================
# Output writers
# =============================================================================

class TestWriters:
    def test_write_failures_creates_file(self, tmp_path):
        failures = [
            DQFailure("DQ-01", "CRITICAL", "test_table", "id=1", "Duplicate id")
        ]
        path = tmp_path / "failures.csv"
        write_failures(failures, path)
        assert path.exists()

    def test_write_failures_has_correct_columns(self, tmp_path):
        failures = [
            DQFailure("DQ-02", "WARNING", "balancesheet", "ABB|2022", "Duplicate key")
        ]
        path = tmp_path / "failures.csv"
        write_failures(failures, path)
        df = pd.read_csv(path)
        for col in FAILURES_COLUMNS:
            assert col in df.columns

    def test_write_summary_creates_file(self, tmp_path):
        results = [DQResult("DQ-01", "CRITICAL", total_checked=100)]
        path = tmp_path / "summary.csv"
        write_summary(results, path)
        assert path.exists()

    def test_write_summary_has_correct_columns(self, tmp_path):
        results = [DQResult("DQ-01", "CRITICAL", total_checked=50)]
        path = tmp_path / "summary.csv"
        write_summary(results, path)
        df = pd.read_csv(path)
        for col in SUMMARY_COLUMNS:
            assert col in df.columns

    def test_write_empty_failures(self, tmp_path):
        path = tmp_path / "empty_failures.csv"
        write_failures([], path)
        assert path.exists()
        df = pd.read_csv(path)
        assert len(df) == 0


# =============================================================================
# run_validation (integration against real data/processed)
# =============================================================================

class TestRunValidation:
    def test_returns_tuple(self):
        results, failures_df = run_validation()
        assert isinstance(results, list)
        assert isinstance(failures_df, pd.DataFrame)

    def test_exactly_16_rules_run(self):
        results, _ = run_validation()
        assert len(results) == 16

    def test_failures_df_has_correct_columns(self):
        _, failures_df = run_validation()
        if not failures_df.empty:
            for col in FAILURES_COLUMNS:
                assert col in failures_df.columns

    def test_all_results_have_rule_id(self):
        results, _ = run_validation()
        for r in results:
            assert r.rule_id.startswith("DQ-")

    def test_dq01_passes_on_real_data(self):
        """Primary keys should be unique in all processed datasets."""
        results, _ = run_validation()
        dq01 = next(r for r in results if r.rule_id == "DQ-01")
        assert dq01.total_failed == 0

    def test_dq04_passes_on_real_data(self):
        """Balance sheet equation should hold for all real data rows."""
        results, _ = run_validation()
        dq04 = next(r for r in results if r.rule_id == "DQ-04")
        assert dq04.total_failed == 0

    def test_dq07_passes_on_real_data(self):
        """No missing company IDs in real processed data."""
        results, _ = run_validation()
        dq07 = next(r for r in results if r.rule_id == "DQ-07")
        assert dq07.total_failed == 0

    def test_output_csvs_written(self):
        run_validation()
        assert Path("output/validation_failures.csv").exists()
        assert Path("output/dq_summary.csv").exists()
