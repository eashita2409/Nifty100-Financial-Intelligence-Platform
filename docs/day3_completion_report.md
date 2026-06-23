# Nifty100 Financial Intelligence Platform
# Sprint 1 Day 3 — Completion Report

> **Date**: 23 June 2026  
> **Sprint**: Sprint 1 · Day 3  
> **Focus**: Data Quality Validation Framework  
> **Status**: ✅ COMPLETE — 16/16 rules implemented · 77/77 tests passing

---

## Executive Summary

Day 3 delivers a production-quality Data Quality Validation Framework across
all 12 Nifty100 source datasets. The framework implements 16 DQ rules spanning
structural integrity, financial equation validation, referential integrity, and
business logic checks. Results are fully traceable to individual rows via the
`output/validation_failures.csv` report.

---

## DQ Scorecard

| Rule | Description | Severity | Checked | Failed | Result |
|------|-------------|----------|---------|--------|--------|
| DQ-01 | Primary Key Uniqueness | CRITICAL | 12,892 | 0 | ✅ PASS |
| DQ-02 | Composite Key Uniqueness (company_id, year) | CRITICAL | 5,406 | 594 | ❌ FAIL |
| DQ-03 | Foreign Key Integrity | CRITICAL | 12,800 | 438 | ❌ FAIL |
| DQ-04 | Balance Sheet Equation | CRITICAL | 1,312 | 0 | ✅ PASS |
| DQ-05 | OPM Cross-Check | WARNING | 1,261 | 232 | ⚠️ FAIL |
| DQ-06 | Positive Sales Validation | WARNING | 1,276 | 1 | ⚠️ FAIL |
| DQ-07 | Missing Company IDs | CRITICAL | 12,800 | 0 | ✅ PASS |
| DQ-08 | Missing Ticker Symbols | CRITICAL | 92 | 0 | ✅ PASS |
| DQ-09 | Duplicate Records | WARNING | 12,892 | 0 | ✅ PASS |
| DQ-10 | Year Range Validation | WARNING | 6,991 | 0 | ✅ PASS |
| DQ-11 | Positive Market Cap | CRITICAL | 552 | 0 | ✅ PASS |
| DQ-12 | Positive Stock Price | CRITICAL | 5,520 | 0 | ✅ PASS |
| DQ-13 | Financial Ratio Range Checks | WARNING | 3,471 | 46 | ⚠️ FAIL |
| DQ-14 | Sector Mapping Validation | WARNING | 92 | 0 | ✅ PASS |
| DQ-15 | Peer Group Mapping Validation | WARNING | 92 | 36 | ⚠️ FAIL |
| DQ-16 | Critical Null Field Validation | CRITICAL | 19,356 | 0 | ✅ PASS |

**Total rows checked: 96,805**  
**Total failures: 1,347**  
**CRITICAL failures: 1,032**  
**WARNING failures: 315**

---

## Passing Rules Summary (10/16)

| Rule | Insight |
|------|---------|
| DQ-01 | All primary keys (`id` columns) are unique across all 12 datasets |
| DQ-04 | Balance sheet equation holds exactly for all 1,312 records |
| DQ-07 | No null or empty `company_id` values in any dataset |
| DQ-08 | All 92 company ticker symbols present in companies master |
| DQ-09 | No exact row duplicates across any dataset |
| DQ-10 | All parsed years in valid range [1990–2030]; TTM rows correctly exempt |
| DQ-11 | All market capitalisation values are positive |
| DQ-12 | All OHLCV price data is positive |
| DQ-14 | All 92 companies have sector mappings |
| DQ-16 | No critical null fields (sales, net_profit, close_price, total_assets, etc.) |

---

## Critical Failures — Analysis

### DQ-02: Composite Key Uniqueness — 594 failures
**Root cause**: `balancesheet.xlsx` and several other financial tables contain
duplicate `(company_id, year)` records. Investigation reveals two patterns:
- **FY2024 duplicates**: Most companies have two entries for year 2024 —
  likely one interim and one final filing both present in the source extract.
- **Historical duplicates**: Companies like ASIANPAINT have duplicate rows for
  2013–2016, suggesting the source data was extracted twice from Screener.in.

**Recommendation**: Deduplicate at the ETL layer before database load.
Keep the latest record per `(company_id, year)` (highest `id`).

### DQ-03: Foreign Key Integrity — 438 failures
**Root cause**: `analysis.xlsx` contains `company_id = WIPRO` which is not
present in the companies master table (92 companies). All 438 DQ-03 failures
trace to WIPRO-related records appearing in datasets where that ticker is not
in the companies reference table.

**Recommendation**: Either add WIPRO to the companies master, or filter
WIPRO records out during ETL. Confirm with Bluestock whether WIPRO is a
Nifty 100 constituent in the target universe.

---

## Warning Failures — Analysis

### DQ-05: OPM Cross-Check — 232 failures
**Root cause**: Banking sector companies (AXISBANK, HDFCBANK, ICICIBANK, KOTAKBANK,
SBIN, etc.) report OPM using Net Interest Income (NII) as the numerator, not
operating profit in the conventional sense. Their `opm_percentage` values in the
source are NII-based ratios (sometimes >1000%), while our calculation
`operating_profit / sales × 100` yields 28–35%. The mismatch is structural
and sector-specific, not a data error.

**Recommendation**: Exclude banking / NBFC sector companies from OPM cross-check,
or apply a separate OPM definition for financial companies in Day 4+.

### DQ-06: Positive Sales — 1 failure
**Root cause**: One record has `sales = 0`. Needs investigation to confirm
whether this is a genuine zero-revenue reporting period or a data entry issue.

### DQ-13: Financial Ratio Range Checks — 46 failures
**Root cause**: Extreme P/E ratios for companies during loss years (negative
earnings produce anomalous ratios) and banks with atypical ROE calculations.
These are mathematically valid but business-context-unusual.

**Recommendation**: Add sector-aware ratio bounds for financial companies.

### DQ-15: Peer Group Mapping — 36 failures
**Root cause**: The `peer_groups.xlsx` only contains 56 rows covering a subset
of companies (mainly banks and large IT companies). 36 of 92 Nifty 100
companies have no peer group entry.

**Recommendation**: Expand `peer_groups.xlsx` to cover all 92 companies before
database load.

---

## TTM (Trailing Twelve Months) Handling

`profitandloss.xlsx` contains 100 TTM rows where the year was stored as `"TTM"`
in the source. After Day 2 normalisation, these rows have `year = null`.

The validation framework treats TTM rows as **valid rolling-period records** and
explicitly exempts them from:
- **DQ-02**: Composite key uniqueness (null years excluded from check)
- **DQ-10**: Year range validation (null years skipped)

No DQ failures are raised for TTM rows.

---

## Deliverables

| File | Purpose |
|------|---------|
| [src/etl/validator.py](file:///c:/Users/eashi/OneDrive/Documents/GitHub/Nifty100_Financial_Intelligence_Platform/src/etl/validator.py) | 16 DQ rules, output writers, `run_validation()` orchestrator |
| [tests/etl/test_validator.py](file:///c:/Users/eashi/OneDrive/Documents/GitHub/Nifty100_Financial_Intelligence_Platform/tests/etl/test_validator.py) | 77 tests across all rules + integration |
| [output/validation_failures.csv](file:///c:/Users/eashi/OneDrive/Documents/GitHub/Nifty100_Financial_Intelligence_Platform/output/validation_failures.csv) | 1,347 failure records with row-level traceability |
| [output/dq_summary.csv](file:///c:/Users/eashi/OneDrive/Documents/GitHub/Nifty100_Financial_Intelligence_Platform/output/dq_summary.csv) | 16-rule summary (checked / failed / severity) |

---

## Test Results

```
============================= test session info ================================
platform win32 -- Python 3.14.5, pytest-9.1.1
collected 77 items

tests/etl/test_validator.py   77 passed in 2.56s

======================== 77 passed ============================================
```

**Pass rate: 100% (77/77)**

Test coverage by class:

| Test Class | Tests |
|-----------|-------|
| TestIsTtm | 6 |
| TestDQ01–TestDQ16 | 3–4 per rule = 58 |
| TestWriters | 5 |
| TestRunValidation | 8 |
| **Total** | **77** |

---

## Cumulative Sprint 1 Test Count

| Day | Tests Added | Running Total |
|-----|-------------|---------------|
| Day 2 | 83 | 83 |
| Day 3 | 77 | **160** |

---

## Recommendations for Day 4 (Database Load)

| Priority | Action |
|----------|--------|
| 🔴 HIGH | Deduplicate `(company_id, year)` before DB insert (resolve DQ-02) |
| 🔴 HIGH | Decide WIPRO universe inclusion (resolve DQ-03) |
| 🟡 MEDIUM | Expand peer_groups coverage to all 92 companies (resolve DQ-15) |
| 🟡 MEDIUM | Apply sector-aware OPM check for banking companies (resolve DQ-05) |
| 🟢 LOW | Investigate the single zero-sales record (DQ-06) |

---

## Day 3 Completion Checklist

- [x] `src/etl/validator.py` — 16 DQ rules, fully typed, documented
- [x] `tests/etl/test_validator.py` — 77 tests, 100% pass
- [x] `output/validation_failures.csv` — 1,347 records
- [x] `output/dq_summary.csv` — 16-rule summary
- [x] TTM rows treated as valid (exempt from DQ-02 and DQ-10)
- [x] All 16 rules cover structural, referential, and business-logic checks
- [x] Modular architecture: each rule is an independent, testable function

---

*Report generated by Antigravity Agent — Nifty100 Financial Intelligence Platform, Sprint 1 Day 3*
