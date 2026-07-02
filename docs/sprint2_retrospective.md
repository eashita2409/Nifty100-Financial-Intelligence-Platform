# Sprint 2 - Retrospective

## Overview
This retrospective covers the goals, achievements, and challenges faced during Sprint 2 of the Nifty100 Financial Intelligence Platform, specifically focusing on Days 13 and 14. 

## Goals vs. Achievements

### 1. Bank ROCE/Leverage Carve-Out (Day 13)
**Goal:** Prevent incorrect "High Leverage" warnings for companies in the Financials sector, as naturally high Debt-to-Equity ratios are common for Banks and NBFCs.
**Achievement:** Successfully implemented logic in `leverage.py` to suppress standard high-leverage and low ICR warnings for the Financials sector. The standard logic for non-financials remained intact.

### 2. ROCE/ROE Validation & Traceability (Day 13)
**Goal:** Compare computed ROE and ROCE values with source values to track anomalies and establish the calculated metrics as the single source of truth for downstream reporting.
**Achievement:** Implemented robust JSON logging into `output/ratio_edge_cases.log`. Over 1,500 discrepancies (mostly version/source discrepancies and formula carve-outs) were automatically documented, leaving the computed ratios cleanly populated in the `financial_ratios` table. The `kpi_engine.py` was also upgraded to source ROE/ROCE strictly from `financial_ratios`.

### 3. KPI Output and Validation (Day 14)
**Goal:** Execute the full pipeline, generate `kpi_summary.csv`, perform SQL-driven screener checks, manually validate calculations, and pass all unit tests.
**Achievement:** 
- `kpi_summary.csv` correctly processes metrics for all valid companies.
- A critical bug involving Cartesian explosions caused by duplicate temporal labels in the `analysis` table was resolved.
- A bug involving NaN year sorting in the final KPI DataFrame was identified and fixed.
- Extracted 34 high-performing companies in `screener_preview.csv` (ROE > 15 AND D/E < 1).
- Manual verifications on INFY, TCS, and RELIANCE passed the strict 0.1% tolerance.
- All 292 pytest unit tests executed successfully.

## Challenges & Fixes
- **Data Shape/Duplicates:** The `analysis` table contained text strings like `"5 Years: 13%"` mapped to the `compounded_sales_growth` column, which caused duplicates in outer joins and parsing errors when treated as raw numerics.
  - *Fix:* Integrated Regex parsing `str.extract(r':\s*(-?\d+\.?\d*)')` and SQL-level `LIKE` filters directly within the KPI engine logic.
- **Testing Dependencies:** Modifications to the underlying SQLite schema and queries (such as adding the `companies` table JOIN in profitability queries) broke the testing environment which relied on an outdated mock schema.
  - *Fix:* Expanded the mock setups in `tests/` and injected the necessary schema definitions and standard test data for `companies` and `financial_ratios` to stabilize the CI loop.

## Key Takeaways
1. **Source of Truth:** Maintaining computed values over inherently volatile raw source indicators proves far more robust for automated analytics engines.
2. **Schema Mocking:** For high-volume pipelines, testing frameworks must mock the full database context seamlessly.
3. **Regex over Casting:** Text extraction requires careful regex mapping when interacting with inconsistent flat-file strings. 

## Next Steps for Sprint 3
- Introduce the API layer to expose these insights.
- Build visualization endpoints for the generated edge cases and screener previews.
