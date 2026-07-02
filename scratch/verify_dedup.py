import json
from collections import Counter

with open('output/ratio_edge_cases.log', 'r') as f:
    lines = [l.strip() for l in f if l.strip()]

data = [json.loads(l) for l in lines]

# Re-verify
seen = set()
duplicates = 0
for d in data:
    key = (d.get('company_id'), d.get('year'), d.get('metric'), d.get('category'))
    if key in seen:
        duplicates += 1
    seen.add(key)

cat_counter = Counter(d.get('category') for d in data)
comp_counter = Counter(d.get('company_name', d.get('company_id')) for d in data)

print(f"Total entries after dedup: {len(data)}")
print(f"Remaining duplicates: {duplicates}")
print(f"\nCategories: {dict(cat_counter)}")
print(f"\nTop 10 companies:")
for c, n in comp_counter.most_common(10):
    print(f"  {c}: {n}")

# Check for test artifacts
test_entries = [d for d in data if d.get('company_id') in ('B1', 'C1', 'TEST1', 'TEST2', 'A')]
print(f"\nTest artifact entries remaining: {len(test_entries)}")
if test_entries:
    for t in test_entries:
        print(f"  {t.get('company_id')} / {t.get('year')} / {t.get('metric')}")
