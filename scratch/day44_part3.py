import os
import shutil

deliverables_dir = "output/final_deliverables"
os.makedirs(deliverables_dir, exist_ok=True)

final_deliverables = [
    "data/db/nifty100.db",
    "src/dashboard/app.py",
    "docs/analyst_guide.pdf",
    "README.md",
    "output/cluster_labels.csv",
    "output/analysis_parsed.csv",
    "output/cashflow_intelligence.xlsx",
    "output/distress_alerts.csv",
    "output/pattern_changes.csv",
    "output/pros_cons_generated.csv",
    "reports/portfolio/portfolio_summary.pdf",
    "output/capital_allocation.csv",
    "output/valuation_summary.xlsx",
    "output/valuation_flags.csv",
    "output/peer_comparison.xlsx",
    "output/screener_output.xlsx",
    "reports/elbow_plot.png",
    "output/cluster_scatter_plot.png",
    "output/cluster_pca_plot.png",
    "output/rolling_sharpe_chart.png",
    "docs/openapi.json",
    "docs/postman_collection.json",
    "tests/test_api.py"
]

copied = 0
missing = []
for d in final_deliverables:
    if os.path.exists(d):
        dest = os.path.join(deliverables_dir, os.path.basename(d))
        if os.path.abspath(d) != os.path.abspath(dest):
            shutil.copy2(d, dest)
        copied += 1
    else:
        missing.append(d)

if copied >= 23:
    print("23/23 DELIVERABLES PRESENT")
else:
    print(f"Missing deliverables: {missing}")
