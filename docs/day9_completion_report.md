# Sprint 2 – Day 09 Completion Report
**Epic 02:** Financial Ratio Engine - Leverage & Efficiency

## Objective
Implement leverage and efficiency ratios and update the `financial_ratios` table. Avoid implementing CAGR.

## Ratios Implemented
The following functions were implemented in `src/analytics/leverage.py`:
1. **Debt to Equity** (`calculate_debt_to_equity`)
2. **High Leverage Flag** (`is_high_leverage` - Flagged `True` if > 2.0)
3. **Interest Coverage Ratio** (`calculate_interest_coverage_ratio`)
4. **Debt Free Label** (`is_debt_free` - Labeled `True` if Borrowings <= 0.5)
5. **ICR Warning Flag** (`is_icr_warning` - Flagged `True` if ICR < 1.5)
6. **Net Debt** (`calculate_net_debt` - Using `borrowings - cash_equivalents`, defaulted cash equivalents to 0 as standard balancesheets didn't separate it out)
7. **Asset Turnover** (`calculate_asset_turnover`)

## Database & Schema Updates
- Added `high_leverage_flag`, `debt_free_label`, `icr_warning_flag`, and `net_debt_cr` to the database schema in `db/schema.sql` and the physical `nifty100.db`.
- Processed the metrics cross-referencing `profitandloss` and `balancesheet` structures and populated the `financial_ratios` table.
- **Rows Updated:** Successfully populated metrics for **1,041 rows**.

## Testing
- **Test Coverage:** Implemented 9 rigorous unit tests inside `tests/analytics/test_leverage.py`.
- Tested the boundaries (zero denominator, negative equity/interest, missing rows) seamlessly. Also included an integration test for Pandas dataframe read and DB update mechanics parsing SQLite booleans.
- **Result:** 9/9 passed.
