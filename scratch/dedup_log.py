import json
from collections import Counter

with open('output/ratio_edge_cases.log', 'r') as f:
    lines = [l.strip() for l in f if l.strip()]

data = [json.loads(l) for l in lines]

# Find exact duplicates
seen = {}
duplicates = []
for i, d in enumerate(data):
    key = (d.get('company_id'), d.get('year'), d.get('metric'), d.get('category'))
    if key in seen:
        duplicates.append((i, key))
    else:
        seen[key] = i

print(f"Total entries: {len(data)}")
print(f"Unique entries: {len(seen)}")
print(f"Duplicate entries: {len(duplicates)}")
print(f"\nDuplicate details:")
for idx, key in duplicates:
    print(f"  Line {idx+1}: {key}")

# Deduplicate and rewrite
unique_data = []
seen_keys = set()
for d in data:
    key = (d.get('company_id'), d.get('year'), d.get('metric'), d.get('category'))
    if key not in seen_keys:
        unique_data.append(d)
        seen_keys.add(key)

with open('output/ratio_edge_cases.log', 'w') as f:
    for d in unique_data:
        f.write(json.dumps(d) + '\n')

print(f"\nDeduplicated log written: {len(unique_data)} entries (removed {len(data) - len(unique_data)} duplicates)")
