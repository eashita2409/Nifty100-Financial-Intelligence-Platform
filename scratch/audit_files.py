import os

print("=" * 60)
print("STEP 3: OUTPUT FILE VERIFICATION")
print("=" * 60)

files = {
    "output/ratio_edge_cases.log": "output",
    "output/screener_preview.csv": "output",
    "output/capital_allocation.csv": "output",
    "output/kpi_summary.csv": "output",
    "docs/day14_completion_report.md": "docs",
    "docs/manual_validation.md": "docs",
    "docs/sprint2_retrospective.md": "docs",
}

for fpath, category in files.items():
    exists = os.path.exists(fpath)
    if exists:
        size = os.path.getsize(fpath)
        status = "EMPTY" if size == 0 else f"OK ({size:,} bytes)"
    else:
        status = "MISSING"
    print(f"  [{category}] {fpath:<45} {status}")
