"""
validator.py
============
Nifty100 Financial Intelligence Platform — Sprint 1, Day 3
Bluestock Fintech

Data Quality Validation Framework — 16 DQ Rules.

All rules read from ``data/processed/`` CSVs produced by the Day 2 loader
and emit structured failure records.  Results are written to:
  - ``output/validation_failures.csv``
  - ``output/dq_summary.csv``

DQ Rule Registry
----------------
DQ-01  Primary Key Uniqueness           (id column per dataset)
DQ-02  Composite Key Uniqueness         (company_id + year)
DQ-03  Foreign Key Integrity            (company_id refs against companies)
DQ-04  Balance Sheet Equation           (total_assets == total_liabilities)
DQ-05  OPM Cross-Check                  (operating_profit / sales ≈ opm_pct)
DQ-06  Positive Sales                   (sales > 0)
DQ-07  Missing Company IDs             (null / empty company_id)
DQ-08  Missing Ticker Symbols           (alias for DQ-07 on companies table)
DQ-09  Duplicate Records               (exact row duplicates)
DQ-10  Year Range Validation            (1990 ≤ year ≤ 2030, TTM exempt)
DQ-11  Positive Market Cap             (market_cap_crore > 0)
DQ-12  Positive Stock Price            (OHLC prices > 0)
DQ-13  Financial Ratio Range Checks    (pe_ratio, pb_ratio, roe bounds)
DQ-14  Sector Mapping Validation       (every company has a sector entry)
DQ-15  Peer Group Mapping Validation   (every company appears in peer_groups)
DQ-16  Critical Null Field Validation  (key numeric fields not null)
"""

from __future__ import annotations

import csv
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# ---------------------------------------------------------------------------
# Module logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROCESSED_DIR = Path("data/processed")
OUTPUT_DIR = Path("output")

FAILURES_CSV = OUTPUT_DIR / "validation_failures.csv"
SUMMARY_CSV = OUTPUT_DIR / "dq_summary.csv"

FAILURES_COLUMNS = [
    "dq_rule",
    "severity",
    "dataset",
    "row_identifier",
    "issue_description",
]

SUMMARY_COLUMNS = [
    "dq_rule",
    "total_checked",
    "total_failed",
    "severity",
]

# Year bounds for DQ-10
YEAR_MIN = 1990
YEAR_MAX = 2030

# OPM tolerance for DQ-05 (percentage points)
OPM_TOLERANCE = 2.0

# Financial ratio caps for DQ-13
RATIO_BOUNDS: Dict[str, Tuple[float, float]] = {
    "pe_ratio": (-200.0, 2000.0),
    "pb_ratio": (-50.0, 500.0),
    "return_on_equity_pct": (-500.0, 500.0),
    "net_profit_margin_pct": (-200.0, 200.0),
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DQFailure:
    """A single data quality failure record."""
    dq_rule: str
    severity: str           # "CRITICAL" | "WARNING" | "INFO"
    dataset: str
    row_identifier: str
    issue_description: str

    def to_dict(self) -> dict:
        return {
            "dq_rule": self.dq_rule,
            "severity": self.severity,
            "dataset": self.dataset,
            "row_identifier": self.row_identifier,
            "issue_description": self.issue_description,
        }


@dataclass
class DQResult:
    """Aggregated result for a single DQ rule."""
    rule_id: str
    severity: str
    total_checked: int = 0
    failures: List[DQFailure] = field(default_factory=list)

    @property
    def total_failed(self) -> int:
        return len(self.failures)

    def to_summary_dict(self) -> dict:
        return {
            "dq_rule": self.rule_id,
            "total_checked": self.total_checked,
            "total_failed": self.total_failed,
            "severity": self.severity,
        }


# ---------------------------------------------------------------------------
# Dataset loader helpers
# ---------------------------------------------------------------------------

def _load_csv(filename: str, processed_dir: Path = PROCESSED_DIR) -> Optional[pd.DataFrame]:
    """Load a processed CSV.  Returns None if missing or empty."""
    path = processed_dir / filename
    if not path.exists():
        logger.warning("Dataset not found: %s", path)
        return None
    if path.stat().st_size == 0:
        logger.warning("Dataset is empty: %s", path)
        return None
    try:
        df = pd.read_csv(path, low_memory=False)
        logger.debug("Loaded %s: %d rows x %d cols", filename, len(df), len(df.columns))
        return df
    except Exception as exc:
        logger.error("Failed to load %s: %s", filename, exc)
        return None


def _load_all(processed_dir: Path = PROCESSED_DIR) -> Dict[str, pd.DataFrame]:
    """Load all processed CSVs into a named dict."""
    mapping = {
        "analysis":          "analysis__analysis.csv",
        "balancesheet":      "balancesheet__balance_sheet.csv",
        "cashflow":          "cashflow__cash_flow.csv",
        "companies":         "companies__companies.csv",
        "documents":         "documents__documents.csv",
        "financial_ratios":  "financial_ratios__sheet1.csv",
        "market_cap":        "market_cap__sheet1.csv",
        "peer_groups":       "peer_groups__sheet1.csv",
        "profitandloss":     "profitandloss__profit_and_loss.csv",
        "prosandcons":       "prosandcons__pros_and_cons.csv",
        "sectors":           "sectors__sheet1.csv",
        "stock_prices":      "stock_prices__sheet1.csv",
    }
    datasets: Dict[str, pd.DataFrame] = {}
    for key, fname in mapping.items():
        df = _load_csv(fname, processed_dir)
        if df is not None:
            datasets[key] = df
    return datasets


def _is_ttm(year_val) -> bool:
    """Return True when a year value represents a TTM (Trailing Twelve Months) entry."""
    if pd.isna(year_val):
        return False
    return str(year_val).strip().upper() == "TTM"


def _valid_company_ids(datasets: Dict[str, pd.DataFrame]) -> set:
    """Return the set of known company IDs from the companies master table."""
    companies = datasets.get("companies")
    if companies is None:
        return set()
    id_col = "id" if "id" in companies.columns else "company_id"
    return set(companies[id_col].dropna().astype(str).str.strip().str.upper())


# ---------------------------------------------------------------------------
# DQ Rule Implementations
# ---------------------------------------------------------------------------

def dq01_primary_key_uniqueness(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-01: id column must be unique within each dataset."""
    result = DQResult(rule_id="DQ-01", severity="CRITICAL")

    for name, df in datasets.items():
        if "id" not in df.columns:
            continue
        total = len(df)
        result.total_checked += total
        dupes = df[df.duplicated(subset=["id"], keep=False)]
        for _, row in dupes.iterrows():
            result.failures.append(DQFailure(
                dq_rule="DQ-01",
                severity="CRITICAL",
                dataset=name,
                row_identifier=str(row.get("id", "?")),
                issue_description=f"Duplicate primary key id={row['id']}",
            ))

    logger.info("DQ-01: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq02_composite_key_uniqueness(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-02: (company_id, year) composite key must be unique per dataset (TTM exempt)."""
    result = DQResult(rule_id="DQ-02", severity="CRITICAL")
    target_tables = ["balancesheet", "cashflow", "financial_ratios",
                     "market_cap", "profitandloss"]

    for name in target_tables:
        df = datasets.get(name)
        if df is None:
            continue
        if "company_id" not in df.columns or "year" not in df.columns:
            continue

        # Exclude TTM rows — stored as null after normalise_year() for TTM values
        mask_ttm = df["year"].apply(_is_ttm) | df["year"].isna()
        df_check = df[~mask_ttm].copy()

        result.total_checked += len(df_check)
        dupes = df_check[df_check.duplicated(subset=["company_id", "year"], keep=False)]
        for _, row in dupes.iterrows():
            result.failures.append(DQFailure(
                dq_rule="DQ-02",
                severity="CRITICAL",
                dataset=name,
                row_identifier=f"{row.get('company_id','?')}|{row.get('year','?')}",
                issue_description=(
                    f"Duplicate composite key (company_id={row.get('company_id','?')}, "
                    f"year={row.get('year','?')})"
                ),
            ))

    logger.info("DQ-02: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq03_foreign_key_integrity(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-03: company_id in child tables must exist in companies master."""
    result = DQResult(rule_id="DQ-03", severity="CRITICAL")
    valid_ids = _valid_company_ids(datasets)

    if not valid_ids:
        logger.warning("DQ-03: companies table missing — skipping FK check")
        return result

    skip_tables = {"companies"}  # parent table exempted
    for name, df in datasets.items():
        if name in skip_tables or "company_id" not in df.columns:
            continue

        result.total_checked += len(df)
        orphans = df[~df["company_id"].astype(str).str.strip().str.upper().isin(valid_ids)]
        for _, row in orphans.iterrows():
            result.failures.append(DQFailure(
                dq_rule="DQ-03",
                severity="CRITICAL",
                dataset=name,
                row_identifier=str(row.get("id", row.get("company_id", "?"))),
                issue_description=(
                    f"company_id '{row.get('company_id','?')}' not found in companies master"
                ),
            ))

    logger.info("DQ-03: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq04_balance_sheet_equation(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-04: total_assets must equal total_liabilities (±1 rounding tolerance)."""
    result = DQResult(rule_id="DQ-04", severity="CRITICAL")
    df = datasets.get("balancesheet")
    if df is None:
        return result

    needed = ["total_assets", "total_liabilities"]
    if not all(c in df.columns for c in needed):
        logger.warning("DQ-04: required columns missing from balancesheet")
        return result

    df_clean = df.dropna(subset=needed)
    result.total_checked = len(df_clean)
    diff = (df_clean["total_assets"] - df_clean["total_liabilities"]).abs()
    failures = df_clean[diff > 1]

    for _, row in failures.iterrows():
        result.failures.append(DQFailure(
            dq_rule="DQ-04",
            severity="CRITICAL",
            dataset="balancesheet",
            row_identifier=f"{row.get('company_id','?')}|{row.get('year','?')}",
            issue_description=(
                f"Balance sheet imbalance: assets={row['total_assets']}, "
                f"liabilities={row['total_liabilities']}, "
                f"diff={row['total_assets']-row['total_liabilities']:.2f}"
            ),
        ))

    logger.info("DQ-04: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq05_opm_cross_check(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-05: operating_profit / sales must approximately equal opm_percentage (±2 ppt)."""
    result = DQResult(rule_id="DQ-05", severity="WARNING")
    df = datasets.get("profitandloss")
    if df is None:
        return result

    needed = ["sales", "operating_profit", "opm_percentage"]
    if not all(c in df.columns for c in needed):
        logger.warning("DQ-05: required columns missing from profitandloss")
        return result

    df_clean = df.dropna(subset=needed).copy()
    df_nonzero = df_clean[df_clean["sales"] != 0]
    result.total_checked = len(df_nonzero)

    calc_opm = (df_nonzero["operating_profit"] / df_nonzero["sales"] * 100).round(1)
    diff = (calc_opm - df_nonzero["opm_percentage"]).abs()
    failures = df_nonzero[diff > OPM_TOLERANCE]

    for _, row in failures.iterrows():
        calc = round(row["operating_profit"] / row["sales"] * 100, 2)
        result.failures.append(DQFailure(
            dq_rule="DQ-05",
            severity="WARNING",
            dataset="profitandloss",
            row_identifier=f"{row.get('company_id','?')}|{row.get('year','?')}",
            issue_description=(
                f"OPM mismatch: calculated={calc}%, stated={row['opm_percentage']}%, "
                f"diff={abs(calc-row['opm_percentage']):.2f}ppt"
            ),
        ))

    logger.info("DQ-05: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq06_positive_sales(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-06: sales must be > 0 (negative or zero is suspect)."""
    result = DQResult(rule_id="DQ-06", severity="WARNING")
    df = datasets.get("profitandloss")
    if df is None or "sales" not in (df.columns if df is not None else []):
        return result

    df_clean = df.dropna(subset=["sales"])
    result.total_checked = len(df_clean)
    failures = df_clean[df_clean["sales"] <= 0]

    for _, row in failures.iterrows():
        result.failures.append(DQFailure(
            dq_rule="DQ-06",
            severity="WARNING",
            dataset="profitandloss",
            row_identifier=f"{row.get('company_id','?')}|{row.get('year','?')}",
            issue_description=f"Non-positive sales value: {row['sales']}",
        ))

    logger.info("DQ-06: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq07_missing_company_ids(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-07: company_id must not be null or empty in any dataset."""
    result = DQResult(rule_id="DQ-07", severity="CRITICAL")

    for name, df in datasets.items():
        if "company_id" not in df.columns:
            continue
        result.total_checked += len(df)
        missing = df[df["company_id"].isna() | (df["company_id"].astype(str).str.strip() == "")]
        for _, row in missing.iterrows():
            result.failures.append(DQFailure(
                dq_rule="DQ-07",
                severity="CRITICAL",
                dataset=name,
                row_identifier=str(row.get("id", "?")),
                issue_description="Null or empty company_id",
            ))

    logger.info("DQ-07: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq08_missing_ticker_symbols(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-08: companies master — id (ticker) must not be null or empty."""
    result = DQResult(rule_id="DQ-08", severity="CRITICAL")
    df = datasets.get("companies")
    if df is None:
        return result

    id_col = "id"
    if id_col not in df.columns:
        return result

    result.total_checked = len(df)
    missing = df[df[id_col].isna() | (df[id_col].astype(str).str.strip() == "")]
    for _, row in missing.iterrows():
        result.failures.append(DQFailure(
            dq_rule="DQ-08",
            severity="CRITICAL",
            dataset="companies",
            row_identifier=str(row.get("company_name", "?")),
            issue_description="Missing ticker symbol (id column null/empty)",
        ))

    logger.info("DQ-08: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq09_duplicate_records(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-09: no exact duplicate rows (all columns identical) in any dataset."""
    result = DQResult(rule_id="DQ-09", severity="WARNING")

    for name, df in datasets.items():
        result.total_checked += len(df)
        dupes = df[df.duplicated(keep=False)]
        if not dupes.empty:
            # Report unique duplicate groups, not every row
            groups = dupes.groupby(list(df.columns), dropna=False).size().reset_index(name="count")
            for _, row in groups.iterrows():
                result.failures.append(DQFailure(
                    dq_rule="DQ-09",
                    severity="WARNING",
                    dataset=name,
                    row_identifier=str(row.get("id", "multiple")),
                    issue_description=f"Exact duplicate row found ({row['count']}x)",
                ))

    logger.info("DQ-09: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq10_year_range_validation(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-10: year must be between YEAR_MIN and YEAR_MAX.  TTM rows are exempt."""
    result = DQResult(rule_id="DQ-10", severity="WARNING")
    target_tables = ["balancesheet", "cashflow", "financial_ratios",
                     "market_cap", "profitandloss", "documents"]

    for name in target_tables:
        df = datasets.get(name)
        if df is None or "year" not in df.columns:
            continue

        # Exclude TTM rows — they are valid rolling-period records
        mask_not_ttm = ~df["year"].apply(_is_ttm)
        df_check = df[mask_not_ttm].copy()
        df_check = df_check.dropna(subset=["year"])
        result.total_checked += len(df_check)

        try:
            years = pd.to_numeric(df_check["year"], errors="coerce")
        except Exception:
            years = df_check["year"]

        out_of_range = df_check[(years < YEAR_MIN) | (years > YEAR_MAX)]
        for _, row in out_of_range.iterrows():
            result.failures.append(DQFailure(
                dq_rule="DQ-10",
                severity="WARNING",
                dataset=name,
                row_identifier=f"{row.get('company_id','?')}|{row.get('year','?')}",
                issue_description=(
                    f"Year {row.get('year','?')} outside valid range "
                    f"[{YEAR_MIN}, {YEAR_MAX}]"
                ),
            ))

    logger.info("DQ-10: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq11_positive_market_cap(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-11: market_cap_crore must be > 0."""
    result = DQResult(rule_id="DQ-11", severity="CRITICAL")
    df = datasets.get("market_cap")
    if df is None or "market_cap_crore" not in df.columns:
        return result

    df_clean = df.dropna(subset=["market_cap_crore"])
    result.total_checked = len(df_clean)
    failures = df_clean[df_clean["market_cap_crore"] <= 0]

    for _, row in failures.iterrows():
        result.failures.append(DQFailure(
            dq_rule="DQ-11",
            severity="CRITICAL",
            dataset="market_cap",
            row_identifier=f"{row.get('company_id','?')}|{row.get('year','?')}",
            issue_description=f"Non-positive market cap: {row['market_cap_crore']} Cr",
        ))

    logger.info("DQ-11: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq12_positive_stock_prices(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-12: open, high, low, close, adjusted_close prices must all be > 0."""
    result = DQResult(rule_id="DQ-12", severity="CRITICAL")
    df = datasets.get("stock_prices")
    if df is None:
        return result

    price_cols = ["open_price", "high_price", "low_price", "close_price", "adjusted_close"]
    available = [c for c in price_cols if c in df.columns]
    result.total_checked = len(df)

    for col in available:
        df_clean = df.dropna(subset=[col])
        bad = df_clean[df_clean[col] <= 0]
        for _, row in bad.iterrows():
            result.failures.append(DQFailure(
                dq_rule="DQ-12",
                severity="CRITICAL",
                dataset="stock_prices",
                row_identifier=f"{row.get('company_id','?')}|{row.get('date','?')}",
                issue_description=f"Non-positive {col}: {row[col]}",
            ))

    logger.info("DQ-12: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq13_financial_ratio_range_checks(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-13: key financial ratios must fall within plausible bounds."""
    result = DQResult(rule_id="DQ-13", severity="WARNING")

    checks = [
        ("market_cap",       ["pe_ratio", "pb_ratio"]),
        ("financial_ratios", ["return_on_equity_pct", "net_profit_margin_pct"]),
    ]

    for table_name, cols in checks:
        df = datasets.get(table_name)
        if df is None:
            continue
        for col in cols:
            if col not in df.columns:
                continue
            lo, hi = RATIO_BOUNDS.get(col, (-1e9, 1e9))
            df_clean = df.dropna(subset=[col])
            result.total_checked += len(df_clean)
            bad = df_clean[(df_clean[col] < lo) | (df_clean[col] > hi)]
            for _, row in bad.iterrows():
                result.failures.append(DQFailure(
                    dq_rule="DQ-13",
                    severity="WARNING",
                    dataset=table_name,
                    row_identifier=f"{row.get('company_id','?')}|{row.get('year','?')}",
                    issue_description=(
                        f"{col}={row[col]:.2f} outside plausible range [{lo}, {hi}]"
                    ),
                ))

    logger.info("DQ-13: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq14_sector_mapping_validation(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-14: every company in the master must have a sector mapping."""
    result = DQResult(rule_id="DQ-14", severity="WARNING")
    companies = datasets.get("companies")
    sectors = datasets.get("sectors")
    if companies is None or sectors is None:
        return result

    company_ids = set(companies["id"].astype(str).str.strip().str.upper())
    sector_ids = set(sectors["company_id"].astype(str).str.strip().str.upper())

    result.total_checked = len(company_ids)
    unmapped = company_ids - sector_ids

    for cid in sorted(unmapped):
        result.failures.append(DQFailure(
            dq_rule="DQ-14",
            severity="WARNING",
            dataset="sectors",
            row_identifier=cid,
            issue_description=f"Company '{cid}' has no sector mapping",
        ))

    logger.info("DQ-14: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq15_peer_group_mapping_validation(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-15: every company in the master must appear in at least one peer group."""
    result = DQResult(rule_id="DQ-15", severity="WARNING")
    companies = datasets.get("companies")
    peer_groups = datasets.get("peer_groups")
    if companies is None or peer_groups is None:
        return result

    company_ids = set(companies["id"].astype(str).str.strip().str.upper())
    peer_ids = set(peer_groups["company_id"].astype(str).str.strip().str.upper())

    result.total_checked = len(company_ids)
    unmapped = company_ids - peer_ids

    for cid in sorted(unmapped):
        result.failures.append(DQFailure(
            dq_rule="DQ-15",
            severity="WARNING",
            dataset="peer_groups",
            row_identifier=cid,
            issue_description=f"Company '{cid}' has no peer group mapping",
        ))

    logger.info("DQ-15: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


def dq16_critical_null_field_validation(datasets: Dict[str, pd.DataFrame]) -> DQResult:
    """DQ-16: critical numeric fields must not be null.

    TTM rows in profitandloss are exempt from the ``year`` null check.
    """
    result = DQResult(rule_id="DQ-16", severity="CRITICAL")

    # Map: (dataset_key, [critical_cols])
    critical_fields: List[Tuple[str, List[str]]] = [
        ("companies",        ["company_name"]),
        ("balancesheet",     ["total_assets", "total_liabilities", "equity_capital"]),
        ("profitandloss",    ["sales", "net_profit"]),
        ("financial_ratios", ["return_on_equity_pct"]),
        ("market_cap",       ["market_cap_crore"]),
        ("stock_prices",     ["close_price", "volume"]),
    ]

    for table_name, cols in critical_fields:
        df = datasets.get(table_name)
        if df is None:
            continue

        for col in cols:
            if col not in df.columns:
                continue

            df_check = df.copy()

            # TTM exemption: profitandloss rows with TTM year are not checked for year nulls
            # (year is already null after normalisation for TTM rows, handled in DQ-10)

            result.total_checked += len(df_check)
            nulls = df_check[df_check[col].isna()]

            for _, row in nulls.iterrows():
                result.failures.append(DQFailure(
                    dq_rule="DQ-16",
                    severity="CRITICAL",
                    dataset=table_name,
                    row_identifier=str(
                        row.get("company_id", row.get("id", "?"))
                    ),
                    issue_description=f"Critical field '{col}' is null",
                ))

    logger.info("DQ-16: checked=%d  failed=%d", result.total_checked, result.total_failed)
    return result


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_failures(failures: List[DQFailure], path: Path = FAILURES_CSV) -> None:
    """Write all DQ failure records to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FAILURES_COLUMNS)
        writer.writeheader()
        for f in failures:
            writer.writerow(f.to_dict())
    logger.info("Failures written -> %s (%d records)", path, len(failures))


def write_summary(results: List[DQResult], path: Path = SUMMARY_CSV) -> None:
    """Write DQ summary (one row per rule) to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        for r in results:
            writer.writerow(r.to_summary_dict())
    logger.info("Summary written -> %s (%d rules)", path, len(results))


# ---------------------------------------------------------------------------
# Main validation runner
# ---------------------------------------------------------------------------

def run_validation(
    processed_dir: Path = PROCESSED_DIR,
    failures_path: Path = FAILURES_CSV,
    summary_path: Path = SUMMARY_CSV,
) -> Tuple[List[DQResult], pd.DataFrame]:
    """Run all 16 DQ rules and emit output CSVs.

    Parameters
    ----------
    processed_dir:
        Directory containing normalised CSV files (output of Day 2 loader).
    failures_path:
        Destination for the detailed failures CSV.
    summary_path:
        Destination for the per-rule summary CSV.

    Returns
    -------
    Tuple[List[DQResult], pd.DataFrame]
        ``(results_list, failures_dataframe)``
    """
    logger.info("=" * 60)
    logger.info("Nifty100 DQ Validation — starting")
    logger.info("  processed_dir : %s", processed_dir)
    logger.info("=" * 60)

    datasets = _load_all(processed_dir)
    logger.info("Loaded %d datasets", len(datasets))

    # ── Run all rules ────────────────────────────────────────────────────────
    rules = [
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
    ]

    results: List[DQResult] = []
    all_failures: List[DQFailure] = []

    for rule_fn in rules:
        try:
            r = rule_fn(datasets)
            results.append(r)
            all_failures.extend(r.failures)
        except Exception as exc:
            logger.error("Rule %s raised an unexpected error: %s", rule_fn.__name__, exc)

    # ── Write output ─────────────────────────────────────────────────────────
    write_failures(all_failures, failures_path)
    write_summary(results, summary_path)

    # ── Log scorecard ────────────────────────────────────────────────────────
    critical = sum(1 for f in all_failures if f.severity == "CRITICAL")
    warnings = sum(1 for f in all_failures if f.severity == "WARNING")
    total_checked = sum(r.total_checked for r in results)

    logger.info("=" * 60)
    logger.info("DQ Validation complete.")
    logger.info("  Rules run      : %d", len(results))
    logger.info("  Total checked  : %d", total_checked)
    logger.info("  Total failures : %d", len(all_failures))
    logger.info("    CRITICAL     : %d", critical)
    logger.info("    WARNING      : %d", warnings)
    logger.info("=" * 60)

    failures_df = pd.DataFrame(
        [f.to_dict() for f in all_failures],
        columns=FAILURES_COLUMNS,
    ) if all_failures else pd.DataFrame(columns=FAILURES_COLUMNS)

    return results, failures_df


# ---------------------------------------------------------------------------
# CLI entry point   (python -m src.etl.validator  or  make validate)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    results, failures_df = run_validation()

    print("\nDQ Summary:")
    for r in results:
        status = "PASS" if r.total_failed == 0 else "FAIL"
        print(
            f"  {r.rule_id}  [{r.severity:8s}]  "
            f"checked={r.total_checked:5d}  failed={r.total_failed:4d}  {status}"
        )

    if not failures_df.empty:
        print(f"\nTop failures ({min(20, len(failures_df))}):")
        print(failures_df.head(20).to_string(index=False))
