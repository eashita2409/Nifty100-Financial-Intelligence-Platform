import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

def generate_analyst_guide():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    docs_dir = os.path.join(base_dir, 'docs')
    os.makedirs(docs_dir, exist_ok=True)
    pdf_path = os.path.join(docs_dir, 'analyst_guide.pdf')
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterTitle', parent=styles['Title'], alignment=1, fontSize=24, spaceAfter=20))
    styles.add(ParagraphStyle(name='Header1', parent=styles['Heading1'], fontSize=16, spaceAfter=10, textColor=colors.HexColor("#2C3E50")))
    styles.add(ParagraphStyle(name='Header2', parent=styles['Heading2'], fontSize=14, spaceAfter=8, textColor=colors.HexColor("#34495E")))
    styles.add(ParagraphStyle(name='CustomBodyText', parent=styles['Normal'], fontSize=11, spaceAfter=6, leading=14))
    styles.add(ParagraphStyle(name='CustomCodeText', parent=styles['Code'], fontSize=10, spaceAfter=6, backColor=colors.HexColor("#F4F6F7")))
    
    Story = []
    
    # 1. Cover Page
    Story.append(Spacer(1, 2*inch))
    Story.append(Paragraph("Nifty100 Financial Intelligence Platform", styles['CenterTitle']))
    Story.append(Paragraph("Analyst Guide & Project Documentation", styles['Title']))
    Story.append(Spacer(1, 2*inch))
    Story.append(Paragraph("Version 1.0", styles['CenterTitle']))
    Story.append(PageBreak())
    
    # 2. Table of Contents
    Story.append(Paragraph("Table of Contents", styles['Header1']))
    toc_items = [
        "1. Project Overview",
        "2. System Architecture",
        "3. Folder Structure",
        "4. Database Schema",
        "5. Data Pipeline",
        "6. Financial Ratio Engine",
        "7. Screener Engine",
        "8. Peer Comparison Engine",
        "9. Streamlit Dashboard",
        "10. Valuation Module",
        "11. Cash Flow Intelligence",
        "12. NLP Pros & Cons Engine",
        "13. FastAPI Backend",
        "14. Reports Generation",
        "15. Configuration Files",
        "16. API Usage Examples",
        "17. KPI Definitions",
        "18. Installation Guide",
        "19. Dashboard Usage",
        "20. Troubleshooting",
        "21. Future Enhancements"
    ]
    for item in toc_items:
        Story.append(Paragraph(item, styles['CustomBodyText']))
    Story.append(PageBreak())
    
    # Content Sections
    sections = [
        ("1. Project Overview", "The Nifty100 Financial Intelligence Platform is an automated analytics ecosystem that tracks, analyzes, and visualizes the fundamental health of the top 100 Indian companies. It consolidates data from multiple sources, generates actionable insights through clustering and NLP models, and presents the findings through both a Streamlit UI and a FastAPI backend."),
        ("2. System Architecture", "The platform employs a modular architecture:\n- ETL Layer: Ingests raw CSVs, normalizes headers, calculates metrics, and populates SQLite.\n- Analytics Layer: Computes 30+ KPIs, sector averages, scoring mechanisms, K-Means clustering, and Cashflow analytics.\n- Backend API: A RESTful FastAPI server exposing real-time insights.\n- Frontend: An interactive Streamlit dashboard consisting of 8 analytical views.\n- Reporting: Automated PDF generation via ReportLab."),
        ("3. Folder Structure", "Root/\n- src/ : Core logic (api, analytics, dashboard, etl, nlp, reports)\n- data/ : Database (nifty100.db) and raw/processed CSVs\n- docs/ : Documentation (analyst_guide.pdf)\n- output/ : CSVs, Excel summaries, clustering data\n- reports/ : Generated PDFs (Tearsheets, Sector, Portfolio, QA)"),
        ("4. Database Schema", "The SQLite database (`nifty100.db`) consists of tightly linked tables via foreign keys:\n- `companies`: Master ticker list and metadata.\n- `sectors`: Broad and sub-sector classifications.\n- `financial_ratios`: Computed yearly KPIs (ROE, ROCE, FCF, etc.).\n- `market_cap`, `profitandloss`, `cashflow`, `balancesheet`.\n- `prosandcons`: Inferred textual highlights."),
        ("5. Data Pipeline", "The ETL pipeline normalizes semi-structured flat files. `database_loader.py` merges disjointed datasets into standardized DataFrames, aligns years chronologically (filling gaps up to 10 years), handles missing data (NaN dropping/interpolation), and loads them securely into the SQLite relational model."),
        ("6. Financial Ratio Engine", "Computes key ratios including:\n- Profitability: ROE, ROCE, NPM, OPM.\n- Solvency: Debt-to-Equity, Interest Coverage Ratio (ICR).\n- Growth: 3, 5, and 10-year CAGRs (Revenue, PAT, EPS)."),
        ("7. Screener Engine", "A flexible querying system that ranks companies by a Composite Quality Score (combining ROE percentiles, valuation discounts, and earnings growth). Supports presets like 'Value Traps', 'High Growth', and 'Distressed'."),
        ("8. Peer Comparison Engine", "Conducts intra-sector comparisons by normalizing metrics across companies within the same `broad_sector`. Visualized via Radar charts comparing individual tickers against Sector Averages."),
        ("9. Streamlit Dashboard", "Features 8 distinct screens:\n1. Home: Market overview.\n2. Profile: Detailed company teardown.\n3. Screener: Filterable grid view.\n4. Peers: Radar charts & comparative tables.\n5. Trends: Time-series Line charts.\n6. Sectors: Aggregate KPI visualizations.\n7. Cashflow: Cash-burn/Returns classification.\n8. Reports: PDF download hub."),
        ("10. Valuation Module", "Tracks enterprise value multipliers. Specifically computes P/E ratio, P/B ratio, and EV/EBITDA. Flags companies trading below intrinsic historical averages."),
        ("11. Cash Flow Intelligence", "Calculates Free Cash Flow (CFO - CapEx), CFO Quality Score, and Capex Intensity. Categorizes companies into one of 8 structural patterns (e.g., 'Cash Cow', 'Aggressive Expansion', 'Distressed')."),
        ("12. NLP Pros & Cons Engine", "Utilizes regex-based rules to ingest raw financial parameters and output human-readable insights. Identifies high growth trajectories as 'PROs' and over-leveraged balances as 'CONs' with assigned confidence percentages."),
        ("13. FastAPI Backend", "Production-grade backend exposing 16 endpoints. Leverages Pydantic for validation, CORS for integration, and generator functions for per-request database pooling."),
        ("14. Reports Generation", "Engineered to produce dynamic multi-page PDFs using ReportLab. Generates Individual Tearsheets, Sector-wide aggregates, and Alphabetically-sorted Portfolio summaries with visual trend arrows (↑, ↓, →)."),
        ("15. Configuration Files", "All environmental paths are dynamically resolved via `Path(__file__)`. Requirements are locked in `requirements.txt`. Built against Python 3.12+."),
        ("16. API Usage Examples", "- `GET /companies`: Lists all tickers.\n- `GET /ratios/RELIANCE`: Retrieves 10-yr history.\n- `POST /recommend`: Body `{'risk_profile': 'Low'}` returns top 3 Mutual Funds."),
        ("17. KPI Definitions", "- **ROE**: Net Income / Shareholder Equity\n- **CAGR**: ((End Value / Start Value)^(1/Years)) - 1\n- **CFO Quality**: Operating Cash Flow / Net Profit\n- **FCF Conversion**: Free Cash Flow / Net Profit"),
        ("18. Installation Guide", "1. Clone repository.\n2. `python -m venv .venv`\n3. `.\\.venv\\Scripts\\activate`\n4. `pip install -r requirements.txt`"),
        ("19. Dashboard Usage", "Run `streamlit run src/dashboard/app.py`. Use the sidebar to navigate between modules. Ensure the SQLite database is populated first using `python src/etl/database_loader.py`."),
        ("20. Troubleshooting", "If the dashboard fails to load missing columns, ensure the Sprint 6 analytics modules (`clustering.py`, `cashflow_kpis.py`) were executed to populate the `output/` artifacts."),
        ("21. Future Enhancements", "Future roadmap includes:\n- Real-time API integration for stock quotes.\n- NLP-based sentiment analysis on earnings call transcripts.\n- Deep Learning models for bankruptcy prediction.")
    ]
    
    for title, text in sections:
        Story.append(Paragraph(title, styles['Header1']))
        Story.append(Paragraph(text, styles['CustomBodyText']))
        Story.append(Spacer(1, 0.2*inch))
        
    doc.build(Story)

if __name__ == "__main__":
    generate_analyst_guide()
