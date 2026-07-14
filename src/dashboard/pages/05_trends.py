import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.dashboard.utils.db import get_companies, get_ratios, get_pl

st.set_page_config(page_title="Trend Analysis", layout="wide")
st.title("Trend Analysis")

companies_df = get_companies()
ratios_df = get_ratios()
pl_df = get_pl()

company_options = companies_df['company_name'].tolist()
selected_company = st.selectbox("Search Company", company_options)

if selected_company:
    company_info = companies_df[companies_df['company_name'] == selected_company].iloc[0]
    comp_id = company_info['id']
    
    comp_ratios = ratios_df[ratios_df['company_id'] == comp_id]
    comp_pl = pl_df[pl_df['company_id'] == comp_id]
    
    if comp_ratios.empty and comp_pl.empty:
        st.warning("No trend data available for this company.")
    else:
        trend_df = comp_pl.merge(comp_ratios, on=['company_id', 'year'], how='outer').sort_values('year')
        
        years_available = len(trend_df['year'].dropna().unique())
        st.info(f"Data available for {years_available} years")
        
        metric_map = {
            'Revenue': 'sales',
            'Net Profit': 'net_profit',
            'ROE': 'return_on_equity_pct',
            'ROCE': 'return_on_capital_employed_pct',
            'OPM': 'opm_percentage',
            'Revenue CAGR': 'revenue_cagr_5yr',
            'PAT CAGR': 'pat_cagr_5yr',
            'FCF': 'free_cash_flow_cr',
            'Debt to Equity': 'debt_to_equity',
            'Asset Turnover': 'asset_turnover'
        }
        
        selected_metrics = st.multiselect(
            "Select Metrics (Max 3)", 
            list(metric_map.keys()), 
            default=['Revenue', 'Net Profit'],
            max_selections=3
        )
        
        if selected_metrics:
            fig = go.Figure()
            
            for i, metric in enumerate(selected_metrics):
                col = metric_map[metric]
                if col in trend_df.columns:
                    metric_data = trend_df[['year', col]].dropna()
                    
                    if not metric_data.empty:
                        metric_data['yoy'] = metric_data[col].pct_change() * 100
                        
                        # Only show text annotations on the chart for the first metric to avoid severe clutter
                        # The others will have it in the hover tooltip
                        mode = 'lines+markers+text' if i == 0 else 'lines+markers'
                        
                        fig.add_trace(go.Scatter(
                            x=metric_data['year'],
                            y=metric_data[col],
                            mode=mode,
                            name=metric,
                            text=[f"{yoy:+.1f}%" if pd.notna(yoy) else "" for yoy in metric_data['yoy']],
                            textposition="top center",
                            hovertemplate=f"<b>{metric}</b>: %{{y}}<br>YoY: %{{text}}<extra></extra>"
                        ))
            
            fig.update_layout(
                title=f"{selected_company} - Trend Analysis",
                xaxis_title="Year",
                yaxis_title="Value",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("View Raw Data"):
                cols_to_show = ['year'] + [metric_map[m] for m in selected_metrics if metric_map[m] in trend_df.columns]
                st.dataframe(trend_df[cols_to_show].set_index('year'), use_container_width=True)
        else:
            st.info("Please select at least one metric to display the chart.")
