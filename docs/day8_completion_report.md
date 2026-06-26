# Sprint 2 – Day 08 Completion Report
**Epic 02:** Financial Ratio Engine

## Objective
Implement the profitability ratio engine and populate the `financial_ratios` table.

## Ratios Implemented
The following functions were implemented in `src/analytics/ratios.py`:
1. **Net Profit Margin** (`calculate_net_profit_margin`)
2. **Operating Profit Margin** (`calculate_operating_profit_margin`)
3. **Return on Equity** (`calculate_return_on_equity`)
4. **Return on Capital Employed (ROCE)** (`calculate_return_on_capital_employed`)
5. **Return on Assets (ROA)** (`calculate_return_on_assets`)

## Rows Updated
Successfully calculated profitability metrics and populated **1,040 rows** in the `financial_ratios` database table across the following columns:
- `net_profit_margin_pct`
- `operating_profit_margin_pct`
- `return_on_equity_pct`
- `return_on_capital_employed_pct`
- `return_on_assets_pct`
- `sector_relative_roce`

## Edge Cases Handled
- **Zero Denominator:** Handled potential division by zero for metrics with missing or zero denominator values (sales, assets). Returns `None` gracefully instead of throwing exceptions.
- **Negative Equity:** For ROE, handled cases where the sum of `equity + reserves <= 0` by returning `None`.
- **Bank ROCE:** Recognized Financial sector companies (using `broad_sector == 'Financials'`). Prevented absolute benchmark calculations and correctly flagged these rows using `sector_relative_roce = True`.
- **OPM Mismatch Logging:** Cross-referenced calculated Operating Profit Margin with the source `opm_percentage`. Mismatches exceeding 1% were successfully captured and routed to `output/opm_crosscheck.log`.
- **ROA Missing Assets:** Avoided erroneous calculations by returning `None` when `total_assets = 0`.

## Performance Summary
- Schema correctly modified in `db/schema.sql` to include missing ratio columns.
- Python integration includes explicit type hints and well-documented docstrings.
- **Test Coverage:** Created comprehensive testing in `tests/analytics/test_ratios.py` satisfying all requested conditions (including 9 passing assertions covering basic edge cases, mismatch logging using pytest caplog, and testing the database insert lifecycle). Tests ran effectively via pytest.
- Data successfully fetched via SQL queries mapped seamlessly into Pandas DataFrames for quick execution and scalable computation.
