# Sprint 2 – Day 11 Completion Report
**Epic 02:** Financial Ratio Engine - Cashflow KPIs

## Objective
Implement structural cashflow KPIs—identifying operational efficiency, capital expenditures, and free cash flows—and classify capital allocation patterns using heuristics.

## KPIs Implemented
The following metrics and classifiers were successfully authored in `src/analytics/cashflow_kpis.py`:
1. **Free Cash Flow (FCF):** Defined mathematically as `Cash from Operations (CFO) - |CapEx|`.
2. **CFO Quality Score:** Defined as `CFO / Net Profit`. Represents earnings realization quality.
3. **CapEx Intensity:** Represented as `|CapEx| / Sales`. Indicates fixed asset reinvestment requirements relative to top-line income.
4. **FCF Conversion:** Represented as `FCF / Net Profit`. Represents the net disposable conversion.
5. **Capital Allocation Pattern Classifier:**
   - **Cash Burn:** Flagged if `CFO < 0`.
   - **Aggressive Expansion:** Flagged if `|CapEx| > CFO`.
   - **Cash Cow / Returner:** Flagged if `FCF > 0` and financing activities show a net payout (`Financing Activity < 0`).
   - **Stable / Moderate Reinvestment:** Default pattern handling remainder cases displaying standard structural sustainability.

## Outputs
- **Data Export:** Generated the CSV dataset `output/capital_allocation.csv` containing cross-referenced variables alongside their calculated metric equivalents for all 1,184 company-year variants dynamically. Columns include: `company_id`, `year`, `fcf`, `cfo_quality_score`, `capex_intensity`, `fcf_conversion`, and `capital_allocation_pattern`.

## Testing
- Implemented **6 comprehensive unit tests** in `tests/analytics/test_cashflow_kpis.py`.
- Verified positive/negative boundaries (e.g., negative CapEx values in standard accounting formats handled using absolute values).
- Re-tested the SQL fetching protocol ensuring the mock-Pandas framework handles `None` zero constraints effectively.
- **Result:** 6/6 assertions fully passed using PyTest.
