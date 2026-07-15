import sqlite3
import pandas as pd
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
import io

from chart_utils import (generate_revenue_chart, generate_net_profit_chart, 
                         generate_roe_roce_chart, generate_bs_stacked_bar, 
                         generate_cf_waterfall)

_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = _ROOT / "data" / "db" / "nifty100.db"
OUTPUT_DIR = _ROOT / "output"
REPORTS_DIR = _ROOT / "reports"
TEARSHEETS_DIR = REPORTS_DIR / "tearsheets"
SECTOR_DIR = REPORTS_DIR / "sector"
SKIPPED_CSV = OUTPUT_DIR / "skipped_tearsheets.csv"
CASHFLOW_INTEL = OUTPUT_DIR / "cashflow_intelligence.xlsx"
PROS_CONS_CSV = OUTPUT_DIR / "pros_cons_generated.csv"

TEARSHEETS_DIR.mkdir(parents=True, exist_ok=True)
SECTOR_DIR.mkdir(parents=True, exist_ok=True)

def _safe(val, default=0.0):
    if pd.isna(val) or val is None:
        return default
    return val

def build_tearsheet(company_id, company_name, df, pros, cons, cap_alloc):
    doc = SimpleDocTemplate(str(TEARSHEETS_DIR / f"{company_id}.pdf"), pagesize=A4,
                            rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    navy_header_style = ParagraphStyle(
        'NavyHeader', parent=styles['Heading1'], backColor=colors.navy, textColor=colors.white,
        alignment=TA_CENTER, spaceBefore=0, spaceAfter=20, padding=10
    )
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading2'], textColor=colors.black, spaceAfter=10)
    normal_style = styles['Normal']
    
    elements = []
    
    # --- PAGE 1 ---
    elements.append(Paragraph(f"<b>{company_name} ({company_id})</b>", navy_header_style))
    
    # KPIs
    latest = df.iloc[-1]
    
    kpis = [
        [f"Revenue\nRs. {_safe(latest.get('sales')):.0f} Cr", f"Net Profit\nRs. {_safe(latest.get('net_profit')):.0f} Cr", f"ROE\n{_safe(latest.get('return_on_equity_pct')):.1f}%"],
        [f"ROCE\n{_safe(latest.get('return_on_capital_employed_pct')):.1f}%", f"D/E Ratio\n{_safe(latest.get('debt_to_equity')):.2f}", f"Asset Turnover\n{_safe(latest.get('asset_turnover')):.2f}"]
    ]
    
    t = Table(kpis, colWidths=[2*inch]*3, rowHeights=[0.8*inch]*2)
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey)
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Charts
    years = df['year'].fillna(0).tolist()
    rev_buf = generate_revenue_chart(years, df['sales'].fillna(0).tolist())
    np_buf = generate_net_profit_chart(years, df['net_profit'].fillna(0).tolist())
    roe_roce_buf = generate_roe_roce_chart(years, df['return_on_equity_pct'].fillna(0).tolist(), df['return_on_capital_employed_pct'].fillna(0).tolist())
    
    chart_table = Table([[Image(rev_buf, width=2.4*inch, height=1.5*inch), Image(np_buf, width=2.4*inch, height=1.5*inch), Image(roe_roce_buf, width=2.4*inch, height=1.5*inch)]])
    elements.append(chart_table)
    
    # --- PAGE 2 ---
    elements.append(PageBreak())
    elements.append(Paragraph("<b>Financial Deep Dive & Insights</b>", navy_header_style))
    
    # BS and CF Charts
    bs_buf = generate_bs_stacked_bar(
        years,
        df['equity_capital'].fillna(0).tolist(),
        df['borrowings'].fillna(0).tolist(),
        (df.get('reserves', pd.Series(0, index=df.index)).fillna(0) + df.get('other_liabilities', pd.Series(0, index=df.index)).fillna(0)).tolist(),
        df['fixed_assets'].fillna(0).tolist(),
        (df.get('total_assets', pd.Series(0, index=df.index)).fillna(0) - df['fixed_assets'].fillna(0) - df.get('investments', pd.Series(0, index=df.index)).fillna(0) - df.get('other_asset', pd.Series(0, index=df.index)).fillna(0)).tolist(),
        (df.get('investments', pd.Series(0, index=df.index)).fillna(0) + df.get('other_asset', pd.Series(0, index=df.index)).fillna(0)).tolist()
    )
    
    cf_buf = generate_cf_waterfall(
        _safe(latest.get('operating_activity')),
        _safe(latest.get('investing_activity')),
        _safe(latest.get('financing_activity')),
        _safe(latest.get('net_cash_flow', _safe(latest.get('operating_activity'))+_safe(latest.get('investing_activity'))+_safe(latest.get('financing_activity'))))
    )
    
    elements.append(Table([[Image(bs_buf, width=3.5*inch, height=2*inch), Image(cf_buf, width=3.5*inch, height=2*inch)]]))
    elements.append(Spacer(1, 10))
    
    # Pros & Cons
    elements.append(Paragraph(f"<b>Capital Allocation Pattern:</b> {cap_alloc}", title_style))
    elements.append(Spacer(1, 10))
    
    pros_text = "<br/>".join([f"• {p}" for p in pros]) if pros else "None"
    cons_text = "<br/>".join([f"• {c}" for c in cons]) if cons else "None"
    
    pc_data = [
        [Paragraph("<b>Strengths (Pros)</b>", normal_style), Paragraph("<b>Weaknesses (Cons)</b>", normal_style)],
        [Paragraph(pros_text, normal_style), Paragraph(cons_text, normal_style)]
    ]
    pc_table = Table(pc_data, colWidths=[3.5*inch, 3.5*inch])
    pc_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEABOVE', (0,1), (-1,1), 1, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10)
    ]))
    elements.append(pc_table)
    
    doc.build(elements)

def build_sector_report(sector, sector_df, all_ratios):
    doc = SimpleDocTemplate(str(SECTOR_DIR / f"{sector.replace('/', '_')}.pdf"), pagesize=A4,
                            rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    navy_header_style = ParagraphStyle(
        'NavyHeader', parent=styles['Heading1'], backColor=colors.navy, textColor=colors.white,
        alignment=TA_CENTER, spaceBefore=0, spaceAfter=20, padding=10
    )
    elements = []
    elements.append(Paragraph(f"<b>Sector Report: {sector}</b>", navy_header_style))
    
    # Sector median KPIs
    elements.append(Paragraph("<b>Median KPIs (Latest Year)</b>", styles['Heading2']))
    metrics = ['return_on_equity_pct', 'return_on_capital_employed_pct', 'debt_to_equity', 'net_profit_margin_pct', 'revenue_cagr_5yr', 'pat_cagr_5yr', 'interest_coverage', 'asset_turnover']
    medians = sector_df[[m for m in metrics if m in sector_df.columns]].median()
    
    kpi_data = [["Metric", "Median Value"]]
    for m in metrics:
        kpi_data.append([m, f"{_safe(medians.get(m, 0)):.2f}"])
        
    t = Table(kpi_data, colWidths=[3*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (1,0), (1,-1), 'RIGHT')
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Company List
    elements.append(Paragraph("<b>Constituent Companies</b>", styles['Heading2']))
    companies = ", ".join(sector_df['company_id'].unique())
    elements.append(Paragraph(companies, styles['Normal']))
    
    doc.build(elements)

def run():
    conn = sqlite3.connect(DB_PATH)
    
    companies = pd.read_sql_query("SELECT id AS company_id, company_name FROM companies", conn)
    pnl = pd.read_sql_query("SELECT company_id, year, sales, net_profit FROM profitandloss", conn)
    bs = pd.read_sql_query("SELECT company_id, year, equity_capital, reserves, borrowings, other_liabilities, fixed_assets, investments, other_asset, total_assets FROM balancesheet", conn)
    cf = pd.read_sql_query("SELECT company_id, year, operating_activity, investing_activity, financing_activity FROM cashflow", conn)
    ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    sectors = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
    
    if PROS_CONS_CSV.exists():
        pc_df = pd.read_csv(PROS_CONS_CSV)
    else:
        pc_df = pd.DataFrame(columns=["company_id", "type", "text"])
        
    if CASHFLOW_INTEL.exists():
        try:
            cf_intel = pd.read_excel(CASHFLOW_INTEL, sheet_name="Cashflow_Intelligence")
        except Exception:
            cf_intel = pd.DataFrame(columns=["company_id", "year", "capital_allocation_pattern"])
    else:
        cf_intel = pd.DataFrame(columns=["company_id", "year", "capital_allocation_pattern"])
        
    skipped = []
    
    # Merge datasets to align years
    master_df = pnl.merge(bs, on=["company_id", "year"], how="outer")\
                   .merge(cf, on=["company_id", "year"], how="outer")\
                   .merge(ratios, on=["company_id", "year"], how="outer")
    master_df = master_df.sort_values(["company_id", "year"]).dropna(subset=["year"])
    
    print("Generating tearsheets...")
    for idx, row in companies.iterrows():
        cid = row['company_id']
        cname = row['company_name']
        
        c_df = master_df[master_df['company_id'] == cid].dropna(how="all", subset=["sales", "operating_activity", "equity_capital"])
        if len(c_df) < 2:
            skipped.append({"company_id": cid, "reason": f"Only {len(c_df)} years of data"})
            continue
        
        c_pros = pc_df[(pc_df['company_id'] == cid) & (pc_df['type'] == 'PRO')]['text'].tolist()
        c_cons = pc_df[(pc_df['company_id'] == cid) & (pc_df['type'] == 'CON')]['text'].tolist()
        
        latest_year = c_df['year'].max()
        cap_alloc_row = cf_intel[(cf_intel['company_id'] == cid) & (cf_intel['year'] == latest_year)]
        
        if not cap_alloc_row.empty and 'capital_allocation_label' in cap_alloc_row.columns:
            cap_alloc = cap_alloc_row['capital_allocation_label'].values[0]
        elif not cap_alloc_row.empty and 'capital_allocation_pattern' in cap_alloc_row.columns:
            cap_alloc = cap_alloc_row['capital_allocation_pattern'].values[0]
        else:
            cap_alloc = "Unknown"
            
        try:
            build_tearsheet(cid, cname, c_df, c_pros, c_cons, cap_alloc)
        except Exception as e:
            print(f"Error generating tearsheet for {cid}: {e}")
            skipped.append({"company_id": cid, "reason": f"Error: {e}"})

    print(f"Skipped {len(skipped)} companies.")
    pd.DataFrame(skipped).to_csv(SKIPPED_CSV, index=False)
    
    print("Generating sector reports...")
    latest_ratios = ratios.sort_values('year').groupby('company_id').tail(1)
    sector_data = latest_ratios.merge(sectors, on='company_id', how='left')
    
    # 1. Generate for each individual sector (10 reports)
    for sector in sector_data['broad_sector'].dropna().unique():
        sec_df = sector_data[sector_data['broad_sector'] == sector]
        if len(sec_df) > 0:
            build_sector_report(sector, sec_df, ratios)
            
    # 2. Generate overall Nifty100 report (11th report)
    build_sector_report("Nifty100", sector_data, ratios)
            
    print("Batch reporting complete.")

if __name__ == "__main__":
    run()
