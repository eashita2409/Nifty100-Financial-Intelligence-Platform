"""
loader.py
=========
Nifty100 Financial Intelligence Platform — Sprint 1, Day 2
Bluestock Fintech

Reusable Excel loading framework that:
  - Dynamically discovers all ``.xlsx`` files in a configurable raw-data
    directory (defaults to ``data/raw``).
  - Reads every sheet inside each workbook.
  - Detects and skips Bluestock-style banner rows (row 0 is a branding
    string; real headers live on row 1).
  - Applies the full normalisation pipeline from ``src.etl.normalizer``.
  - Writes cleaned DataFrames as CSV files to ``data/processed/``.
  - Emits a structured audit trail to ``output/load_audit.csv``.

Public API
----------
discover_excel_files(raw_dir)   → List[Path]
load_workbook(path)             → Dict[str, pd.DataFrame]   (raw, pre-norm)
load_and_normalize(path)        → Dict[str, pd.DataFrame]   (normalised)
run_pipeline(raw_dir, ...)      → pd.DataFrame              (audit log)
"""

from __future__ import annotations

import csv
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.etl.normalizer import normalize_dataframe

# ---------------------------------------------------------------------------
# Module-level logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_RAW_DIR = Path("data/raw")
DEFAULT_PROCESSED_DIR = Path("data/processed")
DEFAULT_AUDIT_PATH = Path("output/load_audit.csv")

# Files whose first row is a Bluestock Fintech branding banner (not a header).
# The real column headers live on row 1 (0-indexed) of these workbooks.
BANNER_FILES = {
    "analysis.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "companies.xlsx",
    "documents.xlsx",
    "profitandloss.xlsx",
    "prosandcons.xlsx",
}

# Audit CSV column order
AUDIT_COLUMNS = [
    "file_name",
    "sheet_name",
    "rows_loaded",
    "columns_loaded",
    "status",
    "timestamp",
]


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def discover_excel_files(raw_dir: Path | str = DEFAULT_RAW_DIR) -> List[Path]:
    """Return a sorted list of ``.xlsx`` files in *raw_dir*.

    Files whose names contain ``- Copy`` (case-insensitive) are excluded to
    prevent accidental ingestion of duplicate artefacts.

    Parameters
    ----------
    raw_dir:
        Directory to search. Defaults to ``data/raw``.

    Returns
    -------
    List[Path]
        Sorted list of discovered ``.xlsx`` paths.

    Raises
    ------
    FileNotFoundError
        When *raw_dir* does not exist.
    """
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    files = sorted(
        p
        for p in raw_dir.glob("*.xlsx")
        if "- copy" not in p.name.lower()
    )
    logger.info("Discovered %d Excel file(s) in %s", len(files), raw_dir)
    for f in files:
        logger.debug("  Found: %s", f.name)
    return files


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _has_banner_row(file_name: str) -> bool:
    """Return True if the workbook uses a Bluestock banner on row 0."""
    return file_name.lower() in {f.lower() for f in BANNER_FILES}


def _read_sheet_raw(
    path: Path,
    sheet_name: str,
    has_banner: bool,
) -> Tuple[pd.DataFrame, str]:
    """Read a single sheet from *path*.

    Parameters
    ----------
    path:
        Full path to the ``.xlsx`` file.
    sheet_name:
        Sheet to load.
    has_banner:
        When ``True``, skip row 0 (branding) and use row 1 as header.

    Returns
    -------
    Tuple[pd.DataFrame, str]
        ``(dataframe, status)`` where *status* is ``"OK"`` or an error message.
    """
    try:
        header_row = 1 if has_banner else 0
        df = pd.read_excel(
            path,
            sheet_name=sheet_name,
            header=header_row,
            engine="openpyxl",
        )
        # Drop fully-blank rows that sneak in from Excel formatting
        df = df.dropna(how="all").reset_index(drop=True)
        return df, "OK"
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to read %s/%s: %s", path.name, sheet_name, exc)
        return pd.DataFrame(), f"ERROR: {exc}"


# ---------------------------------------------------------------------------
# Public loader functions
# ---------------------------------------------------------------------------

def load_workbook(path: Path | str) -> Dict[str, pd.DataFrame]:
    """Load all sheets from *path* into a dict of raw DataFrames.

    No normalisation is applied. Missing / unreadable sheets are skipped
    gracefully and logged as warnings.

    Parameters
    ----------
    path:
        Path to the ``.xlsx`` file.

    Returns
    -------
    Dict[str, pd.DataFrame]
        ``{sheet_name: dataframe}`` mapping. Empty dict if the file cannot
        be opened at all.
    """
    path = Path(path)
    if not path.exists():
        logger.warning("File not found, skipping: %s", path)
        return {}

    has_banner = _has_banner_row(path.name)

    try:
        xl = pd.ExcelFile(path, engine="openpyxl")
        sheet_names: List[str] = xl.sheet_names
    except Exception as exc:  # noqa: BLE001
        logger.error("Cannot open workbook %s: %s", path.name, exc)
        return {}

    result: Dict[str, pd.DataFrame] = {}
    for sheet in sheet_names:
        logger.info("Loading  %s / %s", path.name, sheet)
        df, status = _read_sheet_raw(path, sheet, has_banner)
        if status == "OK":
            logger.info(
                "  -> %d rows x %d cols", len(df), len(df.columns)
            )
            result[sheet] = df
        else:
            logger.warning("  -> SKIPPED (%s)", status)

    return result


def load_and_normalize(path: Path | str) -> Dict[str, pd.DataFrame]:
    """Load all sheets from *path* and apply the normalisation pipeline.

    Parameters
    ----------
    path:
        Path to the ``.xlsx`` file.

    Returns
    -------
    Dict[str, pd.DataFrame]
        ``{sheet_name: normalised_dataframe}`` mapping.
    """
    path = Path(path)
    raw_sheets = load_workbook(path)
    normalised: Dict[str, pd.DataFrame] = {}

    for sheet_name, df in raw_sheets.items():
        logger.info("Normalising %s / %s", path.name, sheet_name)
        try:
            normalised[sheet_name] = normalize_dataframe(df)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Normalisation failed for %s / %s: %s",
                path.name, sheet_name, exc,
            )
            normalised[sheet_name] = df  # keep raw if normalisation fails

    return normalised


# ---------------------------------------------------------------------------
# Processed-file writer
# ---------------------------------------------------------------------------

def _stem_for_sheet(file_stem: str, sheet_name: str) -> str:
    """Build a safe filename stem combining workbook stem and sheet name."""
    safe_sheet = sheet_name.lower().replace(" ", "_").replace("&", "and")
    # If the workbook has only one sheet, omit the sheet name to keep it tidy
    return f"{file_stem}__{safe_sheet}"


def save_processed(
    df: pd.DataFrame,
    file_stem: str,
    sheet_name: str,
    processed_dir: Path,
) -> Path:
    """Persist a normalised DataFrame as a CSV in *processed_dir*.

    Parameters
    ----------
    df:
        Normalised DataFrame to save.
    file_stem:
        Base name of the source ``.xlsx`` file (without extension).
    sheet_name:
        Sheet name used to build the output filename.
    processed_dir:
        Target directory.

    Returns
    -------
    Path
        Full path to the written CSV file.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    stem = _stem_for_sheet(file_stem, sheet_name)
    out_path = processed_dir / f"{stem}.csv"
    df.to_csv(out_path, index=False, encoding="utf-8")
    logger.info("Saved -> %s (%d rows)", out_path.name, len(df))
    return out_path


# ---------------------------------------------------------------------------
# Audit log helpers
# ---------------------------------------------------------------------------

def _audit_record(
    file_name: str,
    sheet_name: str,
    df: Optional[pd.DataFrame],
    status: str,
) -> dict:
    """Build a single audit row dict."""
    rows = len(df) if df is not None and not df.empty else 0
    cols = len(df.columns) if df is not None and not df.empty else 0
    return {
        "file_name": file_name,
        "sheet_name": sheet_name,
        "rows_loaded": rows,
        "columns_loaded": cols,
        "status": status,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _write_audit(records: List[dict], audit_path: Path) -> None:
    """Write the audit log to a CSV file."""
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=AUDIT_COLUMNS)
        writer.writeheader()
        writer.writerows(records)
    logger.info("Audit log written -> %s (%d records)", audit_path, len(records))


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    raw_dir: Path | str = DEFAULT_RAW_DIR,
    processed_dir: Path | str = DEFAULT_PROCESSED_DIR,
    audit_path: Path | str = DEFAULT_AUDIT_PATH,
    expected_files: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Run the full ingest → normalise → save pipeline for all Excel files.

    1. Discovers ``.xlsx`` files in *raw_dir*.
    2. For each file, loads and normalises every sheet.
    3. Saves each sheet as a CSV to *processed_dir*.
    4. Writes an audit log to *audit_path*.
    5. Logs a warning for any *expected_files* that were not found.

    Parameters
    ----------
    raw_dir:
        Source directory containing raw ``.xlsx`` files.
    processed_dir:
        Destination directory for normalised CSV files.
    audit_path:
        Path for the audit CSV.
    expected_files:
        Optional list of filenames that must be present (e.g. the 12 Nifty100
        datasets). Missing files are logged as warnings.

    Returns
    -------
    pd.DataFrame
        Audit log as a DataFrame (mirrors what was written to *audit_path*).
    """
    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)
    audit_path = Path(audit_path)

    logger.info("=" * 60)
    logger.info("Nifty100 ETL Pipeline — starting")
    logger.info("  raw_dir      : %s", raw_dir)
    logger.info("  processed_dir: %s", processed_dir)
    logger.info("  audit_path   : %s", audit_path)
    logger.info("=" * 60)

    # ── 1. File discovery ────────────────────────────────────────────────────
    try:
        found_files = discover_excel_files(raw_dir)
    except FileNotFoundError as exc:
        logger.critical("%s", exc)
        return pd.DataFrame(columns=AUDIT_COLUMNS)

    found_names = {f.name for f in found_files}

    # Warn for expected files that are missing
    if expected_files:
        for fname in expected_files:
            if fname not in found_names:
                logger.warning("Expected file not found in raw_dir: %s", fname)

    audit_records: List[dict] = []
    total_rows = 0

    # ── 2. Per-file processing ───────────────────────────────────────────────
    for file_path in found_files:
        fname = file_path.name
        logger.info("Processing: %s", fname)

        # Load + normalise
        try:
            normalised_sheets = load_and_normalize(file_path)
        except Exception as exc:  # noqa: BLE001
            logger.error("Unrecoverable error processing %s: %s", fname, exc)
            audit_records.append(
                _audit_record(fname, "—", None, f"ERROR: {exc}")
            )
            continue

        if not normalised_sheets:
            # File opened but yielded no usable sheets
            audit_records.append(_audit_record(fname, "—", None, "NO_SHEETS"))
            continue

        for sheet_name, df in normalised_sheets.items():
            # ── 3. Save processed CSV ──────────────────────────────────────
            try:
                save_processed(
                    df,
                    file_stem=file_path.stem,
                    sheet_name=sheet_name,
                    processed_dir=processed_dir,
                )
                status = "OK"
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Save failed for %s / %s: %s", fname, sheet_name, exc
                )
                status = f"SAVE_ERROR: {exc}"

            audit_records.append(_audit_record(fname, sheet_name, df, status))
            total_rows += len(df)

    # ── 4. Write audit log ───────────────────────────────────────────────────
    _write_audit(audit_records, audit_path)

    logger.info("=" * 60)
    logger.info("Pipeline complete.")
    logger.info("  Files processed : %d", len(found_files))
    logger.info("  Sheets processed: %d", len(audit_records))
    logger.info("  Total rows      : %d", total_rows)
    logger.info("=" * 60)

    return pd.DataFrame(audit_records, columns=AUDIT_COLUMNS)


# ---------------------------------------------------------------------------
# CLI entry point  (python -m src.etl.loader  or  make load)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    EXPECTED = [
        "analysis.xlsx",
        "balancesheet.xlsx",
        "cashflow.xlsx",
        "companies.xlsx",
        "documents.xlsx",
        "financial_ratios.xlsx",
        "market_cap.xlsx",
        "peer_groups.xlsx",
        "profitandloss.xlsx",
        "prosandcons.xlsx",
        "sectors.xlsx",
        "stock_prices.xlsx",
    ]

    audit_df = run_pipeline(expected_files=EXPECTED)
    print(audit_df.to_string(index=False))
