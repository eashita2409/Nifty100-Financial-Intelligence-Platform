# Sprint 3 Retrospective

## What Went Well
1. **Reporting & Visualization Engine**: Successfully built a robust reporting engine that turns raw processed data and analytical scores into comprehensive visual and tabular outputs. The generation of Excel-based Peer Comparison reports and customized Radar Charts was streamlined through automated Python scripts.
2. **Quality Validation**: Implemented Data Quality checks that confidently validated edge cases (like Zero Prices, Null revenues, and outlier PE ratios). The test suite ensures data reliability before reaching the presentation layer.
3. **Automated Formatting**: Conditional formatting within Excel (via openpyxl) provided immediate visual insight into peer standing through percentiles, elevating the utility of the reports.

## What Could Be Improved
1. **Test Module Scoping**: Faced minor pathing issues (`ModuleNotFoundError`) with Pytest requiring `PYTHONPATH` adjustments. Ensuring the `src` module is properly installed as an editable package (e.g., via `pip install -e .` or a `setup.py`) would make testing more robust across different environments.
2. **Make Tooling**: Some commands in the provided `Makefile` hit execution snags on Windows (PowerShell/CMD). Migrating to a cross-platform task runner (like `tox` or a pure python CLI wrapper) could reduce OS-specific friction.
3. **Handling Missing Peers**: We noticed some peer cohorts are very sparse (e.g., FMCG only containing Nestle India within this specific database subset). This reduces the utility of "Peer percentiles" for those cohorts.

## Action Items for Next Sprint
- Package the repository into a proper Python module.
- Expand peer mappings to include a broader index if Nifty 100 coverage leaves cohorts too sparse.
- Build a unified PDF export that merges the Radar Charts and Peer Comparisons into a single tear-sheet for each company.
