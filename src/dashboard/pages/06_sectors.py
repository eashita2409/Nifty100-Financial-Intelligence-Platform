import streamlit as st
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path

# Setup path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.dashboard.utils.db import get_sectors, get_ratios, get_pl, get_valuation, get_companies

st.title("Sector Analysis")

sectors_df = get_sectors()
ratios_df = get_ratios()
pl_df = get_pl()
mc_df = get_valuation()
companies_df = get_companies()

if ratios_df.empty or sectors_df.empty:
    st.warning("Insufficient data for Sector Analysis.")
    st.stop()

latest_year = ratios_df['year'].max()

latest_ratios = ratios_df[ratios_df['year'] == latest_year]
latest_pl = pl_df[pl_df['year'] == latest_year] if not pl_df.empty else pd.DataFrame()
latest_mc = mc_df[mc_df['year'] == latest_year] if not mc_df.empty else pd.DataFrame()

# Build combined sector dataframe
df = sectors_df.merge(companies_df[['id', 'company_name']], left_on='company_id', right_on='id')
df = df.merge(latest_ratios, on='company_id', how='left')

if not latest_pl.empty:
    df = df.merge(latest_pl[['company_id', 'sales']], on='company_id', how='left')
else:
    df['sales'] = None

if not latest_mc.empty and 'market_cap_crore' in latest_mc.columns:
    df = df.merge(latest_mc[['company_id', 'market_cap_crore']], on='company_id', how='left')
else:
    df['market_cap_crore'] = None

broad_sectors = sorted(df['broad_sector'].dropna().unique().tolist())
selected_sector = st.selectbox("Select Sector", broad_sectors)

if selected_sector:
    sector_data = df[df['broad_sector'] == selected_sector].copy()

    st.markdown(f"### {selected_sector} — Sector Landscape ({int(latest_year)})")

    if sector_data.empty:
        st.warning("No data for this sector.")
    else:
        # Summary KPIs
        kc1, kc2, kc3, kc4 = st.columns(4)
        kc1.metric("Companies", len(sector_data))
        med_roe = sector_data['return_on_equity_pct'].median()
        kc2.metric("Median ROE", f"{med_roe:.1f}%" if pd.notna(med_roe) else "N/A")
        med_roce = sector_data['return_on_capital_employed_pct'].median()
        kc3.metric("Median ROCE", f"{med_roce:.1f}%" if pd.notna(med_roce) else "N/A")
        med_de = sector_data['debt_to_equity'].median()
        kc4.metric("Median D/E", f"{med_de:.2f}" if pd.notna(med_de) else "N/A")

        st.markdown("---")

        # Bubble chart: Revenue vs ROE, size = Market Cap
        plot_data = sector_data.dropna(subset=['sales', 'return_on_equity_pct'])
        if 'market_cap_crore' in plot_data.columns:
            plot_data = plot_data.dropna(subset=['market_cap_crore'])
            plot_data = plot_data[plot_data['market_cap_crore'] > 0]
            size_col = 'market_cap_crore'
        else:
            plot_data = plot_data.copy()
            plot_data['_size'] = 10
            size_col = '_size'

        if plot_data.empty:
            st.warning("Insufficient numeric data to plot the bubble chart.")
        else:
            color_col = 'sub_sector' if 'sub_sector' in plot_data.columns else 'company_name'
            fig = px.scatter(
                plot_data,
                x='sales',
                y='return_on_equity_pct',
                size=size_col,
                color=color_col,
                hover_name='company_name',
                log_x=True,
                labels={
                    'sales': 'Revenue (Cr) [Log Scale]',
                    'return_on_equity_pct': 'ROE (%)',
                    'market_cap_crore': 'Market Cap (Cr)',
                    'sub_sector': 'Sub Sector'
                },
                title="Revenue vs ROE (Bubble Size = Market Cap)",
                size_max=60
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Sub-Sector Median KPIs")

        kpis = {
            'Median ROE (%)': 'return_on_equity_pct',
            'Median ROCE (%)': 'return_on_capital_employed_pct',
            'Median Rev CAGR (%)': 'revenue_cagr_5yr',
            'Median PAT CAGR (%)': 'pat_cagr_5yr',
            'Median D/E': 'debt_to_equity',
            'Median FCF (Cr)': 'free_cash_flow_cr'
        }

        group_col = 'sub_sector' if 'sub_sector' in sector_data.columns else 'broad_sector'
        avail_kpi_cols = [c for c in kpis.values() if c in sector_data.columns]
        medians = sector_data.groupby(group_col)[avail_kpi_cols].median().reset_index()

        if medians.empty:
            st.warning("No KPI data available to compute medians.")
        else:
            chart_kpis = [(name, col) for name, col in kpis.items() if col in medians.columns]
            cols_per_row = 3
            rows = [chart_kpis[i:i+cols_per_row] for i in range(0, len(chart_kpis), cols_per_row)]
            for row in rows:
                grid = st.columns(cols_per_row)
                for j, (kpi_name, col_name) in enumerate(row):
                    with grid[j]:
                        sub_fig = px.bar(
                            medians,
                            x=group_col,
                            y=col_name,
                            title=kpi_name,
                            color=group_col
                        )
                        sub_fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
                        st.plotly_chart(sub_fig, use_container_width=True)

            with st.expander("View Sub-Sector Medians Data"):
                st.dataframe(medians, hide_index=True, use_container_width=True)

        # Company list table
        st.markdown("### All Companies in Sector")
        comp_cols = ['company_name', 'return_on_equity_pct', 'return_on_capital_employed_pct',
                     'debt_to_equity', 'revenue_cagr_5yr', 'free_cash_flow_cr']
        comp_display = sector_data[[c for c in comp_cols if c in sector_data.columns]].copy()
        comp_display.columns = [c.replace('return_on_equity_pct', 'ROE (%)').replace(
            'return_on_capital_employed_pct', 'ROCE (%)').replace(
            'debt_to_equity', 'D/E').replace('revenue_cagr_5yr', 'Rev CAGR 5Y (%)').replace(
            'free_cash_flow_cr', 'FCF (Cr)').replace('company_name', 'Company') for c in comp_display.columns]
        st.dataframe(comp_display, hide_index=True, use_container_width=True)
