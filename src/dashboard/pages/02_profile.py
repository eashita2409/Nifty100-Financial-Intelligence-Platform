import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
from pathlib import Path

# Setup path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.dashboard.utils.db import (
    get_companies, get_ratios, get_pl, get_cf, get_sectors, get_bs
)

st.title("Company Profile")

companies_df = get_companies()
if companies_df.empty:
    st.warning("No company data available.")
    st.stop()

# Search by ticker/company
options = companies_df['company_id'] + " - " + companies_df['company_name']
selected_option = st.selectbox("Search Company", options=options, index=None, placeholder="Type to search...")

if not selected_option:
    st.info("Please select a company to view its profile.")
else:
    selected_id = selected_option.split(" - ")[0]

    # Fetch Company Data
    company_info = companies_df[companies_df['company_id'] == selected_id].iloc[0]
    sectors_df = get_sectors()
    sector_info = (
        sectors_df[sectors_df['company_id'] == selected_id].iloc[0]
        if not sectors_df.empty and selected_id in sectors_df['company_id'].values
        else None
    )

    # Company Information Card
    st.markdown("### Company Information")
    col_info1, col_info2, col_info3 = st.columns(3)
    col_info1.metric("Name", company_info['company_name'])
    col_info2.metric("Ticker", company_info['company_id'])
    col_info3.metric("Sector", sector_info['broad_sector'] if sector_info is not None else "N/A")

    st.markdown("---")

    # Fetch latest KPIs
    ratios_df = get_ratios()
    company_ratios = ratios_df[ratios_df['company_id'] == selected_id].sort_values('year')
    latest_ratios = company_ratios.iloc[-1] if not company_ratios.empty else None

    if latest_ratios is not None:
        st.markdown("### Key Performance Indicators")
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

        def safe_fmt(val, fmt="{:.2f}", suffix=""):
            if pd.isna(val):
                return "N/A"
            try:
                return fmt.format(float(val)) + suffix
            except Exception:
                return "N/A"

        kpi1.metric("ROE", safe_fmt(latest_ratios.get('return_on_equity_pct', pd.NA), suffix="%"))
        kpi2.metric("ROCE", safe_fmt(latest_ratios.get('return_on_capital_employed_pct', pd.NA), suffix="%"))
        kpi3.metric("Net Profit Margin", safe_fmt(latest_ratios.get('net_profit_margin_pct', pd.NA), suffix="%"))
        kpi4.metric("Debt / Equity", safe_fmt(latest_ratios.get('debt_to_equity', pd.NA)))
        kpi5.metric("Revenue CAGR (5y)", safe_fmt(latest_ratios.get('revenue_cagr_5yr', pd.NA), suffix="%"))
        kpi6.metric("Latest FCF", safe_fmt(latest_ratios.get('free_cash_flow_cr', pd.NA), suffix=" Cr"))

        # Capital Allocation
        cap_alloc = latest_ratios.get('capital_allocation_pattern', None)
        if cap_alloc and not pd.isna(cap_alloc):
            st.info(f"**Capital Allocation Pattern:** {cap_alloc}")
    else:
        st.warning("No ratio data available for this company.")

    st.markdown("---")

    # Charts
    pl_df = get_pl()
    company_pl = pl_df[pl_df['company_id'] == selected_id].sort_values('year')

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Revenue & Net Profit (10Y)")
        if not company_pl.empty:
            fig1 = px.bar(
                company_pl, x='year', y=['sales', 'net_profit'],
                barmode='group',
                labels={'value': 'Amount (Cr)', 'year': 'Year', 'variable': 'Metric'}
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("P&L data not available.")

    with col_chart2:
        st.subheader("ROE vs ROCE (Trend)")
        if not company_ratios.empty:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=company_ratios['year'], y=company_ratios['return_on_equity_pct'],
                mode='lines+markers', name='ROE'
            ))
            fig2.add_trace(go.Scatter(
                x=company_ratios['year'], y=company_ratios['return_on_capital_employed_pct'],
                mode='lines+markers', name='ROCE'
            ))
            fig2.update_layout(
                xaxis_title='Year', yaxis_title='Percentage (%)',
                legend=dict(orientation="h", y=-0.2)
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Ratio trend data not available.")

    st.markdown("---")

    # Cashflow Waterfall
    cf_df = get_cf()
    company_cf = cf_df[cf_df['company_id'] == selected_id].sort_values('year')
    if not company_cf.empty:
        st.subheader("Cash Flow Trend")
        cf_fig = go.Figure()
        cf_fig.add_trace(go.Bar(x=company_cf['year'], y=company_cf['operating_activity'], name='Operating', marker_color='#2ca02c'))
        cf_fig.add_trace(go.Bar(x=company_cf['year'], y=company_cf['investing_activity'], name='Investing', marker_color='#d62728'))
        cf_fig.add_trace(go.Bar(x=company_cf['year'], y=company_cf['financing_activity'], name='Financing', marker_color='#1f77b4'))
        cf_fig.update_layout(barmode='group', xaxis_title='Year', yaxis_title='Cr')
        st.plotly_chart(cf_fig, use_container_width=True)

    st.markdown("---")

    # Pros and Cons from NLP output
    st.subheader("Pros & Cons")

    try:
        pc_path = project_root / "output" / "pros_cons_generated.csv"
        if pc_path.exists():
            pc_df = pd.read_csv(pc_path)
            comp_pc = pc_df[pc_df['company_id'] == selected_id]
            pros_text = comp_pc[comp_pc['type'] == 'PRO']['text'].tolist()
            cons_text = comp_pc[comp_pc['type'] == 'CON']['text'].tolist()
        else:
            pros_text, cons_text = [], []
    except Exception:
        pros_text, cons_text = [], []

    # Supplement with ratio-based pros/cons if NLP file empty
    if not pros_text and not cons_text and latest_ratios is not None:
        roe = latest_ratios.get('return_on_equity_pct', pd.NA)
        roce = latest_ratios.get('return_on_capital_employed_pct', pd.NA)
        de = latest_ratios.get('debt_to_equity', pd.NA)
        fcf = latest_ratios.get('free_cash_flow_cr', pd.NA)

        if pd.notna(roe) and roe > 15:
            pros_text.append("Strong Return on Equity (>15%)")
        elif pd.notna(roe) and roe < 10:
            cons_text.append("Low Return on Equity (<10%)")
        if pd.notna(roce) and roce > 15:
            pros_text.append("Strong Return on Capital Employed (>15%)")
        elif pd.notna(roce) and roce < 10:
            cons_text.append("Low Return on Capital Employed (<10%)")
        if pd.notna(de) and de < 0.5:
            pros_text.append("Low Debt to Equity ratio (<0.5)")
        elif pd.notna(de) and de > 1.5:
            cons_text.append("High Debt to Equity ratio (>1.5)")
        if pd.notna(fcf) and fcf > 0:
            pros_text.append("Positive Free Cash Flow")
        elif pd.notna(fcf) and fcf < 0:
            cons_text.append("Negative Free Cash Flow")

    col_p, col_c = st.columns(2)
    with col_p:
        st.markdown("#### Pros")
        if pros_text:
            for p in pros_text:
                st.markdown(f"- ✅ {p}")
        else:
            st.write("No major pros identified.")

    with col_c:
        st.markdown("#### Cons")
        if cons_text:
            for c in cons_text:
                st.markdown(f"- ⚠️ {c}")
        else:
            st.write("No major cons identified.")
