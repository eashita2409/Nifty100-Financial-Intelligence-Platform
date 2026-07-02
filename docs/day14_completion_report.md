# Sprint 2 - Day 14 Completion Report

## Overview
This report summarizes the completion of Sprint 2, focusing on the resolution of edge cases identified during Day 13, ensuring that financial ratios and derived KPIs are accurately calculated and edge cases for the Financials sector are properly handled.

## Edge Case Resolution Summary
A comprehensive logging mechanism was implemented in `ratios.py` and `leverage.py` to capture and record anomalies in JSON format to `output/ratio_edge_cases.log`.

**Total Anomalies Tracked:** 1503

### By Category
- **VERSION_DIFFERENCE (965 cases):** These represent differences between our computed ROE/ROCE values and the `source_roe` / `source_roce` values initially provided in the `companies` table, mostly due to varying historical versions, rounding differences, or adjustments.
- **FORMULA_DIFFERENCE (538 cases):** These primarily represent cases where Leverage (Debt-to-Equity > 5) or ICR warnings (< 1.5) were systematically suppressed for companies within the Financials sector (Banks, NBFCs), as they naturally operate with high leverage.

### Top Affected Companies
The top five companies exhibiting these variations or requiring suppression are predominantly from the Financials sector:
1. **Punjab National Bank (49 flags)**
2. **Canara Bank (42 flags)**
3. **Indian Railway Finance Corporation Ltd (41 flags)**
4. **Bank of Baroda (39 flags)**
5. **ICICI Bank Ltd (38 flags)**

## Fixes Implemented
1. **Bank ROCE Carve-Out:** Modified `leverage.py` and `ratios.py` to suppress High Leverage warnings and ICR warnings for companies where `broad_sector` = "Financials".
2. **ROE & ROCE Validation:** Validated computed ROE and ROCE against the `source_roe` and `source_roce` respectively, logging an anomaly when `abs(computed - source) > 5`.
3. **KPI Engine Integrity:** 
   - Addressed an issue in `kpi_engine.py` where a Cartesian explosion was occurring when joining the `analysis` table. We filtered the query for `compounded_sales_growth LIKE '5 Years%'`.
   - Cleaned the `five_year_cagr` field to properly extract numerical percentages and avoid `NaN` values.
   - Updated the engine to properly fetch the computed `roe` and `roce` from the `financial_ratios` table as the primary source of truth, treating `companies` data as display-only.
   - Adjusted `year=NaN` sorting bugs that resulted in empty data rows.

## Testing & Validation
All 292 pytest unit tests in the `tests/` directory continue to pass, assuring that the fundamental analytics, ETL, and calculations remain robust and intact.
