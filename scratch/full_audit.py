"""
Comprehensive audit of output/ratio_edge_cases.log
Checks every entry against all 10 requirements.
"""
import json
import sys
from collections import Counter

LOG_PATH = 'output/ratio_edge_cases.log'
REQUIRED_KEYS = ['company_id', 'company_name', 'year', 'metric', 'computed_value',
                 'source_value', 'difference', 'category', 'explanation']
VALID_CATEGORIES = {'FORMULA_DIFFERENCE', 'VERSION_DIFFERENCE', 'DATA_SOURCE_ISSUE'}
TEST_IDS = {'B1', 'C1', 'TEST1', 'TEST2', 'A', 'DUMMY', 'TEST', 'SAMPLE', 'MOCK', 'FAKE'}

issues = []  # Collect all issues with (line_number, description)

with open(LOG_PATH, 'r', encoding='utf-8') as f:
    raw_lines = f.readlines()

print("=" * 70)
print("AUDIT: output/ratio_edge_cases.log")
print("=" * 70)

# ---------------------------------------------------------------
# CHECK 1: Exact line count
# ---------------------------------------------------------------
total_lines = len([l for l in raw_lines if l.strip()])
blank_lines = len([l for l in raw_lines if not l.strip()])
print(f"\n[CHECK 1] Line count")
print(f"  Total non-blank lines: {total_lines}")
print(f"  Blank lines: {blank_lines}")
if total_lines == 1503:
    print(f"  RESULT: PASS (exactly 1503)")
else:
    print(f"  RESULT: FAIL (expected 1503, got {total_lines})")
    issues.append((0, f"Line count mismatch: expected 1503, got {total_lines}"))

# ---------------------------------------------------------------
# CHECK 2: Every line is valid JSON
# ---------------------------------------------------------------
print(f"\n[CHECK 2] JSON validity")
entries = []
json_errors = []
for i, line in enumerate(raw_lines, 1):
    stripped = line.strip()
    if not stripped:
        continue
    try:
        entry = json.loads(stripped)
        entries.append((i, entry))
    except json.JSONDecodeError as e:
        json_errors.append((i, str(e), stripped[:100]))

if json_errors:
    print(f"  RESULT: FAIL ({len(json_errors)} invalid JSON lines)")
    for lineno, err, preview in json_errors[:10]:
        print(f"    Line {lineno}: {err}")
        print(f"      Preview: {preview}...")
        issues.append((lineno, f"Invalid JSON: {err}"))
else:
    print(f"  RESULT: PASS (all {len(entries)} lines are valid JSON)")

# ---------------------------------------------------------------
# CHECK 3: No duplicate entries
# ---------------------------------------------------------------
print(f"\n[CHECK 3] Duplicate check")
seen_keys = {}
duplicates = []
for i, (lineno, entry) in enumerate(entries):
    key = (entry.get('company_id'), entry.get('year'), entry.get('metric'), entry.get('category'))
    if key in seen_keys:
        duplicates.append((lineno, key, seen_keys[key]))
    else:
        seen_keys[key] = lineno

if duplicates:
    print(f"  RESULT: FAIL ({len(duplicates)} duplicates found)")
    for lineno, key, orig_lineno in duplicates[:10]:
        print(f"    Line {lineno} duplicates line {orig_lineno}: {key}")
        issues.append((lineno, f"Duplicate of line {orig_lineno}: {key}"))
else:
    print(f"  RESULT: PASS (0 duplicates)")

# ---------------------------------------------------------------
# CHECK 4: No test artifacts
# ---------------------------------------------------------------
print(f"\n[CHECK 4] Test artifact check")
test_entries = []
for lineno, entry in entries:
    cid = entry.get('company_id', '')
    cname = entry.get('company_name', '')
    if cid in TEST_IDS or (cname and any(t in cname.upper() for t in ['TEST', 'DUMMY', 'MOCK', 'FAKE', 'SAMPLE'])):
        test_entries.append((lineno, cid, cname))

if test_entries:
    print(f"  RESULT: FAIL ({len(test_entries)} test artifacts found)")
    for lineno, cid, cname in test_entries:
        print(f"    Line {lineno}: company_id={cid}, company_name={cname}")
        issues.append((lineno, f"Test artifact: company_id={cid}"))
else:
    print(f"  RESULT: PASS (0 test artifacts)")

# ---------------------------------------------------------------
# CHECK 5: Every entry has all required keys
# ---------------------------------------------------------------
print(f"\n[CHECK 5] Required keys check")
missing_key_entries = []
for lineno, entry in entries:
    missing = [k for k in REQUIRED_KEYS if k not in entry]
    if missing:
        missing_key_entries.append((lineno, missing, entry.get('company_id', '?')))

if missing_key_entries:
    print(f"  RESULT: FAIL ({len(missing_key_entries)} entries missing keys)")
    for lineno, missing, cid in missing_key_entries[:10]:
        print(f"    Line {lineno} ({cid}): missing {missing}")
        issues.append((lineno, f"Missing keys: {missing}"))
else:
    print(f"  RESULT: PASS (all {len(entries)} entries have all 9 required keys)")

# ---------------------------------------------------------------
# CHECK 6: Category values are valid
# ---------------------------------------------------------------
print(f"\n[CHECK 6] Category validation")
invalid_categories = []
category_counter = Counter()
for lineno, entry in entries:
    cat = entry.get('category')
    category_counter[cat] += 1
    if cat not in VALID_CATEGORIES:
        invalid_categories.append((lineno, cat, entry.get('company_id', '?')))

print(f"  Categories found:")
for cat, cnt in category_counter.most_common():
    valid_mark = "OK" if cat in VALID_CATEGORIES else "INVALID"
    print(f"    {cat}: {cnt} [{valid_mark}]")

if invalid_categories:
    print(f"  RESULT: FAIL ({len(invalid_categories)} entries with invalid category)")
    for lineno, cat, cid in invalid_categories[:10]:
        print(f"    Line {lineno} ({cid}): category={cat}")
        issues.append((lineno, f"Invalid category: {cat}"))
else:
    print(f"  RESULT: PASS")

# ---------------------------------------------------------------
# CHECK 7: Malformed values
# ---------------------------------------------------------------
print(f"\n[CHECK 7] Malformed value check")
malformed = []
for lineno, entry in entries:
    cid = entry.get('company_id')
    cname = entry.get('company_name')
    year = entry.get('year')
    metric = entry.get('metric')
    computed = entry.get('computed_value')
    
    problems = []
    
    # Null/empty company_id
    if not cid or cid == 'None' or cid == 'null':
        problems.append(f"company_id is null/empty: {cid!r}")
    
    # Null/empty company_name
    if not cname or cname == 'None' or cname == 'null' or cname == 'Unknown':
        problems.append(f"company_name is invalid: {cname!r}")
    
    # NaN year (as string or float)
    if year is None:
        problems.append("year is None")
    elif isinstance(year, str) and year.lower() in ('nan', 'none', 'null', ''):
        problems.append(f"year is string NaN: {year!r}")
    elif isinstance(year, float) and (year != year):  # NaN check
        problems.append("year is float NaN")
    
    # NaN in computed_value as string
    if isinstance(computed, str) and computed.lower() in ('nan', 'none', 'null'):
        problems.append(f"computed_value is string NaN: {computed!r}")
    
    # Empty metric
    if not metric or metric == 'None':
        problems.append(f"metric is invalid: {metric!r}")
    
    if problems:
        malformed.append((lineno, entry.get('company_id'), problems))

if malformed:
    print(f"  RESULT: FAIL ({len(malformed)} entries with malformed values)")
    for lineno, cid, problems in malformed[:20]:
        for p in problems:
            print(f"    Line {lineno} ({cid}): {p}")
            issues.append((lineno, p))
else:
    print(f"  RESULT: PASS (no malformed values)")

# ---------------------------------------------------------------
# CHECK 8: Trailing whitespace / BOM / encoding issues
# ---------------------------------------------------------------
print(f"\n[CHECK 8] Formatting check")
format_issues = []
if raw_lines and raw_lines[0].startswith('\ufeff'):
    format_issues.append("BOM detected at start of file")
for i, line in enumerate(raw_lines, 1):
    if line.strip() and not line.endswith('\n'):
        if i < len(raw_lines):  # last line is ok without newline
            format_issues.append(f"Line {i}: missing trailing newline")
    if '\t' in line:
        format_issues.append(f"Line {i}: contains tab characters")
    if '\r\n' in line and '\n' in line:
        pass  # Windows line endings are acceptable

if format_issues:
    print(f"  RESULT: WARNING ({len(format_issues)} formatting issues)")
    for fi in format_issues[:10]:
        print(f"    {fi}")
else:
    print(f"  RESULT: PASS (clean formatting)")

# ---------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------
print(f"\n{'=' * 70}")
print(f"AUDIT SUMMARY")
print(f"{'=' * 70}")
print(f"\n  Total entries: {len(entries)}")
print(f"\n  Entries by category:")
for cat, cnt in category_counter.most_common():
    print(f"    {cat}: {cnt}")

comp_counter = Counter(entry.get('company_name', entry.get('company_id', '?')) for _, entry in entries)
print(f"\n  Top 10 companies with most anomalies:")
for comp, cnt in comp_counter.most_common(10):
    print(f"    {comp}: {cnt}")

print(f"\n  Total issues found: {len(issues)}")
if issues:
    print(f"\n  Issue breakdown:")
    issue_types = Counter()
    for _, desc in issues:
        # Categorize
        if 'Duplicate' in desc:
            issue_types['Duplicates'] += 1
        elif 'Test artifact' in desc:
            issue_types['Test artifacts'] += 1
        elif 'Missing keys' in desc:
            issue_types['Missing keys'] += 1
        elif 'Invalid category' in desc:
            issue_types['Invalid category'] += 1
        elif 'Invalid JSON' in desc:
            issue_types['Invalid JSON'] += 1
        elif 'company_name' in desc:
            issue_types['Malformed company_name'] += 1
        elif 'year' in desc:
            issue_types['Malformed year'] += 1
        elif 'Line count' in desc:
            issue_types['Line count'] += 1
        else:
            issue_types['Other'] += 1
    for itype, cnt in issue_types.most_common():
        print(f"    {itype}: {cnt}")

if not issues:
    print(f"\n  VERDICT: ratio_edge_cases.log is submission-ready")
else:
    print(f"\n  VERDICT: ratio_edge_cases.log has {len(issues)} issues that must be resolved")

# Write issues to a file for reference
if issues:
    with open('scratch/audit_issues.txt', 'w') as f:
        for lineno, desc in sorted(issues):
            f.write(f"Line {lineno}: {desc}\n")
    print(f"\n  Full issue list written to scratch/audit_issues.txt")
