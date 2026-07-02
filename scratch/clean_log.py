import json

with open('output/ratio_edge_cases.log', 'r') as f:
    lines = [l.strip() for l in f if l.strip()]

data = [json.loads(l) for l in lines]

# Remove test artifacts (company_ids that don't belong to real Nifty100 companies)
test_ids = {'B1', 'C1', 'TEST1', 'TEST2', 'A'}
clean_data = [d for d in data if d.get('company_id') not in test_ids]

removed = len(data) - len(clean_data)
print(f"Removed {removed} test artifact entries")
print(f"Final clean count: {len(clean_data)}")

with open('output/ratio_edge_cases.log', 'w') as f:
    for d in clean_data:
        f.write(json.dumps(d) + '\n')

# Final verification
seen = set()
dups = 0
for d in clean_data:
    key = (d.get('company_id'), d.get('year'), d.get('metric'), d.get('category'))
    if key in seen:
        dups += 1
    seen.add(key)
print(f"Remaining duplicates: {dups}")
test_remain = [d for d in clean_data if d.get('company_id') in test_ids]
print(f"Remaining test artifacts: {len(test_remain)}")
