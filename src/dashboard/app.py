import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Nifty 100 Financial Intelligence Platform")
st.caption("⚠️ **Note**: Market Cap and Stock Price datasets used in this platform are SIMULATED for demonstration purposes.")
st.markdown("""
Welcome to the **Nifty 100 Financial Intelligence Platform** — a comprehensive analytics dashboard
covering all 100 companies in India's premier index.

---

### Navigation Guide

| Page | Description |
|------|-------------|
| 🏠 **Home** | Universe overview, KPIs, sector distribution, quality scores |
| 🏢 **Company Profile** | Deep dive into any company: financials, ratios, pros/cons |
| 🔍 **Screener** | Filter companies by 9+ financial metrics, export CSV |
| 👥 **Peer Comparison** | Radar chart comparison within peer groups |
| 📈 **Trend Analysis** | Multi-metric historical trend charts |
| 🏭 **Sector Analysis** | Sector-level bubble charts, sub-sector KPI medians |
| 💰 **Capital Allocation** | 8-pattern capital allocation intelligence, YoY changes |
| 📄 **Reports** | Download tearsheets, sector reports, annual report links |

---
""")

st.info("👈 Use the sidebar to navigate between pages.")

col1, col2, col3 = st.columns(3)
col1.metric("Nifty 100 Companies", "92", help="Companies with full financial data in the database")
col2.metric("Data Vintage", "2012–2024", help="Historical data range available")
col3.metric("Financial Tables", "6", help="P&L, Balance Sheet, Cash Flow, Ratios, Market Cap, Documents")
