"""
normalizer.py
=============
Nifty100 Financial Intelligence Platform — Sprint 1, Day 2
Bluestock Fintech

Provides pure, stateless normalization functions for cleaning raw financial
data loaded from Excel. All functions are designed to be composable and
safe: they never raise on bad input, preferring to return the value
unchanged (with a warning) rather than crash.

Functions
---------
normalize_column_names(columns)   → List[str]
normalize_ticker(value)           → str
normalize_year(value)             → Optional[int]
strip_whitespace(df)              → pd.DataFrame
normalize_dataframe(df)           → pd.DataFrame
"""

from __future__ import annotations

import logging
import re
from typing import Any, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column name normalisation
# ---------------------------------------------------------------------------

# Characters that should be replaced with underscores
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_column_names(columns: List[Any]) -> List[str]:
    """Convert an iterable of column labels to snake_case strings.

    Rules applied in order:
    1. Cast to ``str`` and strip surrounding whitespace.
    2. Lower-case everything.
    3. Replace any run of non-alphanumeric characters with a single ``_``.
    4. Strip leading / trailing underscores.
    5. Replace blank names (after sanitisation) with ``unnamed_<index>``.

    Parameters
    ----------
    columns:
        Any iterable of column labels (strings, ints, floats, NaN, …).

    Returns
    -------
    List[str]
        A list of normalised snake_case column name strings, one per input.

    Examples
    --------
    >>> normalize_column_names(["Company ID", "Net Profit %", "OPM%"])
    ['company_id', 'net_profit_pct', 'opm_pct']  # NB: % → pct handled below
    """
    result: List[str] = []
    seen: dict[str, int] = {}

    for i, col in enumerate(columns):
        raw = str(col).strip() if pd.notna(col) else ""

        # Replace % with _pct before general sanitisation
        raw = raw.replace("%", "_pct")

        # Lower-case
        normalised = raw.lower()

        # Collapse non-alphanumeric runs → single underscore
        normalised = _NON_ALNUM_RE.sub("_", normalised)

        # Strip edge underscores
        normalised = normalised.strip("_")

        # Fallback for empty names
        if not normalised:
            normalised = f"unnamed_{i}"

        # De-duplicate by suffixing with counter
        if normalised in seen:
            seen[normalised] += 1
            normalised = f"{normalised}_{seen[normalised]}"
        else:
            seen[normalised] = 0

        result.append(normalised)

    return result


# ---------------------------------------------------------------------------
# Ticker normalisation
# ---------------------------------------------------------------------------

def normalize_ticker(value: Any) -> str:
    """Normalise a stock ticker symbol to uppercase with whitespace stripped.

    Parameters
    ----------
    value:
        Raw ticker value. May be a string, number, or NaN.

    Returns
    -------
    str
        Uppercase ticker string, or an empty string when the input is null /
        not representable as a non-empty string.

    Examples
    --------
    >>> normalize_ticker("  hdfcbank ")
    'HDFCBANK'
    >>> normalize_ticker("infy")
    'INFY'
    >>> normalize_ticker(None)
    ''
    """
    if pd.isna(value) if not isinstance(value, str) else False:
        return ""
    ticker = str(value).strip().upper()
    return ticker


# ---------------------------------------------------------------------------
# Year normalisation
# ---------------------------------------------------------------------------

# Patterns for the various year formats found in the raw data:
#   "Mar 2023", "Dec 2012", "Mar-13", "Mar-2014", "2023", 2023 (int)
_YEAR_MONTH_FULL_RE = re.compile(
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})",
    re.IGNORECASE,
)
_YEAR_MONTH_SHORT_RE = re.compile(
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{2,4})",
    re.IGNORECASE,
)
_BARE_YEAR_RE = re.compile(r"^\s*(\d{4})\s*$")


def normalize_year(value: Any) -> Optional[int]:
    """Parse a raw year field into a 4-digit integer (YYYY).

    Handles the following formats observed in Nifty100 raw data:
    - ``"Mar 2023"``  → 2023
    - ``"Dec 2012"``  → 2012
    - ``"Mar-13"``    → 2013   (2-digit year interpreted as 2000+)
    - ``"Mar-2014"``  → 2014
    - ``2023``        → 2023   (bare integer)
    - ``"2023"``      → 2023   (bare string)

    Parameters
    ----------
    value:
        Raw year value from the Excel sheet.

    Returns
    -------
    Optional[int]
        4-digit year as an integer, or ``None`` if the value cannot be parsed.

    Examples
    --------
    >>> normalize_year("Mar 2023")
    2023
    >>> normalize_year("Mar-13")
    2013
    >>> normalize_year(2024)
    2024
    >>> normalize_year("N/A")
    None
    """
    if value is None:
        return None

    # Numeric types (int, float)
    if isinstance(value, (int, float)):
        if pd.isna(value):
            return None
        year_int = int(value)
        if 1900 <= year_int <= 2100:
            return year_int
        logger.warning("normalize_year: out-of-range numeric year %s", value)
        return None

    text = str(value).strip()

    # "Mar 2023" / "Dec 2012" style
    m = _YEAR_MONTH_FULL_RE.search(text)
    if m:
        return int(m.group(1))

    # "Mar-13" / "Mar-2014" style
    m = _YEAR_MONTH_SHORT_RE.search(text)
    if m:
        year_part = m.group(1)
        year_int = int(year_part)
        if year_int < 100:
            year_int += 2000
        return year_int

    # Bare 4-digit year string
    m = _BARE_YEAR_RE.match(text)
    if m:
        return int(m.group(1))

    logger.warning("normalize_year: unrecognised year format %r", value)
    return None


# ---------------------------------------------------------------------------
# Whitespace stripping
# ---------------------------------------------------------------------------

def strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Strip leading/trailing whitespace from all string-valued cells.

    Only ``object`` and ``StringDtype`` columns are processed; numeric and
    datetime columns are left untouched.

    Parameters
    ----------
    df:
        Input DataFrame. The original is never modified.

    Returns
    -------
    pd.DataFrame
        A copy of ``df`` with string cells stripped.
    """
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].apply(
                lambda v: v.strip() if isinstance(v, str) else v
            )
    return df


# ---------------------------------------------------------------------------
# Full DataFrame normalisation pipeline
# ---------------------------------------------------------------------------

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the full normalisation pipeline to a raw DataFrame.

    Steps (in order):
    1. Strip whitespace from all string cells.
    2. Normalise column names to snake_case.
    3. Normalise ``company_id`` / ``ticker`` columns to uppercase.
    4. Normalise ``year`` column to integer YYYY (where present).

    Parameters
    ----------
    df:
        Raw DataFrame as loaded from Excel (with real headers already set).

    Returns
    -------
    pd.DataFrame
        Normalised copy of the input DataFrame.
    """
    df = strip_whitespace(df)

    # Normalise column names
    df.columns = normalize_column_names(list(df.columns))

    # Ticker / company_id columns → uppercase
    ticker_cols = [c for c in df.columns if c in {"company_id", "ticker", "symbol"}]
    for col in ticker_cols:
        df[col] = df[col].apply(normalize_ticker)
        logger.debug("Normalised ticker column: %s", col)

    # Year column → integer YYYY
    if "year" in df.columns:
        original_year = df["year"].copy()
        df["year"] = df["year"].apply(normalize_year)
        failed_mask = df["year"].isna() & original_year.notna()
        if failed_mask.any():
            bad_vals = original_year[failed_mask].unique().tolist()
            logger.warning(
                "normalize_dataframe: %d year values could not be parsed: %s",
                failed_mask.sum(),
                bad_vals[:10],
            )

    return df
