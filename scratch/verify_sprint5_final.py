"""Sprint 5 Final Deliverable Verification."""
import sys
import sqlite3
import math
import pandas as pd
from pathlib import Path

ROOT = Path('.')
sys.path.insert(0, str(ROOT))

PASS, FAIL = [], []

def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
        print(f'[PASS] {name}' + (f' — {detail}' if detail else ''))
    else:
        FAIL.append(name)
        print(f'[FAIL] {name}' + (f' — {detail}' if detail else ''))

def load(table):
    conn = sqlite3.connect('data/db/nifty100.db')
    df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
    conn.close()
    return df

print('='*60)
print('SPRINT 5 — FINAL DELIVERABLES VERIFICATION')
print('='*60)

# ── Output files ────────────────────────────────────────────────────────────
print('\n[OUTPUT FILES]')
required_outputs = {
    'output/pros_cons_generated.csv':       None,
    'output/analysis_parsed.csv':           None,
    'output/cashflow_intelligence.xlsx':    None,
    'output/distress_alerts.csv':           None,
    'output/pattern_changes.csv':           None,
    'output/skipped_tearsheets.csv':        None,
    'reports/portfolio/portfolio_summary.pdf': None,
}
for fp in required_outputs:
    p = ROOT / fp
    check(fp, p.exists(), f'{p.stat().st_size//1024} KB' if p.exists() else 'MISSING')

# ── Tearsheets ──────────────────────────────────────────────────────────────
print('\n[TEARSHEETS]')
tear_dir = ROOT / 'reports' / 'tearsheets'
if tear_dir.exists():
    pdfs = list(tear_dir.glob('*.pdf'))
    check('reports/tearsheets/ exists', True, f'{len(pdfs)} PDFs')
    check('Tearsheet count >= 90', len(pdfs) >= 90, f'{len(pdfs)} tearsheets')
else:
    check('reports/tearsheets/ exists', False, 'directory missing')

# ── Sector reports ──────────────────────────────────────────────────────────
print('\n[SECTOR REPORTS]')
sec_dir = ROOT / 'reports' / 'sector'
if sec_dir.exists():
    sec_pdfs = list(sec_dir.glob('*.pdf'))
    check('reports/sector/ exists', True, f'{len(sec_pdfs)} PDFs')
    check('Sector report count >= 11', len(sec_pdfs) >= 11, f'{len(sec_pdfs)} sector reports')
else:
    check('reports/sector/ exists', False, 'directory missing')

# ── Portfolio PDF ────────────────────────────────────────────────────────────
print('\n[PORTFOLIO PDF]')
port_path = ROOT / 'reports' / 'portfolio' / 'portfolio_summary.pdf'
check('portfolio_summary.pdf exists', port_path.exists(),
      f'{port_path.stat().st_size//1024} KB' if port_path.exists() else 'MISSING')

# ── Pros/Cons quality ────────────────────────────────────────────────────────
print('\n[PROS/CONS QUALITY]')
try:
    pc_df = pd.read_csv(ROOT / 'output' / 'pros_cons_generated.csv')
    companies_db = load('companies')
    all_companies = set(companies_db['id'].tolist())

    pros_by_company = pc_df[pc_df['type'] == 'PRO'].groupby('company_id')['text'].count()
    cons_by_company = pc_df[pc_df['type'] == 'CON'].groupby('company_id')['text'].count()

    missing_pros = [c for c in all_companies if pros_by_company.get(c, 0) == 0]
    missing_cons = [c for c in all_companies if cons_by_company.get(c, 0) == 0]

    check('Every company has >= 1 PRO',
          len(missing_pros) == 0,
          f'Missing: {missing_pros[:5]}' if missing_pros else f'{len(pros_by_company)} companies have pros')
    check('Every company has >= 1 CON',
          len(missing_cons) == 0,
          f'Missing: {missing_cons[:5]}' if missing_cons else f'{len(cons_by_company)} companies have cons')

    # Confidence > 60
    if 'confidence' in pc_df.columns:
        low_conf = pc_df[pc_df['confidence'] <= 60]
        check('All confidence > 60', len(low_conf) == 0,
              f'{len(low_conf)} entries with confidence <= 60' if low_conf.empty is False else 'all > 60')
    print(f'  Total pros/cons: {len(pc_df)} rows ({len(pros_by_company)} PRO companies, {len(cons_by_company)} CON companies)')

except Exception as e:
    check('Pros/Cons analysis', False, str(e))

# ── Cashflow Intelligence ────────────────────────────────────────────────────
print('\n[CASHFLOW INTELLIGENCE]')
try:
    ci = pd.read_excel(ROOT / 'output' / 'cashflow_intelligence.xlsx', sheet_name='Latest_Snapshot')
    check('Cashflow Intelligence has 92 companies', len(ci) == 92, f'{len(ci)} rows in Latest_Snapshot')
    required_cols = ['company_id', 'year', 'cfo_quality_score', 'capex_intensity',
                     'fcf_conversion', 'distress_signal', 'deleveraging_flag', 'capital_allocation_pattern']
    for col in required_cols:
        check(f'  Column: {col}', col in ci.columns)
except Exception as e:
    check('Cashflow Intelligence readable', False, str(e))

# ── Distress alerts ──────────────────────────────────────────────────────────
print('\n[DISTRESS ALERTS]')
try:
    da = pd.read_csv(ROOT / 'output' / 'distress_alerts.csv')
    check('distress_alerts.csv readable', True, f'{len(da)} rows')
except Exception as e:
    check('distress_alerts.csv readable', False, str(e))

# ── Pattern changes ──────────────────────────────────────────────────────────
print('\n[PATTERN CHANGES]')
try:
    pc = pd.read_csv(ROOT / 'output' / 'pattern_changes.csv')
    check('pattern_changes.csv readable', True, f'{len(pc)} YoY transitions')
    for col in ['company_id', 'company_name', 'previous_pattern', 'current_pattern', 'change_year']:
        check(f'  pattern_changes has {col}', col in pc.columns)
except Exception as e:
    check('pattern_changes.csv readable', False, str(e))

# ── Portfolio PDF page count ──────────────────────────────────────────────────
print('\n[PORTFOLIO PDF VALIDATION]')
try:
    from reportlab.lib.pagesizes import A4
    # Use PyPDF to count pages if available, otherwise check size
    try:
        import pypdf
        reader = pypdf.PdfReader(str(port_path))
        n_pages = len(reader.pages)
        check('Portfolio PDF has 92 pages', n_pages == 92, f'{n_pages} pages')
    except ImportError:
        # Estimate from file size (each page ~3KB)
        size_kb = port_path.stat().st_size // 1024
        check('Portfolio PDF size > 50 KB', size_kb > 50, f'{size_kb} KB (pypdf not installed for exact count)')
except Exception as e:
    check('Portfolio PDF validation', False, str(e))

# ── Summary ──────────────────────────────────────────────────────────────────
print('\n' + '='*60)
print('SPRINT 5 VERIFICATION SUMMARY')
print('='*60)
print(f'Passed: {len(PASS)}/{len(PASS)+len(FAIL)}')
if FAIL:
    print('Failed:')
    for f in FAIL:
        print(f'  [FAIL] {f}')
else:
    print('ALL CHECKS PASSED — Sprint 5 is COMPLETE')
