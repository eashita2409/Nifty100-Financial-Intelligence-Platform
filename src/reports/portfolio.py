"""
Sprint 5 Day 35 — Portfolio Summary PDF Generator
Generates reports/portfolio/portfolio_summary.pdf
One page per company, sorted alphabetically by NSE ticker.
Each page: Company Name, Ticker, Sector, Top 6 KPIs, Trend arrows.
"""

import sqlite3
import sys
import math
import pandas as pd
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "db" / "nifty100.db"
OUTPUT_DIR = ROOT / "reports" / "portfolio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PDF = OUTPUT_DIR / "portfolio_summary.pdf"

# ── Colour palette ─────────────────────────────────────────────────────────
NAVY    = colors.HexColor("#0D1B2A")
BLUE    = colors.HexColor("#1565C0")
TEAL    = colors.HexColor("#00796B")
GREEN   = colors.HexColor("#2E7D32")
RED     = colors.HexColor("#C62828")
AMBER   = colors.HexColor("#F57F17")
GREY_LT = colors.HexColor("#F5F5F5")
GREY_MID= colors.HexColor("#E0E0E0")
WHITE   = colors.white

PAGE_W, PAGE_H = A4  # 595.27 x 841.89 pts
MARGIN = 1.8 * cm


# ── Load data ──────────────────────────────────────────────────────────────
def load_data():
    conn = sqlite3.connect(DB_PATH)
    companies = pd.read_sql_query("SELECT * FROM companies ORDER BY id", conn)
    sectors   = pd.read_sql_query("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
    ratios    = pd.read_sql_query("""
        SELECT company_id, year,
               return_on_equity_pct,
               return_on_capital_employed_pct,
               debt_to_equity,
               free_cash_flow_cr,
               revenue_cagr_5yr,
               pat_cagr_5yr,
               net_profit_margin_pct,
               interest_coverage
        FROM financial_ratios
        WHERE year IS NOT NULL
        ORDER BY company_id, year
    """, conn)
    conn.close()

    # Ensure year is numeric and drop any NaN years
    ratios['year'] = pd.to_numeric(ratios['year'], errors='coerce')
    ratios = ratios.dropna(subset=['year'])

    # Merge sector
    merged = companies.merge(sectors, left_on="id", right_on="company_id", how="left")
    return merged, ratios


def trend_arrow(current, previous, pct_threshold=2.0):
    """Return trend arrow: ↑ ↓ → based on year-on-year change."""
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return "→"
    change_pct = ((current - previous) / abs(previous)) * 100
    if change_pct > pct_threshold:
        return "↑"
    elif change_pct < -pct_threshold:
        return "↓"
    return "→"


def arrow_color(arrow):
    if arrow == "↑":
        return GREEN
    elif arrow == "↓":
        return RED
    return AMBER


def safe(val, decimals=2, suffix=""):
    """Format value safely; return dash if NaN."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "—"
    try:
        if decimals == 0:
            return f"{int(round(val))}{suffix}"
        return f"{val:.{decimals}f}{suffix}"
    except Exception:
        return "—"


# ── Page-level header/footer ───────────────────────────────────────────────
def make_header_footer(canvas, doc):
    """Draw page header and footer on every page."""
    canvas.saveState()

    # Header bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 1.2 * cm, PAGE_W, 1.2 * cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(MARGIN, PAGE_H - 0.85 * cm, "Nifty 100 Financial Intelligence Platform")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.85 * cm, "Portfolio Summary Report — FY 2024")

    # Footer bar
    canvas.setFillColor(GREY_MID)
    canvas.rect(0, 0, PAGE_W, 0.8 * cm, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(MARGIN, 0.25 * cm,
        "Data source: NSE/BSE filings. For informational purposes only. Not investment advice.")
    canvas.drawRightString(PAGE_W - MARGIN, 0.25 * cm, f"Page {doc.page}")

    canvas.restoreState()


# ── Build one company's page content ──────────────────────────────────────
def build_company_page(cid, company_row, ratios_df, styles):
    """Return a list of Flowables for one company page."""
    elems = []

    company_name = str(company_row.get("company_name", cid))
    sector       = str(company_row.get("broad_sector", "N/A"))
    sub_sector   = str(company_row.get("sub_sector", ""))

    comp_ratios  = ratios_df[ratios_df["company_id"] == cid].dropna(subset=['year']).sort_values("year")
    latest       = comp_ratios.iloc[-1]  if not comp_ratios.empty else pd.Series(dtype=object)
    prev         = comp_ratios.iloc[-2]  if len(comp_ratios) >= 2 else pd.Series(dtype=object)
    prev2        = comp_ratios.iloc[-3]  if len(comp_ratios) >= 3 else pd.Series(dtype=object)

    try:
        yr_raw = latest.get("year", 2024)
        latest_year = int(float(yr_raw)) if yr_raw is not None and not (isinstance(yr_raw, float) and math.isnan(yr_raw)) else 2024
    except Exception:
        latest_year = 2024

    # ── Company header block ───────────────────────────────────────────────
    header_style = ParagraphStyle(
        "CompanyHeader",
        parent=styles["Normal"],
        fontSize=18,
        textColor=WHITE,
        fontName="Helvetica-Bold",
        leading=22,
        spaceAfter=0,
    )
    sub_style = ParagraphStyle(
        "CompanySub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#B0BEC5"),
        fontName="Helvetica",
        leading=14,
        spaceAfter=0,
    )
    ticker_style = ParagraphStyle(
        "Ticker",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.HexColor("#80DEEA"),
        fontName="Helvetica-Bold",
    )

    # Blue banner with company name
    content_w = PAGE_W - 2 * MARGIN
    banner = Table(
        [[
            Paragraph(company_name, header_style),
            Paragraph(cid, ticker_style),
        ]],
        colWidths=[content_w * 0.75, content_w * 0.25],
        rowHeights=[1.4 * cm],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",(0, 0), (0, -1), 10),
        ("RIGHTPADDING",(-1, 0), (-1, -1), 10),
        ("ALIGN",      (1, 0), (1, -1), "RIGHT"),
        ("ROUNDEDCORNERS", [6]),
    ]))
    elems.append(banner)
    elems.append(Spacer(1, 4))

    # Sector badges
    sector_row = Table(
        [[
            Paragraph(f"Sector: <b>{sector}</b>", ParagraphStyle(
                "SectorTag", parent=styles["Normal"],
                fontSize=9, textColor=NAVY,
                backColor=colors.HexColor("#E3F2FD"),
                borderPadding=(2, 6, 2, 6),
            )),
            Paragraph(f"Sub-sector: {sub_sector}" if sub_sector and sub_sector != "nan" else "",
                ParagraphStyle("SubTag", parent=styles["Normal"],
                    fontSize=9, textColor=WHITE,
                    backColor=TEAL,
                    borderPadding=(2, 6, 2, 6))),
            Paragraph(f"Data through FY{latest_year}", ParagraphStyle(
                "YearTag", parent=styles["Normal"],
                fontSize=9, textColor=colors.HexColor("#546E7A"),
            )),
        ]],
        colWidths=[content_w * 0.38, content_w * 0.38, content_w * 0.24],
    )
    sector_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elems.append(sector_row)
    elems.append(HRFlowable(width="100%", thickness=1, color=BLUE, spaceAfter=6, spaceBefore=4))

    # ── KPI Cards (2 rows × 3 cols) ────────────────────────────────────────
    kpis = [
        {
            "label": "Revenue CAGR (5Y)",
            "value": safe(latest.get("revenue_cagr_5yr"), suffix="%"),
            "arrow": trend_arrow(latest.get("revenue_cagr_5yr"), prev.get("revenue_cagr_5yr")),
            "prev":  safe(prev.get("revenue_cagr_5yr"), suffix="%"),
        },
        {
            "label": "PAT CAGR (5Y)",
            "value": safe(latest.get("pat_cagr_5yr"), suffix="%"),
            "arrow": trend_arrow(latest.get("pat_cagr_5yr"), prev.get("pat_cagr_5yr")),
            "prev":  safe(prev.get("pat_cagr_5yr"), suffix="%"),
        },
        {
            "label": "ROE",
            "value": safe(latest.get("return_on_equity_pct"), suffix="%"),
            "arrow": trend_arrow(latest.get("return_on_equity_pct"), prev.get("return_on_equity_pct")),
            "prev":  safe(prev.get("return_on_equity_pct"), suffix="%"),
        },
        {
            "label": "ROCE",
            "value": safe(latest.get("return_on_capital_employed_pct"), suffix="%"),
            "arrow": trend_arrow(latest.get("return_on_capital_employed_pct"), prev.get("return_on_capital_employed_pct")),
            "prev":  safe(prev.get("return_on_capital_employed_pct"), suffix="%"),
        },
        {
            "label": "Debt / Equity",
            "value": safe(latest.get("debt_to_equity")),
            "arrow": trend_arrow(
                latest.get("debt_to_equity"), prev.get("debt_to_equity")
            ) if pd.notna(latest.get("debt_to_equity", float("nan"))) else "→",
            # For D/E, lower is better — invert arrow colour logic
            "invert": True,
            "prev":  safe(prev.get("debt_to_equity")),
        },
        {
            "label": "Free Cash Flow",
            "value": (f"₹{latest.get('free_cash_flow_cr'):,.0f} Cr"
                      if pd.notna(latest.get("free_cash_flow_cr")) else "—"),
            "arrow": trend_arrow(latest.get("free_cash_flow_cr"), prev.get("free_cash_flow_cr")),
            "prev":  (f"₹{prev.get('free_cash_flow_cr'):,.0f} Cr"
                      if not prev.empty and pd.notna(prev.get("free_cash_flow_cr")) else "—"),
        },
    ]

    def make_kpi_card(kpi):
        arrow = kpi["arrow"]
        invert = kpi.get("invert", False)
        # Invert arrow colour for metrics where lower is better (D/E)
        if invert:
            acolor = RED if arrow == "↑" else (GREEN if arrow == "↓" else AMBER)
        else:
            acolor = arrow_color(arrow)

        # Arrow background
        arrow_bg = colors.HexColor("#E8F5E9") if acolor == GREEN else (
                   colors.HexColor("#FFEBEE") if acolor == RED else
                   colors.HexColor("#FFF8E1"))

        return Table(
            [
                [Paragraph(f'<b>{kpi["label"]}</b>',
                    ParagraphStyle("KPILabel", fontSize=8, textColor=colors.HexColor("#546E7A"),
                                   fontName="Helvetica-Bold"))],
                [Paragraph(kpi["value"],
                    ParagraphStyle("KPIVal", fontSize=20, textColor=NAVY, fontName="Helvetica-Bold",
                                   leading=24))],
                [Table([[
                    Paragraph(arrow, ParagraphStyle("Arrow", fontSize=13, textColor=acolor,
                                                     fontName="Helvetica-Bold")),
                    Paragraph(f' prev: {kpi["prev"]}',
                        ParagraphStyle("PrevVal", fontSize=7, textColor=colors.HexColor("#90A4AE"))),
                ]], colWidths=[0.6*cm, None],
                   style=[("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                          ("LEFTPADDING", (0,0), (-1,-1), 0),
                          ("RIGHTPADDING", (0,0), (-1,-1), 0),
                          ("TOPPADDING", (0,0), (-1,-1), 0),
                          ("BOTTOMPADDING", (0,0), (-1,-1), 0)])],
            ],
            colWidths=[(content_w / 3) - 4],
            style=[
                ("BACKGROUND",     (0, 0), (-1, -1), GREY_LT),
                ("BOX",            (0, 0), (-1, -1), 1, GREY_MID),
                ("LEFTPADDING",    (0, 0), (-1, -1), 8),
                ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
                ("TOPPADDING",     (0, 0), (0, 0), 8),
                ("TOPPADDING",     (0, 1), (0, 1), 2),
                ("BOTTOMPADDING",  (0, -1), (-1, -1), 8),
                ("ROUNDEDCORNERS", [6]),
            ],
        )

    # Arrange 6 cards in 2 rows of 3
    cards_row1 = [make_kpi_card(kpis[i]) for i in range(3)]
    cards_row2 = [make_kpi_card(kpis[i]) for i in range(3, 6)]
    gap = 4

    kpi_table1 = Table(
        [cards_row1],
        colWidths=[(content_w - 2*gap) / 3] * 3,
        spaceBefore=4,
        spaceAfter=gap,
    )
    kpi_table1.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), gap//2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), gap//2),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    kpi_table2 = Table(
        [cards_row2],
        colWidths=[(content_w - 2*gap) / 3] * 3,
        spaceAfter=8,
    )
    kpi_table2.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), gap//2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), gap//2),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    elems.append(kpi_table1)
    elems.append(kpi_table2)

    # ── Trend legend ──────────────────────────────────────────────────────
    legend = Paragraph(
        '<font color="#2E7D32">↑ Improved (&gt;+2%)</font>   '
        '<font color="#F57F17">→ Flat (±2%)</font>   '
        '<font color="#C62828">↓ Declined (&gt;-2%)</font>   '
        '<font color="#546E7A">  Compared to prior year</font>',
        ParagraphStyle("Legend", fontSize=7.5, textColor=colors.HexColor("#546E7A"), leading=10)
    )
    elems.append(legend)
    elems.append(HRFlowable(width="100%", thickness=0.5, color=GREY_MID, spaceBefore=6, spaceAfter=6))

    # ── 3-Year KPI trend table ─────────────────────────────────────────────
    yr_cols = []
    for row in [comp_ratios.iloc[-3] if len(comp_ratios) >= 3 else None,
                prev if not prev.empty else None,
                latest if not latest.empty else None]:
        yr_cols.append(row)

    years_label = []
    for r in yr_cols:
        if r is not None and not (isinstance(r, pd.Series) and r.empty):
            try:
                yv = r.get('year')
                if yv is not None and not (isinstance(yv, float) and math.isnan(yv)):
                    years_label.append(f"FY{int(float(yv))}")
                else:
                    years_label.append("—")
            except Exception:
                years_label.append("—")
        else:
            years_label.append("—")

    def yr_val(row, col, suffix=""):
        if row is None or (isinstance(row, pd.Series) and row.empty):
            return "—"
        v = row.get(col)
        if v is None:
            return "—"
        try:
            fv = float(v)
            if math.isnan(fv):
                return "—"
            return f"{fv:.2f}{suffix}"
        except Exception:
            return "—"

    trend_data = [
        ["Metric"] + years_label,
        ["Revenue CAGR 5Y (%)"] + [yr_val(r, "revenue_cagr_5yr", "%") for r in yr_cols],
        ["PAT CAGR 5Y (%)"]     + [yr_val(r, "pat_cagr_5yr", "%") for r in yr_cols],
        ["ROE (%)"]             + [yr_val(r, "return_on_equity_pct", "%") for r in yr_cols],
        ["ROCE (%)"]            + [yr_val(r, "return_on_capital_employed_pct", "%") for r in yr_cols],
        ["Debt / Equity"]       + [yr_val(r, "debt_to_equity") for r in yr_cols],
        ["Net Profit Margin (%)"]+ [yr_val(r, "net_profit_margin_pct", "%") for r in yr_cols],
        ["Interest Coverage"]   + [yr_val(r, "interest_coverage") for r in yr_cols],
    ]

    col_w = content_w / 4
    trend_table = Table(trend_data, colWidths=[content_w - 3 * col_w] + [col_w] * 3)
    n_data_rows = len(trend_data) - 1  # exclude header
    row_styles = []
    for ri in range(n_data_rows):
        bg = WHITE if ri % 2 == 0 else GREY_LT
        row_styles.append(("BACKGROUND", (0, ri + 1), (-1, ri + 1), bg))

    trend_style = TableStyle([
        # Header row
        ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  8),
        ("ALIGN",         (1, 0), (-1, 0),  "CENTER"),
        # Data rows
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("FONTNAME",      (0, 1), (0, -1),  "Helvetica-Bold"),
        ("FONTNAME",      (1, 1), (-1, -1), "Helvetica"),
        ("ALIGN",         (1, 1), (-1, -1), "CENTER"),
        ("GRID",          (0, 0), (-1, -1), 0.4, GREY_MID),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ] + row_styles)
    trend_table.setStyle(trend_style)
    elems.append(Paragraph("<b>3-Year KPI Trend</b>",
        ParagraphStyle("TrendHdr", fontSize=9, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=4)))
    elems.append(trend_table)
    elems.append(Spacer(1, 6))

    # ── Pros / Cons section ──────────────────────────────────────────────
    pc_path = ROOT / "output" / "pros_cons_generated.csv"
    pros_list, cons_list = [], []
    if pc_path.exists():
        try:
            pc_df = pd.read_csv(pc_path)
            comp_pc = pc_df[pc_df["company_id"] == cid]
            pros_list = comp_pc[comp_pc["type"] == "PRO"]["text"].head(4).tolist()
            cons_list = comp_pc[comp_pc["type"] == "CON"]["text"].head(4).tolist()
        except Exception:
            pass

    pro_style  = ParagraphStyle("Pro",  fontSize=8, textColor=GREEN,  leading=12, leftIndent=8)
    con_style  = ParagraphStyle("Con",  fontSize=8, textColor=RED,    leading=12, leftIndent=8)
    head_style = ParagraphStyle("PCHd", fontSize=9, textColor=WHITE,  fontName="Helvetica-Bold", leading=12)

    pros_col = ([Paragraph("<b>Strengths</b>", head_style)] +
                [Paragraph(f"+ {p}", pro_style) for p in pros_list] or
                [Paragraph("No strengths identified", ParagraphStyle("NoPC", fontSize=8, textColor=colors.grey))])
    cons_col = ([Paragraph("<b>Risks</b>", head_style)] +
                [Paragraph(f"- {c}", con_style) for c in cons_list] or
                [Paragraph("No risks identified", ParagraphStyle("NoPC", fontSize=8, textColor=colors.grey))])

    pc_table = Table(
        [[pros_col, cons_col]],
        colWidths=[content_w / 2 - 3, content_w / 2 - 3],
        spaceAfter=4,
    )
    pc_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (0, -1), colors.HexColor("#E8F5E9")),
        ("BACKGROUND",   (1, 0), (1, -1), colors.HexColor("#FFEBEE")),
        ("BACKGROUND",   (0, 0), (0, 0),  GREEN),
        ("BACKGROUND",   (1, 0), (1, 0),  RED),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("INNERGRID",    (0, 0), (-1, -1), 0, WHITE),
        ("BOX",          (0, 0), (-1, -1), 0.5, GREY_MID),
    ]))
    elems.append(Paragraph("<b>Strengths &amp; Risks</b>",
        ParagraphStyle("PCHeader", fontSize=9, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=4)))
    elems.append(pc_table)

    return elems


# ── Main builder ───────────────────────────────────────────────────────────
def build_portfolio_pdf():
    print("Loading data...")
    companies_df, ratios_df = load_data()

    # Sort alphabetically by ticker
    companies_sorted = companies_df.sort_values("id").reset_index(drop=True)
    n = len(companies_sorted)
    print(f"Building portfolio summary for {n} companies...")

    doc = BaseDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN + 1.4 * cm,  # space for header
        bottomMargin=MARGIN + 0.8 * cm,  # space for footer
        title="Nifty 100 Portfolio Summary",
        author="Nifty 100 Financial Intelligence Platform",
        subject="Sprint 5 Day 35 — Portfolio Summary",
    )

    frame = Frame(
        MARGIN, MARGIN + 0.8 * cm,
        PAGE_W - 2 * MARGIN,
        PAGE_H - 2 * MARGIN - 1.4 * cm - 0.8 * cm,
        id="main_frame",
        showBoundary=0,
    )
    doc.addPageTemplates([PageTemplate(id="company_page", frames=[frame],
                                       onPage=make_header_footer)])

    styles = getSampleStyleSheet()
    story  = []
    errors = []

    for i, row in companies_sorted.iterrows():
        cid  = row["id"]
        try:
            page_elems = build_company_page(cid, row, ratios_df, styles)
            story.extend(page_elems)
            if i < n - 1:
                story.append(PageBreak())
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            errors.append((cid, str(e)))
            print(f"  [ERROR] {cid}: {e}")
            # Still add a placeholder page so pagination is correct
            placeholder = Paragraph(
                f"<b>{cid}</b> — {row.get('company_name', '')}",
                ParagraphStyle("Err", fontSize=14, textColor=RED)
            )
            story.append(placeholder)
            story.append(Paragraph(f"Error: {str(e)[:200]}",
                ParagraphStyle("ErrMsg", fontSize=9, textColor=colors.grey)))
            if i < n - 1:
                story.append(PageBreak())

        if (i + 1) % 10 == 0 or (i + 1) == n:
            print(f"  Processed {i + 1}/{n} companies...")

    print(f"Building PDF ({n} pages)...")
    doc.build(story)

    size_kb = OUTPUT_PDF.stat().st_size // 1024
    print(f"\nPortfolio summary saved: {OUTPUT_PDF}")
    print(f"File size: {size_kb} KB")
    print(f"Total pages: {n}")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for cid, err in errors:
            print(f"  {cid}: {err}")
    else:
        print("No errors.")

    return len(errors)


if __name__ == "__main__":
    n_errors = build_portfolio_pdf()
    sys.exit(0 if n_errors == 0 else 1)
