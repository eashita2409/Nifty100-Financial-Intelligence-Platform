"""
tests/etl/test_normalizer.py
============================
Nifty100 Financial Intelligence Platform — Sprint 1, Day 2
Bluestock Fintech

Unit tests for src.etl.normalizer.

Covers:
  - normalize_column_names: snake_case, special chars, %, duplicates, empty
  - normalize_ticker: uppercase, whitespace, None, numeric, NaN
  - normalize_year: all raw formats found in Nifty100 data
  - strip_whitespace: string columns only
  - normalize_dataframe: end-to-end pipeline
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from src.etl.normalizer import (
    normalize_column_names,
    normalize_dataframe,
    normalize_ticker,
    normalize_year,
    strip_whitespace,
)


# =============================================================================
# normalize_column_names
# =============================================================================

class TestNormalizeColumnNames:
    """Tests for normalize_column_names."""

    def test_basic_snake_case(self):
        result = normalize_column_names(["Company Name", "Net Profit"])
        assert result == ["company_name", "net_profit"]

    def test_already_snake_case(self):
        result = normalize_column_names(["company_id", "year"])
        assert result == ["company_id", "year"]

    def test_percent_sign_replaced_with_pct(self):
        result = normalize_column_names(["OPM%", "Net Profit%"])
        assert result == ["opm_pct", "net_profit_pct"]

    def test_special_characters_collapsed(self):
        result = normalize_column_names(["Cash & Equivalents", "P/E Ratio"])
        assert result == ["cash_equivalents", "p_e_ratio"]

    def test_multiple_spaces_collapsed(self):
        result = normalize_column_names(["  Total   Assets  "])
        assert result == ["total_assets"]

    def test_numeric_column_label(self):
        result = normalize_column_names([1, 2, 3])
        assert result == ["1", "2", "3"]

    def test_empty_column_label_gets_unnamed(self):
        result = normalize_column_names([pd.NA, "", None])
        # All three are empty/null; should get unnamed_0, unnamed_1, unnamed_2
        assert all(r.startswith("unnamed_") for r in result)

    def test_duplicate_columns_deduplicated(self):
        result = normalize_column_names(["sales", "sales", "sales"])
        assert result[0] == "sales"
        assert result[1] == "sales_1"
        assert result[2] == "sales_2"

    def test_leading_trailing_underscores_stripped(self):
        result = normalize_column_names(["_internal_", "__double__"])
        assert not result[0].startswith("_")
        assert not result[0].endswith("_")

    def test_mixed_case_lowercased(self):
        result = normalize_column_names(["CompanyID", "TICKER", "NetProfit"])
        assert result == ["companyid", "ticker", "netprofit"]

    def test_returns_list(self):
        result = normalize_column_names(["a", "b"])
        assert isinstance(result, list)

    def test_empty_input(self):
        result = normalize_column_names([])
        assert result == []

    def test_real_bluestock_columns(self):
        """Validate against actual column names seen in Nifty100 raw files."""
        raw = [
            "id", "company_id", "year", "equity_capital", "reserves",
            "borrowings", "other_liabilities", "total_liabilities",
            "fixed_assets", "cwip", "investments", "other_asset", "total_assets",
        ]
        result = normalize_column_names(raw)
        # Already snake_case — should be unchanged
        assert result == raw


# =============================================================================
# normalize_ticker
# =============================================================================

class TestNormalizeTicker:
    """Tests for normalize_ticker."""

    def test_lowercase_to_uppercase(self):
        assert normalize_ticker("hdfcbank") == "HDFCBANK"

    def test_already_uppercase(self):
        assert normalize_ticker("INFY") == "INFY"

    def test_strips_whitespace(self):
        assert normalize_ticker("  TCS  ") == "TCS"

    def test_mixed_case(self):
        assert normalize_ticker("  relIance  ") == "RELIANCE"

    def test_none_returns_empty_string(self):
        assert normalize_ticker(None) == ""

    def test_nan_returns_empty_string(self):
        assert normalize_ticker(float("nan")) == ""

    def test_numeric_input_stringified(self):
        # Unusual but safe — should not crash
        result = normalize_ticker(12345)
        assert result == "12345"

    def test_empty_string(self):
        assert normalize_ticker("") == ""

    def test_whitespace_only(self):
        assert normalize_ticker("   ") == ""

    def test_real_nifty100_tickers(self):
        tickers = ["HDFCBANK", "TCS", "RELIANCE", "INFY", "SBILIFE"]
        for t in tickers:
            assert normalize_ticker(t) == t

    def test_lowercase_nifty100_tickers(self):
        pairs = [
            ("hdfcbank", "HDFCBANK"),
            ("tcs", "TCS"),
            ("sbilife", "SBILIFE"),
        ]
        for raw, expected in pairs:
            assert normalize_ticker(raw) == expected


# =============================================================================
# normalize_year
# =============================================================================

class TestNormalizeYear:
    """Tests for normalize_year — covers all raw formats in Nifty100 data."""

    # ── "Month YYYY" formats ─────────────────────────────────────────────────

    def test_mar_yyyy(self):
        assert normalize_year("Mar 2023") == 2023

    def test_dec_yyyy(self):
        assert normalize_year("Dec 2012") == 2012

    def test_jun_yyyy(self):
        assert normalize_year("Jun 2019") == 2019

    def test_case_insensitive_month(self):
        assert normalize_year("MAR 2023") == 2023
        assert normalize_year("mar 2023") == 2023

    # ── "Month-YY" and "Month-YYYY" formats ──────────────────────────────────

    def test_mar_two_digit_year(self):
        assert normalize_year("Mar-13") == 2013

    def test_dec_two_digit_year(self):
        assert normalize_year("Dec-09") == 2009

    def test_mar_four_digit_year_hyphen(self):
        assert normalize_year("Mar-2014") == 2014

    def test_two_digit_year_century_prefix(self):
        """2-digit years should be interpreted as 20xx."""
        assert normalize_year("Mar-00") == 2000
        assert normalize_year("Mar-99") == 2099

    # ── Bare integer / string ─────────────────────────────────────────────────

    def test_integer_year(self):
        assert normalize_year(2024) == 2024

    def test_string_integer_year(self):
        assert normalize_year("2024") == 2024

    def test_float_year(self):
        assert normalize_year(2022.0) == 2022

    # ── Null / invalid inputs ─────────────────────────────────────────────────

    def test_none_returns_none(self):
        assert normalize_year(None) is None

    def test_nan_returns_none(self):
        assert normalize_year(float("nan")) is None

    def test_unrecognised_string_returns_none(self):
        assert normalize_year("N/A") is None
        assert normalize_year("FY24") is None
        assert normalize_year("invalid") is None

    def test_out_of_range_integer_returns_none(self):
        assert normalize_year(1800) is None
        assert normalize_year(2200) is None

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_boundary_years_valid(self):
        assert normalize_year(1900) == 1900
        assert normalize_year(2100) == 2100

    def test_year_with_extra_whitespace(self):
        assert normalize_year("  2023  ") == 2023


# =============================================================================
# strip_whitespace
# =============================================================================

class TestStripWhitespace:
    """Tests for strip_whitespace."""

    def test_strips_string_columns(self):
        df = pd.DataFrame({"name": ["  HDFC  ", " TCS", "Reliance "]})
        result = strip_whitespace(df)
        assert list(result["name"]) == ["HDFC", "TCS", "Reliance"]

    def test_numeric_columns_unchanged(self):
        df = pd.DataFrame({"value": [1.0, 2.5, 3.0]})
        result = strip_whitespace(df)
        assert list(result["value"]) == [1.0, 2.5, 3.0]

    def test_does_not_mutate_original(self):
        df = pd.DataFrame({"name": ["  ABC  "]})
        _ = strip_whitespace(df)
        assert df["name"].iloc[0] == "  ABC  "

    def test_none_values_preserved(self):
        df = pd.DataFrame({"name": ["  HDFC  ", None]})
        result = strip_whitespace(df)
        assert result["name"].iloc[0] == "HDFC"
        assert pd.isna(result["name"].iloc[1])  # pandas stores None as NaN

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = strip_whitespace(df)
        assert result.empty


# =============================================================================
# normalize_dataframe (integration)
# =============================================================================

class TestNormalizeDataframe:
    """Integration tests for the full normalize_dataframe pipeline."""

    def _make_raw_df(self) -> pd.DataFrame:
        return pd.DataFrame({
            "Company ID": ["  hdfcbank  ", "  tcs  "],
            "Year": ["Mar 2023", "Dec 2019"],
            "Net Profit %": [22.5, 18.0],
            "Sales": [10000, 9000],
        })

    def test_column_names_normalised(self):
        df = normalize_dataframe(self._make_raw_df())
        assert "company_id" in df.columns
        assert "year" in df.columns
        assert "net_profit_pct" in df.columns
        assert "sales" in df.columns

    def test_ticker_normalised(self):
        df = normalize_dataframe(self._make_raw_df())
        assert df["company_id"].tolist() == ["HDFCBANK", "TCS"]

    def test_year_normalised(self):
        df = normalize_dataframe(self._make_raw_df())
        assert df["year"].tolist() == [2023, 2019]

    def test_whitespace_stripped(self):
        df = normalize_dataframe(self._make_raw_df())
        for val in df["company_id"]:
            assert val == val.strip()

    def test_does_not_mutate_input(self):
        raw = self._make_raw_df()
        original_cols = list(raw.columns)
        _ = normalize_dataframe(raw)
        assert list(raw.columns) == original_cols

    def test_no_year_column_no_crash(self):
        df = pd.DataFrame({"company_id": ["INFY"], "revenue": [50000]})
        result = normalize_dataframe(df)
        assert "year" not in result.columns
        assert "company_id" in result.columns

    def test_empty_dataframe_no_crash(self):
        df = pd.DataFrame()
        result = normalize_dataframe(df)
        assert result.empty
