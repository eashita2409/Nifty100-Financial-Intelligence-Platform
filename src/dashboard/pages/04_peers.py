import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

# Setup path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.dashboard.utils.db import get_peers, get_peer_percentiles, get_companies, get_screener_data

st.title("Peer Comparison")

peers_df = get_peers()
percentiles_df = get_peer_percentiles()
companies_df = get_companies()

if peers_df.empty or percentiles_df.empty:
    st.warning("Peer comparison data is not available.")
    st.stop()

# Get unique peer groups
unique_groups = peers_df['peer_group_name'].dropna().unique().tolist()
selected_group = st.selectbox("Select Peer Group", options=unique_groups)

if not selected_group:
    st.info("Please select a peer group.")
else:
    # Filter companies in this group
    group_companies = peers_df[peers_df['peer_group_name'] == selected_group]

    # Fetch latest percentiles (filter by latest year)
    latest_year = percentiles_df['year'].max()
    percentiles_latest = percentiles_df[percentiles_df['year'] == latest_year]

    # Merge to get company names and percentiles
    group_data = group_companies.merge(companies_df, left_on='company_id', right_on='id', how='inner')
    group_data = group_data.merge(percentiles_latest, on='company_id', how='left')

    # The percentiles columns
    radar_metrics = {
        'roe_rank': 'ROE',
        'roce_rank': 'ROCE',
        'npm_rank': 'Net Profit Margin',
        'debt_equity_rank': 'Debt to Equity',
        'fcf_rank': 'Free Cash Flow',
        'revenue_cagr_rank': 'Rev CAGR (5Y)'
    }

    st.markdown("### Radar Comparison (Percentiles)")
    # Calculate peer average percentiles
    peer_avg = group_data[list(radar_metrics.keys())].mean().to_dict()

    # Allow selecting a specific company to compare against average
    company_options = group_data['company_name'].tolist()
    selected_company_name = st.selectbox("Select Company to Compare", options=company_options)

    if not selected_company_name:
        st.info("Please select a company to compare.")
    else:
        selected_company_data = group_data[group_data['company_name'] == selected_company_name].iloc[0]

        fig = go.Figure()
        # Add average trace
        fig.add_trace(go.Scatterpolar(
            r=[peer_avg[k] for k in radar_metrics.keys()] + [peer_avg[list(radar_metrics.keys())[0]]],
            theta=list(radar_metrics.values()) + [list(radar_metrics.values())[0]],
            fill='toself',
            name='Peer Average',
            line_color='gray'
        ))

        # Add selected company trace
        fig.add_trace(go.Scatterpolar(
            r=[selected_company_data[k] if pd.notna(selected_company_data[k]) else 0 for k in radar_metrics.keys()] + [selected_company_data[list(radar_metrics.keys())[0]] if pd.notna(selected_company_data[list(radar_metrics.keys())[0]]) else 0],
            theta=list(radar_metrics.values()) + [list(radar_metrics.values())[0]],
            fill='toself',
            name=selected_company_name,
            line_color='blue'
        ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### KPI Comparison Table")

    # Get absolute data for KPI comparison table
    with st.spinner("Fetching absolute metrics..."):
        df_raw = get_screener_data() # Gets latest year by default
        
    group_raw_data = group_data[['company_id', 'company_name', 'is_benchmark']].merge(df_raw, on='company_id', how='inner')

    if not group_raw_data.empty:
        display_cols = ['company_name', 'is_benchmark', 'composite_quality_score', 'roe', 'roce', 'net_margin', 'debt_equity', 'revenue_cagr_5yr', 'pe']
        
        # Clean up dataframe for display
        display_df = group_raw_data[[c for c in display_cols if c in group_raw_data.columns]].copy()
        
        # Streamlit dataframe styling for benchmark
        def highlight_benchmark(row):
            # We need to return an array of styles of the same length as the row
            if row.get('is_benchmark', 0) == 1:
                return ['background-color: rgba(255, 215, 0, 0.2)'] * len(row)
            return [''] * len(row)

        st.dataframe(display_df.style.apply(highlight_benchmark, axis=1), use_container_width=True, hide_index=True)
    else:
        st.info("Raw KPI data not available for this peer group.")
