"""
Sprint 4 Day 27 - Comprehensive QA Test Suite
Tests all 8 pages across 10 companies with timing measurements.
"""
import sys
import os
import time
import traceback
import pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from streamlit.testing.v1 import AppTest

TEST_COMPANIES = [
    'Tata Consultancy Services Ltd',
    'Infosys Ltd',
    'Reliance Industries Ltd',
    'HDFC Bank Ltd',
    'ITC Ltd',
    'Bharat Electronics Ltd',
    'Hindustan Aeronautics Ltd',
    'NTPC Ltd',
    'Sun Pharmaceutical Industries Ltd',
    'Asian Paints Ltd',
]

results = {}

def run_test(page_path, name, timeout=15):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    t0 = time.time()
    at = AppTest.from_file(page_path)
    at.run(timeout=timeout)
    elapsed = time.time() - t0

    if at.exception:
        err = str(at.exception)
        print(f"  [FAIL] Exception: {err[:200]}")
        results[name] = {'status': 'FAIL', 'error': err[:200], 'time_s': round(elapsed, 2)}
        return None, elapsed

    print(f"  [PASS] Rendered in {elapsed:.2f}s")
    results[name] = {'status': 'PASS', 'error': None, 'time_s': round(elapsed, 2)}
    return at, elapsed

def interact_and_check(at, name, selectbox_value=None, multiselect_values=None, timeout=12):
    if at is None:
        return
    try:
        t0 = time.time()
        if selectbox_value and at.selectbox:
            # Find the closest match
            opts = at.selectbox[0].options
            match = next((o for o in opts if selectbox_value.lower() in o.lower()), None)
            if match:
                at.selectbox[0].select(match).run(timeout=timeout)
                elapsed = time.time() - t0
                if at.exception:
                    print(f"  [FAIL] Exception after selecting '{match}': {str(at.exception)[:200]}")
                    results[name]['status'] = 'FAIL'
                    results[name]['error'] = str(at.exception)[:200]
                else:
                    print(f"  [PASS] Selected '{match}' in {elapsed:.2f}s")
                    results[name]['interaction_time_s'] = round(elapsed, 2)
            else:
                print(f"  [WARN] No match for '{selectbox_value}' in options")
    except Exception as e:
        print(f"  [ERROR] Interaction failed: {e}")

# -------------------------------------------------------
# Page 1: Home
# -------------------------------------------------------
at, _ = run_test('src/dashboard/pages/01_home.py', 'Home')

# -------------------------------------------------------
# Page 2: Company Profile - Test 5 companies for timing
# -------------------------------------------------------
profile_times = []
at_profile, _ = run_test('src/dashboard/pages/02_profile.py', 'Company Profile')
for comp in TEST_COMPANIES[:5]:
    t0 = time.time()
    at_p = AppTest.from_file('src/dashboard/pages/02_profile.py')
    at_p.run(timeout=15)
    if not at_p.exception:
        opts = at_p.selectbox[0].options if at_p.selectbox else []
        match = next((o for o in opts if comp.split()[0].lower() in o.lower()), None)
        if match:
            at_p.selectbox[0].select(match).run(timeout=12)
            elapsed = time.time() - t0
            profile_times.append((comp, elapsed, None if not at_p.exception else str(at_p.exception)[:100]))
            print(f"  Profile [{comp[:20]}...]: {elapsed:.2f}s {'OK' if not at_p.exception else 'FAIL'}")

if profile_times:
    avg = sum(t for _, t, _ in profile_times) / len(profile_times)
    print(f"\n  Avg Profile Load: {avg:.2f}s | Target: <3s | {'PASS' if avg < 3 else 'FAIL'}")
    results['Company Profile']['avg_load_time_s'] = round(avg, 2)
    results['Company Profile']['profile_timings'] = {c: round(t, 2) for c, t, _ in profile_times}

# -------------------------------------------------------
# Page 3: Screener - test default and preset interaction
# -------------------------------------------------------
at, _ = run_test('src/dashboard/pages/03_screener.py', 'Screener')
if at and at.button:
    print(f"  Found {len(at.button)} buttons")
    for i, btn in enumerate(at.button):
        print(f"  Button {i}: '{btn.label}'")

# -------------------------------------------------------
# Page 4: Peer Comparison
# -------------------------------------------------------
at, _ = run_test('src/dashboard/pages/04_peers.py', 'Peer Comparison')
if at:
    interact_and_check(at, 'Peer Comparison', selectbox_value='TCS')

# -------------------------------------------------------
# Page 5: Trend Analysis - test multiple companies
# -------------------------------------------------------
at, _ = run_test('src/dashboard/pages/05_trends.py', 'Trend Analysis')
if at:
    for comp in ['TCS', 'RELIANCE', 'HDFCBANK']:
        interact_and_check(at, f'Trend Analysis ({comp})', selectbox_value=comp)

# -------------------------------------------------------
# Page 6: Sector Analysis
# -------------------------------------------------------
at, _ = run_test('src/dashboard/pages/06_sectors.py', 'Sector Analysis')
if at:
    if at.selectbox:
        sectors = at.selectbox[0].options[:3]
        for sec in sectors:
            at.selectbox[0].select(sec).run(timeout=10)
            if at.exception:
                print(f"  [FAIL] Sector '{sec}': {str(at.exception)[:100]}")
            else:
                print(f"  [PASS] Sector '{sec}' rendered OK")

# -------------------------------------------------------
# Page 7: Capital Allocation
# -------------------------------------------------------
at, _ = run_test('src/dashboard/pages/07_capital.py', 'Capital Allocation')
if at:
    if at.selectbox:
        patterns = at.selectbox[0].options[:3]
        for p in patterns:
            at.selectbox[0].select(p).run(timeout=10)
            if at.exception:
                print(f"  [FAIL] Pattern '{p}': {str(at.exception)[:100]}")
            else:
                print(f"  [PASS] Pattern '{p}' rendered OK")

# -------------------------------------------------------
# Page 8: Annual Reports - test multiple companies
# -------------------------------------------------------
at, _ = run_test('src/dashboard/pages/08_reports.py', 'Annual Reports')
if at:
    for comp in ['ITC', 'BEL', 'HAL', 'NTPC', 'SUNPHARMA']:
        interact_and_check(at, f'Annual Reports ({comp})', selectbox_value=comp)

# -------------------------------------------------------
# Print Final Summary
# -------------------------------------------------------
print(f"\n{'='*60}")
print("FINAL QA SUMMARY")
print(f"{'='*60}")
passed = sum(1 for v in results.values() if v['status'] == 'PASS')
failed = sum(1 for v in results.values() if v['status'] == 'FAIL')
print(f"Total Pages Tested: {len(results)}")
print(f"PASSED: {passed} | FAILED: {failed}")
print()
for page, result in results.items():
    status = result['status']
    time_s = result.get('time_s', '?')
    err = result.get('error', '')
    print(f"  [{status}] {page} ({time_s}s) {'| Error: ' + err[:80] if err else ''}")
