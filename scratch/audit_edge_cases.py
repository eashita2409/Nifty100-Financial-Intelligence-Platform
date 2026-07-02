import json
from collections import Counter

print("=" * 60)
print("STEP 4: RATIO EDGE CASE REVIEW")
print("=" * 60)

with open('output/ratio_edge_cases.log', 'r') as f:
    lines = [l.strip() for l in f if l.strip()]

# Parse all lines as JSON
data = []
parse_errors = 0
for i, line in enumerate(lines):
    try:
        entry = json.loads(line)
        data.append(entry)
    except json.JSONDecodeError:
        parse_errors += 1

print(f"\n  Total lines: {len(lines)}")
print(f"  Successfully parsed as JSON: {len(data)}")
print(f"  Parse errors (non-JSON lines): {parse_errors}")

if parse_errors > 0:
    print(f"\n  ⚠ WARNING: {parse_errors} lines are NOT valid JSON. These need to be fixed.")

# Category breakdown
cat_counter = Counter(d.get('category', 'UNKNOWN') for d in data)
print(f"\n  Anomaly count by category:")
for cat, cnt in cat_counter.most_common():
    print(f"    {cat}: {cnt}")

# Top 10 companies
comp_counter = Counter(d.get('company_name', d.get('company_id', 'UNKNOWN')) for d in data)
print(f"\n  Top 10 companies with most anomalies:")
for comp, cnt in comp_counter.most_common(10):
    print(f"    {comp}: {cnt}")

# Duplicate check
print(f"\n  Duplicate check:")
seen = set()
duplicates = 0
for d in data:
    key = (d.get('company_id'), d.get('year'), d.get('metric'), d.get('category'))
    if key in seen:
        duplicates += 1
    seen.add(key)
print(f"    Exact duplicates (same company/year/metric/category): {duplicates}")
if duplicates > 0:
    print(f"    ⚠ DUPLICATES FOUND — need regeneration")
else:
    print(f"    ✓ No duplicates detected")
