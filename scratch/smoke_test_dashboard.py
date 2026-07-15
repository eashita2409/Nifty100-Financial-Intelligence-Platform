"""Runtime smoke test for all dashboard pages - bypasses Streamlit caching."""
import sys
import sqlite3
import pandas as pd
import traceback
from pathlib import Path

sys.path.insert(0, '.')
ROOT = Path('.')

PASS = []
FAIL = []

def test(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f'[PASS] {name}')
    except Exception as e:
        FAIL.append((name, str(e)))
        print(f'[FAIL] {name}: {e}')
        traceback.print_exc()


def load_table(table):
    conn = sqlite3.connect('data/db/nifty100.db')
    df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
    conn.close()
    return df


# 1. All DB tables load
def test_db_tables():
    tables = ['companies', 'profitandloss', 'balancesheet', 'cashflow',
              'financial_ratios', 'sectors', 'peer_groups', 'peer_percentiles',
              'market_cap', 'documents']
    for t in tables:
        df = load_table(t)
        assert len(df) > 0, f'{t} is empty'
        print(f'  {t}: {len(df)} rows')

test('DB tables', test_db_tables)


# 2. Screener engine - full pipeline
def test_screener():
    from src.screener.engine import ScreenerEngine
    engine = ScreenerEngine()
    df = engine.fetch_data('data/db/nifty100.db', target_year=2024)
    assert len(df) > 0, "fetch_data returned empty df"
    df2 = engine.calculate_composite_quality_score(df)
    assert 'composite_quality_score' in df2.columns
    params = {'roe_min': 10.0, 'roce_min': 0.0, 'debt_equity_max': 5.0,
              'fcf_min': -1000.0, 'revenue_cagr_5y_min': 0.0, 'pat_cagr_5y_min': 0.0,
              'pe_max': 100.0, 'pb_max': 20.0, 'dividend_yield_min': 0.0}
    filtered = engine.apply_filters(df2, params)
    print(f'  {len(df2)} companies total, {len(filtered)} with ROE>=10')
    # Check key columns exist
    for col in ['company_name', 'broad_sector', 'roe', 'pe', 'debt_equity',
                'revenue_cagr_5yr', 'composite_quality_score']:
        assert col in df2.columns, f'Missing col: {col}'

test('ScreenerEngine', test_screener)


# 3. Capital allocation patterns
def test_capital_patterns():
    ratios = load_table('financial_ratios')
    ratios = ratios.dropna(subset=['year'])
    with_pattern = ratios.dropna(subset=['capital_allocation_pattern'])
    assert len(with_pattern) > 0, "No capital allocation patterns found"
    latest_year = ratios['year'].max()
    latest = ratios[ratios['year'] == latest_year].dropna(subset=['capital_allocation_pattern'])
    print(f'  Total with patterns: {len(with_pattern)}, latest year ({latest_year}): {len(latest)}')
    print(f'  Patterns: {sorted(with_pattern["capital_allocation_pattern"].unique())}')
    # Companies without a pattern in latest year
    all_companies = load_table('companies')
    without = all_companies[~all_companies['id'].isin(latest['company_id'].unique())]
    if len(without) > 0:
        print(f'  [WARN] {len(without)} companies have no pattern in latest year')
    assert len(latest) >= 80, f"Expected >=80 companies with patterns in latest year, got {len(latest)}"

test('Capital allocation patterns', test_capital_patterns)


# 4. Peer groups + percentiles merge
def test_peer_merge():
    peers = load_table('peer_groups')
    percentiles = load_table('peer_percentiles')
    companies = load_table('companies')
    
    groups = peers['peer_group_name'].dropna().unique()
    assert len(groups) > 0, "No peer groups"
    print(f'  Peer groups: {list(groups)[:5]}...')
    
    for g in groups[:3]:  # Test first 3 groups
        grp = peers[peers['peer_group_name'] == g]
        latest_year = percentiles['year'].max()
        pp_latest = percentiles[percentiles['year'] == latest_year]
        merged = grp.merge(companies, left_on='company_id', right_on='id', how='inner')
        merged = merged.merge(pp_latest, on='company_id', how='left')
        print(f'  Group "{g}": {len(merged)} companies merged')
        assert len(merged) > 0, f'No data for group {g}'

test('Peer merge', test_peer_merge)


# 5. Sector analysis merge
def test_sector():
    sectors = load_table('sectors')
    ratios = load_table('financial_ratios')
    ratios = ratios.dropna(subset=['year'])
    companies = load_table('companies')
    mc = load_table('market_cap')

    latest_year = ratios['year'].max()
    lr = ratios[ratios['year'] == latest_year]
    
    df = sectors.merge(companies[['id', 'company_name']], left_on='company_id', right_on='id')
    df = df.merge(lr, on='company_id', how='left')
    
    lmc = mc[mc['year'] == latest_year]
    df = df.merge(lmc[['company_id', 'market_cap_crore']], on='company_id', how='left')
    
    assert 'return_on_equity_pct' in df.columns
    assert 'company_name' in df.columns
    print(f'  Sector df: {len(df)} rows, {df["broad_sector"].nunique()} sectors')
    
    # Check bubble chart data
    plot_data = df.dropna(subset=['sales', 'return_on_equity_pct', 'market_cap_crore'])
    print(f'  Bubble chart data: {len(plot_data)} companies with complete data')

test('Sector analysis', test_sector)


# 6. Profile page - company data
def test_profile():
    companies = load_table('companies')
    ratios = load_table('financial_ratios')
    pl = load_table('profitandloss')
    cf = load_table('cashflow')
    
    # Test with 10 diverse companies
    test_companies = ['TCS', 'HDFCBANK', 'INFY', 'RELIANCE', 'AXISBANK',
                      'TATAMOTORS', 'SBIN', 'WIPRO', 'BAJFINANCE', 'KOTAKBANK']
    
    for cid in test_companies:
        if cid not in companies['id'].values:
            continue
        comp_ratios = ratios[ratios['company_id'] == cid].dropna(subset=['year'])
        comp_pl = pl[pl['company_id'] == cid].dropna(subset=['year'])
        comp_cf = cf[cf['company_id'] == cid]
        
        if not comp_ratios.empty:
            latest = comp_ratios.sort_values('year').iloc[-1]
            cap_alloc = latest.get('capital_allocation_pattern')
        else:
            cap_alloc = None
        
        print(f'  {cid}: {len(comp_ratios)}yr ratios, {len(comp_pl)}yr P&L, {len(comp_cf)}yr CF, cap_alloc={cap_alloc}')

test('Company profiles (10 companies)', test_profile)


# 7. Reports and file availability
def test_reports():
    # Annual reports
    docs = load_table('documents')
    assert len(docs) > 0
    has_links = docs.dropna(subset=['annual_report'])
    has_links = has_links[has_links['annual_report'].str.strip() != '']
    print(f'  Annual report links: {len(has_links)} / {len(docs)}')
    
    # Tearsheets
    tearsheet_dir = ROOT / 'reports' / 'tearsheets'
    if tearsheet_dir.exists():
        pdfs = list(tearsheet_dir.glob('*.pdf'))
        print(f'  Tearsheets: {len(pdfs)} PDFs')
        assert len(pdfs) >= 90
    
    # Sector reports
    sector_dir = ROOT / 'reports' / 'sector'
    if sector_dir.exists():
        sector_pdfs = list(sector_dir.glob('*.pdf'))
        print(f'  Sector reports: {len(sector_pdfs)} PDFs')
        assert len(sector_pdfs) >= 10

test('Reports & Files', test_reports)


# 8. Output files
def test_output_files():
    required = [
        'output/analysis_parsed.csv',
        'output/pros_cons_generated.csv',
        'output/cashflow_intelligence.xlsx',
        'output/distress_alerts.csv',
        'output/pattern_changes.csv',
        'output/skipped_tearsheets.csv',
    ]
    for f in required:
        p = ROOT / f
        assert p.exists(), f"Missing: {f}"
        print(f'  {f}: exists')

test('Output files', test_output_files)


# Summary
print('\n' + '='*60)
print(f'PASSED: {len(PASS)}/{len(PASS)+len(FAIL)}')
if FAIL:
    print('FAILURES:')
    for name, err in FAIL:
        print(f'  FAIL: {name} -> {err}')
else:
    print('ALL TESTS PASSED - Dashboard is ready!')
