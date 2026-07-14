import streamlit as st
import plotly.express as px
import pandas as pd
from src.dashboard.utils.db import get_sectors, get_ratios, get_pl, get_valuation, get_companies

st.set_page_config(page_title="Sector Analysis", layout="wide")
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
latest_pl = pl_df[pl_df['year'] == latest_year]
latest_mc = mc_df[mc_df['year'] == latest_year]

df = sectors_df.merge(companies_df[['id', 'company_name']], left_on='company_id', right_on='id')
df = df.merge(latest_ratios, on='company_id', how='left')
df = df.merge(latest_pl[['company_id', 'sales']], on='company_id', how='left')
df = df.merge(latest_mc[['company_id', 'market_cap_crore']], on='company_id', how='left')

broad_sectors = sorted(df['broad_sector'].dropna().unique().tolist())
selected_sector = st.selectbox("Select Sector", broad_sectors)

if selected_sector:
    sector_data = df[df['broad_sector'] == selected_sector].copy()
    
    st.markdown(f"### {selected_sector} - Sector Landscape ({latest_year})")
    
    if sector_data.empty:
         st.warning("No data for this sector.")
    else:
        plot_data = sector_data.dropna(subset=['sales', 'return_on_equity_pct', 'market_cap_crore'])
        
        if plot_data.empty:
            st.warning("Insufficient numeric data to plot the bubble chart.")
        else:
            # Plotly size requires strictly positive values
            plot_data = plot_data[plot_data['market_cap_crore'] > 0]
            
            fig = px.scatter(
                plot_data,
                x='sales',
                y='return_on_equity_pct',
                size='market_cap_crore',
                color='sub_sector',
                hover_name='company_name',
                log_x=True, 
                labels={
                    'sales': 'Revenue (Cr) [Log Scale]',
                    'return_on_equity_pct': 'ROE (%)',
                    'market_cap_crore': 'Market Cap',
                    'sub_sector': 'Sub Sector'
                },
                title="Revenue vs ROE (Bubble Size: Market Cap)",
                size_max=60
            )
            st.plotly_chart(fig, use_container_width=True)
            
        st.markdown("### Sub-Sector Median KPI Comparison")
        
        kpis = {
            'Median ROE (%)': 'return_on_equity_pct',
            'Median ROCE (%)': 'return_on_capital_employed_pct',
            'Median Rev CAGR (%)': 'revenue_cagr_5yr',
            'Median PAT CAGR (%)': 'pat_cagr_5yr',
            'Median D/E': 'debt_to_equity',
            'Median FCF (Cr)': 'free_cash_flow_cr'
        }
        
        medians = sector_data.groupby('sub_sector')[list(kpis.values())].median().reset_index()
        
        if medians.empty:
            st.warning("No KPI data available to compute medians.")
        else:
            cols = st.columns(3)
            for i, (kpi_name, col_name) in enumerate(kpis.items()):
                with cols[i % 3]:
                    sub_fig = px.bar(
                        medians,
                        x='sub_sector',
                        y=col_name,
                        title=kpi_name,
                        labels={col_name: '', 'sub_sector': ''},
                        color='sub_sector'
                    )
                    sub_fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
                    st.plotly_chart(sub_fig, use_container_width=True)
                    
            with st.expander("View Sub-Sector Medians Data"):
                st.dataframe(medians, hide_index=True, use_container_width=True)
