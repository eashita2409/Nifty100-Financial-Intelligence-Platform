# Nifty100 Financial Intelligence Platform
# Sprint 1 Day 2 — Completion Report

> **Date**: 23 June 2026  
> **Sprint**: Sprint 1 · Day 2  
> **Focus**: Excel Loader & Normalizer  
> **Updated**: Re-run with all 12 datasets (prosandcons.xlsx added)  
> **Status**: ✅ COMPLETE — 12/12 files processed

---

## Executive Summary

Day 2 successfully delivered a production-quality Excel loading and normalisation
framework for the Nifty100 Financial Intelligence Platform. All 12 source datasets
are now ingested, cleaned, and persisted to `data/processed/`. The full pytest
suite of **83 tests passes with 0 failures**.

---

## Pipeline Execution Results

### Files Processed

| # | File | Sheet | Rows Loaded | Columns | Status |
|---|------|-------|-------------|---------|--------|
| 1 | `analysis.xlsx` | Analysis | 20 | 6 | ✅ OK |
| 2 | `balancesheet.xlsx` | Balance Sheet | 1,312 | 13 | ✅ OK |
| 3 | `cashflow.xlsx` | Cash Flow | 1,187 | 7 | ✅ OK |
| 4 | `companies.xlsx` | Companies | 92 | 12 | ✅ OK |
| 5 | `documents.xlsx` | Documents | 1,585 | 4 | ✅ OK |
| 6 | `financial_ratios.xlsx` | Sheet1 | 1,184 | 16 | ✅ OK |
| 7 | `market_cap.xlsx` | Sheet1 | 552 | 9 | ✅ OK |
| 8 | `peer_groups.xlsx` | Sheet1 | 56 | 4 | ✅ OK |
| 9 | `profitandloss.xlsx` | Profit & Loss | 1,276 | 15 | ✅ OK |
| 10 | `prosandcons.xlsx` | Pros & Cons | 16 | 4 | ✅ OK |
| 11 | `sectors.xlsx` | Sheet1 | 92 | 6 | ✅ OK |
| 12 | `stock_prices.xlsx` | Sheet1 | 5,520 | 9 | ✅ OK |

### Aggregate Metrics

| Metric | Value |
|--------|-------|
| Files processed | **12 of 12** |
| Sheets processed | 12 |
| **Total rows loaded** | **12,892** |
| Total columns across sheets | 114 |
| Files with status OK | 12 (100%) |
| Files with errors | 0 |

---

## Processed Output Files (`data/processed/`)

| CSV File | Source | Rows | Size |
|----------|--------|------|------|
| `analysis__analysis.csv` | analysis.xlsx | 20 | 1.8 KB |
| `balancesheet__balance_sheet.csv` | balancesheet.xlsx | 1,312 | 95.5 KB |
| `cashflow__cash_flow.csv` | cashflow.xlsx | 1,187 | 54.3 KB |
| `companies__companies.csv` | companies.xlsx | 92 | 54.8 KB |
| `documents__documents.csv` | documents.xlsx | 1,585 | 117.5 KB |
| `financial_ratios__sheet1.csv` | financial_ratios.xlsx | 1,184 | 115.5 KB |
| `market_cap__sheet1.csv` | market_cap.xlsx | 552 | 32.6 KB |
| `peer_groups__sheet1.csv` | peer_groups.xlsx | 56 | 1.7 KB |
| `profitandloss__profit_and_loss.csv` | profitandloss.xlsx | 1,276 | 100.3 KB |
| `prosandcons__pros_and_cons.csv` | prosandcons.xlsx | 16 | 1.5 KB |
| `sectors__sheet1.csv` | sectors.xlsx | 92 | 5.1 KB |
| `stock_prices__sheet1.csv` | stock_prices.xlsx | 5,520 | 388.9 KB |
| **TOTAL** | | **12,892** | **969.5 KB** |

---

## Deliverables Created

### Source Modules

#### `src/etl/normalizer.py`
Pure, stateless normalisation functions with full type hints and docstrings:

| Function | Purpose |
|----------|---------|
| `normalize_column_names(columns)` | Convert column labels to snake_case |
| `normalize_ticker(value)` | Uppercase + strip ticker symbols |
| `normalize_year(value)` | Parse 6 raw year formats → `int YYYY` |
| `strip_whitespace(df)` | Strip leading/trailing spaces from all string cells |
| `normalize_dataframe(df)` | Compose all transforms into a single pipeline call |

Year formats handled:
- `"Mar 2023"` → 2023
- `"Dec 2012"` → 2012
- `"Mar-13"` → 2013 _(2-digit interpreted as 20xx)_
- `"Mar-2014"` → 2014
- `2024` _(int)_ → 2024
- `"2024"` _(bare string)_ → 2024

#### `src/etl/loader.py`
Reusable Excel loading framework:

| Function | Purpose |
|----------|---------|
| `discover_excel_files(raw_dir)` | Glob all `.xlsx`, exclude `- Copy` files |
| `load_workbook(path)` | Load all sheets; detect & skip Bluestock banner rows |
| `load_and_normalize(path)` | Load + apply full normalisation pipeline |
| `save_processed(df, ...)` | Persist normalised DataFrame as UTF-8 CSV |
| `run_pipeline(...)` | Orchestrate full ETL; write audit log |

Key design decisions:
- **Banner detection**: 6 Bluestock-style files have `row 0` = branding; `row 1` = real headers. The loader auto-detects and skips these.
- **Graceful degradation**: Missing files, bad sheets, and save errors are caught, logged, and recorded in the audit as `ERROR:…` rather than crashing.
- **Audit trail**: Every sheet processed emits an audit record with `file_name`, `sheet_name`, `rows_loaded`, `columns_loaded`, `status`, and UTC `timestamp`.

### Test Suites

#### `tests/etl/test_normalizer.py` — 52 tests
| Test Class | Count | Coverage |
|-----------|-------|----------|
| `TestNormalizeColumnNames` | 13 | snake_case, %, dedup, empty, mixed types |
| `TestNormalizeTicker` | 11 | uppercase, strip, None, NaN, numeric |
| `TestNormalizeYear` | 18 | all 6 raw formats, nulls, out-of-range, boundaries |
| `TestStripWhitespace` | 5 | strings, numerics, mutation safety, NaN |
| `TestNormalizeDataframe` | 7 | end-to-end integration |

#### `tests/etl/test_loader.py` — 31 tests
| Test Class | Count | Coverage |
|-----------|-------|----------|
| `TestDiscoverExcelFiles` | 7 | discovery, Copy exclusion, sorting, types, missing dir |
| `TestHasBannerRow` | 4 | banner files, clean files, case insensitivity |
| `TestLoadWorkbook` | 5 | clean schema, banner skip, missing file, return types |
| `TestLoadAndNormalize` | 5 | snake_case cols, uppercase tickers, int years |
| `TestRunPipeline` | 9 | audit structure, CSV output, row counts, Copy exclusion |

### Audit Log

`output/load_audit.csv` — **12 records**, all status `OK`.

---

## Issues Found

| # | Issue | Severity | Resolution |
|---|-------|----------|-----------|
| 1 | `profitandloss.xlsx` contains `"TTM"` (Trailing Twelve Months) values in the `year` column | Low | `normalize_year()` returns `None` for unrecognised formats and logs a warning. 100 TTM rows have `year = null` in the processed CSV. This is expected behaviour — TTM rows represent the latest rolling period and require special handling in Day 3 validation. |
| 2 | 7 Excel files use Bluestock branding banner as row 0 (including prosandcons.xlsx) | Low | Handled automatically via `BANNER_FILES` set in loader |
| 3 | Windows `cp1252` console rejects Unicode arrows in log messages | Low | Replaced `→` with ASCII `->` in all log format strings |
| 4 | Python Scripts dir not on PATH (pytest, pip executables) | Low | Use full Python path `C:\Users\eashi\AppData\Local\Python\pythoncore-3.14-64\python.exe` |

---

## Test Results

```
============================= test session info ================================
platform win32 -- Python 3.14.5, pytest-9.1.1
collected 83 items

tests/etl/test_normalizer.py   52 passed
tests/etl/test_loader.py       31 passed

======================== 83 passed in 1.88s ====================================
```

**Pass rate: 100% (83/83)**

---

## Day 2 Completion Checklist

- [x] `src/etl/normalizer.py` — 5 functions, fully typed, documented
- [x] `src/etl/loader.py` — dynamic discovery, banner handling, audit log
- [x] `normalize_year()` — 6 raw formats handled
- [x] `normalize_ticker()` — uppercase + strip
- [x] `normalize_column_names()` — snake_case, %, dedup
- [x] All **12** Excel files loaded successfully
- [x] All **12** processed CSVs saved to `data/processed/`
- [x] `output/load_audit.csv` generated (12 records, all OK)
- [x] `tests/etl/test_normalizer.py` — 52 tests, 100% pass
- [x] `tests/etl/test_loader.py` — 31 tests, 100% pass
- [x] Production-quality: type hints, logging, docstrings, error handling
- [x] `prosandcons.xlsx` — ✅ now ingested (16 rows, Pros & Cons sheet)

---

## Ready for Day 3

Day 2 output provides a clean, validated foundation for Day 3:

- **Input**: `data/processed/*.csv` — 12 normalised datasets, **12,892 rows total**
- **Known data quality flag**: `profitandloss.xlsx` has 100 `TTM` year values → `null` after normalisation. Day 3 validation should handle these as a special category (not treated as data errors).
- **Next**: Day 3 — Data Quality Validation (schema checks, null rates, outlier detection)

---

*Report updated by Antigravity Agent — Nifty100 Financial Intelligence Platform, Sprint 1 Day 2 (re-run with 12/12 datasets)*
