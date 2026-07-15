"""Diagnostic script to check dashboard health."""
import sys
import sqlite3
import pandas as pd

sys.path.insert(0, '.')

errors = []
warnings = []

# Test db.py imports
try:
    from src.dashboard.utils.db import (
        get_companies, get_ratios, get_pl, get_bs, get_cf,
        get_sectors, get_peers, get_peer_percentiles,
        get_valuation, get_documents
    )
    print('[OK] db.py imports OK')
except Exception as e:
    errors.append(f'db.py imports: {e}')

# Test screener engine
try:
    from src.screener.engine import ScreenerEngine
    print('[OK] ScreenerEngine import OK')
except Exception as e:
    errors.append(f'ScreenerEngine: {e}')

# Test DB tables
conn = sqlite3.connect('data/db/nifty100.db')
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f'\nDB Tables: {tables}')

# Check required tables
required_tables = ['companies', 'profitandloss', 'balancesheet', 'cashflow',
                   'financial_ratios', 'sectors', 'peer_groups', 'peer_percentiles',
                   'market_cap', 'documents']
for t in required_tables:
    if t not in tables:
        warnings.append(f'Missing table: {t}')
    else:
        count = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f'  [OK] {t}: {count} rows')

# Check capital_allocation_pattern in financial_ratios
if 'financial_ratios' in tables:
    cols = [r[1] for r in conn.execute('PRAGMA table_info(financial_ratios)').fetchall()]
    if 'capital_allocation_pattern' in cols:
        print('\n[OK] financial_ratios.capital_allocation_pattern exists')
        nn = conn.execute("SELECT COUNT(*) FROM financial_ratios WHERE capital_allocation_pattern IS NOT NULL").fetchone()[0]
        print(f'  Non-null values: {nn}')
    else:
        warnings.append('financial_ratios missing capital_allocation_pattern column')
        print('\n[FAIL] financial_ratios.capital_allocation_pattern MISSING')

# Check screener engine actually works
try:
    engine = ScreenerEngine()
    db_path = 'data/db/nifty100.db'
    df = engine.fetch_data(db_path, target_year=2024)
    print(f'\n[OK] ScreenerEngine.fetch_data: {len(df)} rows, cols: {list(df.columns)[:10]}')
    df2 = engine.calculate_composite_quality_score(df)
    print(f'[OK] calculate_composite_quality_score: {len(df2)} rows')
    new_cols = [c for c in df2.columns if c not in df.columns]
    print(f'  New cols: {new_cols}')
    # Check specific cols needed by home page
    for col in ['roe', 'pe', 'debt_equity', 'revenue_cagr_5yr', 'debt_free_label', 'composite_quality_score', 'broad_sector', 'company_name', 'roce', 'net_margin']:
        if col in df2.columns:
            print(f'  [OK] {col}')
        else:
            warnings.append(f'ScreenerEngine output missing col: {col}')
except Exception as e:
    errors.append(f'ScreenerEngine.fetch_data: {e}')
    import traceback
    traceback.print_exc()

# Check peer_groups columns
if 'peer_groups' in tables:
    pcols = [r[1] for r in conn.execute('PRAGMA table_info(peer_groups)').fetchall()]
    print(f'\npeer_groups cols: {pcols}')

# Check peer_percentiles columns
if 'peer_percentiles' in tables:
    ppcols = [r[1] for r in conn.execute('PRAGMA table_info(peer_percentiles)').fetchall()]
    print(f'peer_percentiles cols: {ppcols}')

# Check market_cap columns
if 'market_cap' in tables:
    mccols = [r[1] for r in conn.execute('PRAGMA table_info(market_cap)').fetchall()]
    print(f'market_cap cols: {mccols}')

# Summary
print('\n' + '='*60)
print('ERRORS:')
for e in errors:
    print(f'  [FAIL] {e}')
print('\nWARNINGS:')
for w in warnings:
    print(f'  [WARN] {w}')
if not errors and not warnings:
    print('  None - all checks passed!')
conn.close()
