# Nifty100 Financial Intelligence Platform
# Dataset Inventory Report

> **Sprint 1 · Day 1** — Dataset Ingestion Preparation  
> **Updated**: 23 June 2026 (re-run with all 12 files)  
> Location: `data/raw/`  
> Source: `C:\Users\eashi\Downloads\`

---

## Summary

| Metric | Value |
|--------|-------|
| Files requested | 12 |
| Files located & copied | **12** |
| Files missing | **0** |
| Total rows across all files | **13,896** |
| Total dataset size | **799.1 KB** |
| Duplicates (`- Copy`) skipped | 0 |

---

## File Inventory

| # | Filename | Sheet Name | Rows | Columns | File Size |
|---|----------|-----------|------|---------|-----------|
| 1 | `analysis.xlsx` | Analysis | 20 | 6 | 6.2 KB |
| 2 | `balancesheet.xlsx` | Balance Sheet | 1,312 | 13 | 97.5 KB |
| 3 | `cashflow.xlsx` | Cash Flow | 1,187 | 7 | 52.6 KB |
| 4 | `companies.xlsx` | Companies | 92 | 12 | 25.5 KB |
| 5 | `documents.xlsx` | Documents | 1,585 | 4 | 49.4 KB |
| 6 | `financial_ratios.xlsx` | Sheet1 | 1,184 | 16 | 108.7 KB |
| 7 | `market_cap.xlsx` | Sheet1 | 552 | 9 | 35.0 KB |
| 8 | `peer_groups.xlsx` | Sheet1 | 56 | 4 | 6.2 KB |
| 9 | `profitandloss.xlsx` | Profit & Loss | 1,276 | 15 | 104.8 KB |
| 10 | `prosandcons.xlsx` | Pros & Cons | 16 | 4 | 6.1 KB |
| 11 | `sectors.xlsx` | Sheet1 | 92 | 6 | 8.6 KB |
| 12 | `stock_prices.xlsx` | Sheet1 | 5,520 | 9 | 298.4 KB |

---

## Detailed File Profiles

### 1. `analysis.xlsx`
- **Sheet**: Analysis
- **Rows**: 20 | **Columns**: 6
- **File Size**: 6.2 KB (6,367 bytes)
- **Notes**: Summary growth metrics (Sales CAGR, Profit CAGR, Stock CAGR, ROE) per company

---

### 2. `balancesheet.xlsx`
- **Sheet**: Balance Sheet
- **Rows**: 1,312 | **Columns**: 13
- **File Size**: 97.5 KB (99,846 bytes)
- **Notes**: Annual balance sheet figures across Nifty 100 constituents

---

### 3. `cashflow.xlsx`
- **Sheet**: Cash Flow
- **Rows**: 1,187 | **Columns**: 7
- **File Size**: 52.6 KB (53,875 bytes)
- **Notes**: Operating, investing, and financing cash flow data

---

### 4. `companies.xlsx`
- **Sheet**: Companies
- **Rows**: 92 | **Columns**: 12
- **File Size**: 25.5 KB (26,073 bytes)
- **Notes**: Master company reference — 92 Nifty 100 constituents with 12 attributes each

---

### 5. `documents.xlsx`
- **Sheet**: Documents
- **Rows**: 1,585 | **Columns**: 4
- **File Size**: 49.4 KB (50,590 bytes)
- **Notes**: Annual report PDF links indexed by company and year

---

### 6. `financial_ratios.xlsx`
- **Sheet**: Sheet1
- **Rows**: 1,184 | **Columns**: 16
- **File Size**: 108.7 KB (111,346 bytes)
- **Notes**: Widest dataset (16 cols) — valuation ratios (P/E, P/B, ROE, ROCE, etc.)

---

### 7. `market_cap.xlsx`
- **Sheet**: Sheet1
- **Rows**: 552 | **Columns**: 9
- **File Size**: 35.0 KB (35,876 bytes)
- **Notes**: Market capitalisation and valuation multiples time series

---

### 8. `peer_groups.xlsx`
- **Sheet**: Sheet1
- **Rows**: 56 | **Columns**: 4
- **File Size**: 6.2 KB (6,399 bytes)
- **Notes**: Peer comparison groupings reference table

---

### 9. `profitandloss.xlsx`
- **Sheet**: Profit & Loss
- **Rows**: 1,276 | **Columns**: 15
- **File Size**: 104.8 KB (107,350 bytes)
- **Notes**: Income statement data — revenue, EBITDA, PAT across years. Contains 100 `TTM` (Trailing Twelve Months) year values.

---

### 10. `prosandcons.xlsx`
- **Sheet**: Pros & Cons
- **Rows**: 16 | **Columns**: 4
- **File Size**: 6.1 KB (6,246 bytes)
- **Notes**: Qualitative analyst notes — pros and cons text per company. No year column.

---

### 11. `sectors.xlsx`
- **Sheet**: Sheet1
- **Rows**: 92 | **Columns**: 6
- **File Size**: 8.6 KB (8,819 bytes)
- **Notes**: Sector/industry classification and index weight for 92 companies

---

### 12. `stock_prices.xlsx`
- **Sheet**: Sheet1
- **Rows**: 5,520 | **Columns**: 9
- **File Size**: 298.4 KB (305,606 bytes)
- **Notes**: **Largest dataset** — daily OHLCV price/volume time series data

---

## Dataset Size Distribution

```
stock_prices.xlsx      ████████████████████████ 298.4 KB  (37.3%)
financial_ratios.xlsx  █████████████            108.7 KB  (13.6%)
profitandloss.xlsx     █████████████            104.8 KB  (13.1%)
balancesheet.xlsx      ████████████             97.5  KB  (12.2%)
cashflow.xlsx          ██████                   52.6  KB  ( 6.6%)
documents.xlsx         ██████                   49.4  KB  ( 6.2%)
market_cap.xlsx        ████                     35.0  KB  ( 4.4%)
companies.xlsx         ███                      25.5  KB  ( 3.2%)
sectors.xlsx           █                         8.6  KB  ( 1.1%)
analysis.xlsx          █                         6.2  KB  ( 0.8%)
peer_groups.xlsx       █                         6.2  KB  ( 0.8%)
prosandcons.xlsx       █                         6.1  KB  ( 0.8%)
```

---

## Row Count Distribution

```
stock_prices.xlsx      ████████████████████████  5,520 rows  (39.7%)
documents.xlsx         ███████                   1,585 rows  (11.4%)
balancesheet.xlsx      ██████                    1,312 rows  ( 9.4%)
profitandloss.xlsx     ██████                    1,276 rows  ( 9.2%)
cashflow.xlsx          █████                     1,187 rows  ( 8.5%)
financial_ratios.xlsx  █████                     1,184 rows  ( 8.5%)
market_cap.xlsx        ██                          552 rows  ( 4.0%)
companies.xlsx         ░                            92 rows  ( 0.7%)
sectors.xlsx           ░                            92 rows  ( 0.7%)
peer_groups.xlsx       ░                            56 rows  ( 0.4%)
analysis.xlsx          ░                            20 rows  ( 0.1%)
prosandcons.xlsx       ░                            16 rows  ( 0.1%)
                                          Total: 13,896 rows
```

---

## Ingestion Verification Checklist

- [x] All 12 source files located in `C:\Users\eashi\Downloads\`
- [x] No duplicate files (`- Copy` variants) copied
- [x] Source files not modified (copy-only operation)
- [x] All 12 files successfully copied to `data/raw/`
- [x] All 12 files readable by pandas / openpyxl
- [x] Row counts, column counts, and file sizes captured
- [x] `prosandcons.xlsx` — ✅ present (16 rows, 4 cols)

---

*Report updated by Antigravity Agent — Nifty100 Financial Intelligence Platform, Sprint 1 (all 12 datasets confirmed)*
