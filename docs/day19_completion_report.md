# Sprint 3 — Day 19 Completion Report

## Overview
Successfully generated radar charts for all Nifty 100 companies. The radar charts visualize a company's performance across key financial metrics and overlay the peer average to provide context.

## Actions Completed
- **Created directory**: `reports/radar_charts/` for storing the visual outputs.
- **Data Normalization**: Applied min-max scaling (0 to 1) for metrics across the dataset to enable multi-axis plotting on a standardized radar chart.
- **Metric Inclusion**: Plotted 8 key performance indicators:
  1. ROE (Return on Equity)
  2. ROCE (Return on Capital Employed)
  3. NPM (Net Profit Margin)
  4. Debt/Equity
  5. FCF (Free Cash Flow)
  6. Revenue CAGR
  7. PAT CAGR
  8. Composite Score
- **Peer Comparison**: Integrated sector-based peer averages for every metric and overlaid these on each company's individual chart.
- **File Generation**: Saved individual `.png` files as `companyname_radar.png` (using company IDs) in the `reports/radar_charts/` directory.

## Next Steps
- Incorporate radar charts into individual company reports.
- Share generated assets with stakeholders for feedback.
