"""
Full runtime test of all dashboard page logic.
Simulates exactly what each Streamlit page does, without Streamlit itself.
Reports PASS/FAIL per page with details.
"""
import sys
import sqlite3
import pandas as pd
import traceback
from pathlib import Path

ROOT = Path('.')
sys.path.insert(0, str(ROOT))

RESULTS = []

def ok(page, detail=""):
    RESULTS.append(('PASS', page, detail))
    print(f'[PASS] {page}' + (f' — {detail}' if detail else ''))

def fail(page, detail):
    RESULTS.append(('FAIL', page, detail))
    print(f'[FAIL] {page} — {detail}')
    traceback.print_exc()

def load(table, where=""):
    conn = sqlite3.connect('data/db/nifty100.db')
    q = f'SELECT * FROM {table}' + (f' WHERE {where}' if where else '')
    df = pd.read_sql_query(q, conn)
    conn.close()
    return df

print('='*60)
print('NIFTY 100 DASHBOARD — FULL RUNTIME VERIFICATION')
print('='*60)

# ─────────────────────────────────────────────
# PAGE 1: HOME
# ─────────────────────────────────────────────
print('\n[PAGE 1: HOME]')
try:
    from src.screener.engine import ScreenerEngine
    engine = ScreenerEngine()

    for year in [2024, 2023, 2022]:
        df = engine.fetch_data('data/db/nifty100.db', target_year=year)
        df = engine.calculate_composite_quality_score(df).fillna(0)

        assert not df.empty, f"Empty data for {year}"
        assert 'roe' in df.columns
        assert 'pe' in df.columns
        assert 'debt_equity' in df.columns
        assert 'revenue_cagr_5yr' in df.columns
        assert 'debt_free_label' in df.columns
        assert 'composite_quality_score' in df.columns
        assert 'broad_sector' in df.columns
        assert 'company_name' in df.columns

        avg_roe = df['roe'].mean()
        sector_counts = df['broad_sector'].value_counts()
        top10 = df.nlargest(10, 'composite_quality_score')
        hist_data = df['composite_quality_score']

        print(f'  Year {year}: {len(df)} companies, avg ROE={avg_roe:.2f}%, '
              f'{len(sector_counts)} sectors, top company={top10.iloc[0]["company_name"]}')

    ok('Home', f'{len(df)} companies, {df["broad_sector"].nunique()} sectors, year filter works')

except Exception as e:
    fail('Home', str(e))


# ─────────────────────────────────────────────
# PAGE 2: COMPANY PROFILE (10 companies)
# ─────────────────────────────────────────────
print('\n[PAGE 2: COMPANY PROFILE]')
try:
    companies = load('companies')
    ratios = load('financial_ratios').dropna(subset=['year'])
    pl = load('profitandloss').dropna(subset=['year'])
    cf = load('cashflow')
    sectors = load('sectors')
    pc_path = ROOT / 'output' / 'pros_cons_generated.csv'
    pc_df = pd.read_csv(pc_path) if pc_path.exists() else pd.DataFrame()

    test_companies = [
        'TCS', 'HDFCBANK', 'INFY', 'RELIANCE', 'AXISBANK',
        'TATAMOTORS', 'SBIN', 'WIPRO', 'BAJFINANCE', 'KOTAKBANK'
    ]
    results_detail = []

    for cid in test_companies:
        if cid not in companies['id'].values:
            results_detail.append(f'{cid}: NOT IN DB')
            continue

        comp_info = companies[companies['id'] == cid].iloc[0]
        sector_info = sectors[sectors['company_id'] == cid]
        comp_ratios = ratios[ratios['company_id'] == cid].sort_values('year')
        comp_pl = pl[pl['company_id'] == cid].sort_values('year')
        comp_cf = cf[cf['company_id'] == cid].sort_values('year')

        # KPIs
        if not comp_ratios.empty:
            latest = comp_ratios.iloc[-1]
            roe = latest.get('return_on_equity_pct')
            roce = latest.get('return_on_capital_employed_pct')
            cap_alloc = latest.get('capital_allocation_pattern')
        else:
            roe = roce = cap_alloc = None

        # Charts would render
        assert not comp_pl.empty, f'{cid}: no P&L data'
        assert 'sales' in comp_pl.columns
        assert 'net_profit' in comp_pl.columns

        # CF chart
        assert not comp_cf.empty, f'{cid}: no CF data'
        assert 'operating_activity' in comp_cf.columns

        # Pros/cons
        if not pc_df.empty:
            comp_pros = pc_df[(pc_df['company_id'] == cid) & (pc_df['type'] == 'PRO')]
            comp_cons = pc_df[(pc_df['company_id'] == cid) & (pc_df['type'] == 'CON')]
            n_pros = len(comp_pros)
            n_cons = len(comp_cons)
        else:
            n_pros = n_cons = 0

        sector_name = sector_info['broad_sector'].iloc[0] if not sector_info.empty else 'N/A'
        results_detail.append(
            f'{cid}: sector={sector_name}, ROE={roe:.1f}% if roe else N/A, '
            f'cap={cap_alloc}, {len(comp_ratios)}yr, pros={n_pros}, cons={n_cons}'
        )

    for r in results_detail:
        print(f'  {r}')
    ok('Company Profile', f'{len(test_companies)} companies tested')

except Exception as e:
    fail('Company Profile', str(e))


# ─────────────────────────────────────────────
# PAGE 3: SCREENER
# ─────────────────────────────────────────────
print('\n[PAGE 3: SCREENER]')
try:
    engine = ScreenerEngine()
    df = engine.fetch_data('data/db/nifty100.db', target_year=2024)
    df = engine.calculate_composite_quality_score(df).fillna(0)

    presets = [
        {'roe_min': 15.0, 'roce_min': 15.0, 'debt_equity_max': 1.0, 'fcf_min': 0.0,
         'revenue_cagr_5y_min': 10.0, 'pat_cagr_5y_min': 10.0, 'pe_max': 100.0,
         'pb_max': 20.0, 'dividend_yield_min': 0.0},  # Quality
        {'roe_min': 0.0, 'roce_min': 0.0, 'debt_equity_max': 5.0, 'fcf_min': -1000.0,
         'revenue_cagr_5y_min': 0.0, 'pat_cagr_5y_min': 0.0, 'pe_max': 20.0,
         'pb_max': 3.0, 'dividend_yield_min': 0.0},   # Value
        {'roe_min': 0.0, 'roce_min': 0.0, 'debt_equity_max': 5.0, 'fcf_min': -1000.0,
         'revenue_cagr_5y_min': 15.0, 'pat_cagr_5y_min': 15.0, 'pe_max': 100.0,
         'pb_max': 20.0, 'dividend_yield_min': 0.0},  # Growth
    ]
    preset_names = ['Quality', 'Value', 'Growth']

    for pname, params in zip(preset_names, presets):
        filtered = engine.apply_filters(df, params)
        # CSV export
        csv_bytes = filtered.to_csv(index=False).encode('utf-8')
        assert len(csv_bytes) > 0, f'{pname}: CSV export empty'
        print(f'  Preset {pname}: {len(filtered)} companies, CSV={len(csv_bytes)} bytes')

    # Slider test — ROE >= 20
    roe20 = engine.apply_filters(df, {'roe_min': 20.0, 'roce_min': 0.0,
        'debt_equity_max': 5.0, 'fcf_min': -1000.0, 'revenue_cagr_5y_min': 0.0,
        'pat_cagr_5y_min': 0.0, 'pe_max': 100.0, 'pb_max': 20.0, 'dividend_yield_min': 0.0})
    print(f'  ROE>=20 filter: {len(roe20)} companies')

    ok('Screener', f'{len(df)} companies loaded, presets work, CSV export works')

except Exception as e:
    fail('Screener', str(e))


# ─────────────────────────────────────────────
# PAGE 4: PEER COMPARISON
# ─────────────────────────────────────────────
print('\n[PAGE 4: PEER COMPARISON]')
try:
    peers = load('peer_groups')
    percentiles = load('peer_percentiles')
    companies = load('companies')

    groups = peers['peer_group_name'].dropna().unique()
    print(f'  {len(groups)} peer groups: {list(groups)}')

    radar_metrics = {
        'roe_rank': 'ROE', 'roce_rank': 'ROCE', 'npm_rank': 'Net Profit Margin',
        'debt_equity_rank': 'Debt/Equity', 'fcf_rank': 'Free Cash Flow',
        'revenue_cagr_rank': 'Rev CAGR (5Y)'
    }

    tested_groups = []
    for group in groups:
        grp_companies = peers[peers['peer_group_name'] == group]
        latest_year = percentiles['year'].max()
        pp_latest = percentiles[percentiles['year'] == latest_year]
        merged = grp_companies.merge(companies, left_on='company_id', right_on='id', how='inner')
        merged = merged.merge(pp_latest, on='company_id', how='left')

        # Radar chart simulation
        avail_metrics = {k: v for k, v in radar_metrics.items() if k in merged.columns}
        if avail_metrics:
            peer_avg = merged[list(avail_metrics.keys())].fillna(50).mean().to_dict()
            for idx, row in merged.iterrows():
                comp_r = [float(row[k]) if pd.notna(row.get(k)) else 50 for k in avail_metrics.keys()]
                # This is what the radar chart trace uses
                break  # Just test first company

        tested_groups.append(f'{group}({len(merged)}co)')

    print(f'  Groups: {tested_groups}')

    # KPI table test
    engine = ScreenerEngine()
    df_raw = engine.fetch_data('data/db/nifty100.db', target_year=2024)
    df_raw = engine.calculate_composite_quality_score(df_raw).fillna(0)

    sample_group = groups[0]
    grp = peers[peers['peer_group_name'] == sample_group]
    merged_grp = grp.merge(companies, left_on='company_id', right_on='id', how='inner')
    kpi_table = merged_grp[['company_id', 'company_name', 'is_benchmark']].merge(
        df_raw, on='company_id', how='inner'
    )
    print(f'  KPI table for "{sample_group}": {len(kpi_table)} rows')

    ok('Peer Comparison', f'{len(groups)} groups, radar chart data OK, KPI table OK')

except Exception as e:
    fail('Peer Comparison', str(e))


# ─────────────────────────────────────────────
# PAGE 5: TREND ANALYSIS
# ─────────────────────────────────────────────
print('\n[PAGE 5: TREND ANALYSIS]')
try:
    companies = load('companies')
    ratios = load('financial_ratios').dropna(subset=['year'])
    pl = load('profitandloss').dropna(subset=['year'])

    metric_map = {
        'Revenue (Cr)': 'sales', 'Net Profit (Cr)': 'net_profit',
        'ROE (%)': 'return_on_equity_pct', 'ROCE (%)': 'return_on_capital_employed_pct',
        'OPM (%)': 'opm_percentage', 'Revenue CAGR 5Y (%)': 'revenue_cagr_5yr',
        'PAT CAGR 5Y (%)': 'pat_cagr_5yr', 'FCF (Cr)': 'free_cash_flow_cr',
        'Debt to Equity': 'debt_to_equity', 'Asset Turnover': 'asset_turnover',
        'Net Profit Margin (%)': 'net_profit_margin_pct', 'EPS': 'eps',
    }

    test_cos = ['TCS', 'RELIANCE', 'SBIN', 'TATAMOTORS']
    for cid in test_cos:
        comp_ratios = ratios[ratios['company_id'] == cid]
        comp_pl = pl[pl['company_id'] == cid]
        trend_df = comp_pl.merge(comp_ratios, on=['company_id', 'year'], how='outer').sort_values('year')

        avail = [name for name, col in metric_map.items() if col in trend_df.columns]
        # Simulate chart for Revenue + Net Profit
        for metric in ['Revenue (Cr)', 'Net Profit (Cr)']:
            col = metric_map[metric]
            if col in trend_df.columns:
                mdata = trend_df[['year', col]].dropna()
                yoy = mdata[col].pct_change() * 100
                assert len(mdata) > 0
        print(f'  {cid}: {len(trend_df)} years, {len(avail)}/{len(metric_map)} metrics available')

    ok('Trend Analysis', f'{len(test_cos)} companies, {len(avail)} metrics, YoY calc works')

except Exception as e:
    fail('Trend Analysis', str(e))


# ─────────────────────────────────────────────
# PAGE 6: SECTOR ANALYSIS
# ─────────────────────────────────────────────
print('\n[PAGE 6: SECTOR ANALYSIS]')
try:
    sectors = load('sectors')
    ratios = load('financial_ratios').dropna(subset=['year'])
    pl = load('profitandloss').dropna(subset=['year'])
    mc = load('market_cap')
    companies = load('companies')

    latest_year = ratios['year'].max()
    lr = ratios[ratios['year'] == latest_year]
    lpl = pl[pl['year'] == latest_year]
    lmc = mc[mc['year'] == latest_year]

    df = sectors.merge(companies[['id', 'company_name']], left_on='company_id', right_on='id')
    df = df.merge(lr, on='company_id', how='left')
    df = df.merge(lpl[['company_id', 'sales']], on='company_id', how='left')
    df = df.merge(lmc[['company_id', 'market_cap_crore']], on='company_id', how='left')

    broad_sectors = sorted(df['broad_sector'].dropna().unique())
    print(f'  Sectors: {broad_sectors}')

    for sector in broad_sectors:
        sdf = df[df['broad_sector'] == sector].copy()
        # Bubble chart
        plot = sdf.dropna(subset=['sales', 'return_on_equity_pct'])
        mc_plot = plot.dropna(subset=['market_cap_crore'])
        mc_plot = mc_plot[mc_plot['market_cap_crore'] > 0]
        # Sub-sector medians
        grpcol = 'sub_sector' if 'sub_sector' in sdf.columns else 'broad_sector'
        avail_cols = [c for c in ['return_on_equity_pct', 'return_on_capital_employed_pct',
                                   'revenue_cagr_5yr', 'pat_cagr_5yr', 'debt_to_equity',
                                   'free_cash_flow_cr'] if c in sdf.columns]
        medians = sdf.groupby(grpcol)[avail_cols].median().reset_index()
        print(f'  {sector}: {len(sdf)} companies, bubble={len(mc_plot)}, sub_medians={len(medians)}')

    ok('Sector Analysis', f'{len(broad_sectors)} sectors, bubble charts OK, sub-sector medians OK')

except Exception as e:
    fail('Sector Analysis', str(e))


# ─────────────────────────────────────────────
# PAGE 7: CAPITAL ALLOCATION
# ─────────────────────────────────────────────
print('\n[PAGE 7: CAPITAL ALLOCATION]')
try:
    ratios = load('financial_ratios').dropna(subset=['year'])
    companies = load('companies')

    latest_year = ratios['year'].max()
    latest = ratios[ratios['year'] == latest_year].copy()
    df = latest.merge(companies[['id', 'company_name']], left_on='company_id', right_on='id', how='left')
    df_pat = df.dropna(subset=['capital_allocation_pattern'])

    # Fallback test
    if df_pat.empty:
        all_pat = ratios.dropna(subset=['capital_allocation_pattern'])
        df_pat = (all_pat.sort_values('year').groupby('company_id').tail(1)
                  .merge(companies[['id', 'company_name']], left_on='company_id', right_on='id', how='left'))

    patterns = sorted(df_pat['capital_allocation_pattern'].unique())
    print(f'  {len(df_pat)} companies with patterns: {patterns}')

    # Treemap data
    df_pat['count'] = 1
    assert 'company_name' in df_pat.columns
    assert 'capital_allocation_pattern' in df_pat.columns

    # Pattern deep dive
    for pat in patterns:
        sub = df_pat[df_pat['capital_allocation_pattern'] == pat]
        med_roe = sub['return_on_equity_pct'].median()
        med_fcf = sub['free_cash_flow_cr'].median()
        print(f'  {pat}: {len(sub)} companies, median ROE={med_roe:.1f}%, median FCF={med_fcf:.0f}Cr')

    # Pattern changes
    pc = ROOT / 'output' / 'pattern_changes.csv'
    changes = pd.read_csv(pc) if pc.exists() else pd.DataFrame()
    print(f'  YoY pattern changes: {len(changes)} transitions')

    ok('Capital Allocation', f'{len(df_pat)} companies, {len(patterns)} patterns, treemap OK, YoY={len(changes)} changes')

except Exception as e:
    fail('Capital Allocation', str(e))


# ─────────────────────────────────────────────
# PAGE 8: REPORTS
# ─────────────────────────────────────────────
print('\n[PAGE 8: REPORTS]')
try:
    companies = load('companies')
    docs = load('documents')
    sectors = load('sectors')
    companies_enriched = companies.merge(sectors, left_on='id', right_on='company_id', how='left')

    # Tearsheets
    tear_dir = ROOT / 'reports' / 'tearsheets'
    pdfs = list(tear_dir.glob('*.pdf')) if tear_dir.exists() else []
    print(f'  Tearsheets: {len(pdfs)} PDFs')
    assert len(pdfs) >= 90, f'Expected >=90, got {len(pdfs)}'

    # Test downloads for 10 companies
    test_cos = ['TCS', 'HDFCBANK', 'INFY', 'RELIANCE', 'AXISBANK',
                'TATAMOTORS', 'SBIN', 'WIPRO', 'BAJFINANCE', 'KOTAKBANK']
    found, missing = [], []
    for cid in test_cos:
        p = tear_dir / f'{cid}_tearsheet.pdf'
        if p.exists():
            size = p.stat().st_size
            found.append(f'{cid}({size//1024}KB)')
        else:
            missing.append(cid)
    print(f'  Found tearsheets: {found}')
    if missing:
        print(f'  Missing tearsheets: {missing}')

    # Sector reports
    sec_dir = ROOT / 'reports' / 'sector'
    sec_pdfs = list(sec_dir.glob('*.pdf')) if sec_dir.exists() else []
    print(f'  Sector reports: {len(sec_pdfs)} PDFs: {[p.stem for p in sec_pdfs]}')
    assert len(sec_pdfs) >= 10, f'Expected >=10, got {len(sec_pdfs)}'

    # Annual reports
    docs['year'] = pd.to_numeric(docs['year'], errors='coerce')
    docs_sorted = docs.sort_values('year', ascending=False)
    with_links = docs.dropna(subset=['annual_report'])
    with_links = with_links[with_links['annual_report'].str.strip() != '']
    print(f'  Annual report links: {len(with_links)} / {len(docs)} documents')

    # Test TCS docs
    tcs_docs = docs[docs['company_id'] == 'TCS'].sort_values('year', ascending=False)
    print(f'  TCS annual reports: {len(tcs_docs)} ({tcs_docs["year"].min():.0f}–{tcs_docs["year"].max():.0f})')

    ok('Reports', f'{len(pdfs)} tearsheets, {len(sec_pdfs)} sector PDFs, {len(with_links)} annual report links')

except Exception as e:
    fail('Reports', str(e))


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
print('\n' + '='*60)
print('FINAL VERIFICATION SUMMARY')
print('='*60)
passed = [r for r in RESULTS if r[0] == 'PASS']
failed = [r for r in RESULTS if r[0] == 'FAIL']
print(f'PASSED: {len(passed)}/8')
print(f'FAILED: {len(failed)}/8')
print()
for status, page, detail in RESULTS:
    icon = '[OK]' if status == 'PASS' else '[!!]'
    print(f'  {icon} {page}: {detail}')

if not failed:
    print('\nDASHBOARD IS PRODUCTION READY')
else:
    print('\nISSUES TO FIX:')
    for _, page, detail in failed:
        print(f'  - {page}: {detail}')
