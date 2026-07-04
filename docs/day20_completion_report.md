# Sprint 3 — Day 20 Completion Report

## Overview
Successfully generated the comprehensive Peer Comparison Report, providing deep insights into each Nifty 100 company relative to its peer group. The report is neatly organized across multiple worksheets and utilizes conditional formatting to highlight outperformance and underperformance.

## Actions Completed
- **Data Compilation**: Exported the full dataset and joined 20 key performance indicators (KPIs) with their respective company peer group assignments.
- **Percentile Scoring**: Calculated universe-wide percentile ranks (0-100) for all 20 KPIs, taking into account metrics where "lower is better" (e.g., Debt/Equity, P/E, P/B, PEG) to correctly assign higher percentiles to favorable figures.
- **Excel Report Structure (`output/peer_comparison.xlsx`)**:
  - **11 Worksheets**: Created a dedicated worksheet for each of the 11 peer groups.
  - **KPIs & Percentiles**: Configured each worksheet to display the 20 KPI columns side-by-side with their respective percentile columns.
  - **Median Row**: Appended a median row at the bottom of each peer group table to establish the group baseline.
- **Visual Formatting**:
  - **Benchmark Highlight**: Applied a gold highlight row to uniquely identify the benchmark company in each group.
  - **Conditional Formatting**: Added color-coded heatmaps to all percentile columns:
    - **Green**: Top quartile (≥ 75th percentile)
    - **Yellow**: Middle quartiles (25th – 75th percentile)
    - **Red**: Bottom quartile (≤ 25th percentile)

## Next Steps
- Review the peer comparison report for any missing metrics or edge cases.
- Integrate the findings from the peer report into the broader analysis workflow.
