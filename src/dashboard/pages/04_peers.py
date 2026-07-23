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

if peers_df.empty:
    st.warning("Peer group data is not available. Please run the peer analysis pipeline first.")
    st.stop()

if percentiles_df.empty:
    st.warning("Peer percentile data is not available. Please run the peer analysis pipeline first.")
    st.stop()

# Get unique peer groups
unique_groups = peers_df['peer_group_name'].dropna().unique().tolist()
selected_group = st.selectbox("Select Peer Group", options=unique_groups)

if not selected_group:
    st.info("Please select a peer group.")
else:
    # Filter companies in this group
    group_companies = peers_df[peers_df['peer_group_name'] == selected_group]

    # Fetch latest percentiles
    latest_year = percentiles_df['year'].max()
    percentiles_latest = percentiles_df[percentiles_df['year'] == latest_year]

    # Merge to get company names and percentiles
    if 'group_companies' in locals() and hasattr(group_companies, 'columns') and 'company_id' in group_companies.columns: group_companies['company_id'] = group_companies['company_id'].astype(str).str.strip().str.upper()
    if 'companies_df' in locals() and hasattr(companies_df, 'columns') and 'company_id' in companies_df.columns: companies_df['company_id'] = companies_df['company_id'].astype(str).str.strip().str.upper()
    group_data = group_companies.merge(companies_df, on='company_id', how='inner')
    if 'group_data' in locals() and hasattr(group_data, 'columns') and 'company_id' in group_data.columns: group_data['company_id'] = group_data['company_id'].astype(str).str.strip().str.upper()
    if 'percentiles_latest' in locals() and hasattr(percentiles_latest, 'columns') and 'company_id' in percentiles_latest.columns: percentiles_latest['company_id'] = percentiles_latest['company_id'].astype(str).str.strip().str.upper()
    group_data = group_data.merge(percentiles_latest, on='company_id', how='left')

    # Radar metrics available
    ALL_RADAR_METRICS = {
        'roe_rank': 'ROE',
        'roce_rank': 'ROCE',
        'npm_rank': 'Net Profit Margin',
        'debt_equity_rank': 'Debt/Equity',
        'fcf_rank': 'Free Cash Flow (INR Crore)',
        'revenue_cagr_rank': 'Rev CAGR (5Y)'
    }

    # Only use columns that exist
    radar_metrics = {k: v for k, v in ALL_RADAR_METRICS.items() if k in group_data.columns}

    if not radar_metrics:
        st.warning("No percentile rank columns found for this peer group.")
    else:
        st.markdown(f"### Peer Group: **{selected_group}** ({len(group_data)} companies)")
        st.markdown("### Radar Comparison (Percentiles)")

        # Compute peer averages – fill NaN with 50 (median rank)
        peer_avg = group_data[list(radar_metrics.keys())].fillna(50).mean().to_dict()

        # Allow selecting a specific company to compare against average
        company_options = group_data['company_name'].tolist()
        selected_company_name = st.selectbox("Select Company to Compare", options=company_options)

        if selected_company_name:
            sel_row = group_data[group_data['company_name'] == selected_company_name]
            if sel_row.empty:
                st.warning("Company data not found in this peer group.")
            else:
                selected_company_data = sel_row.iloc[0]
                keys = list(radar_metrics.keys())
                labels = list(radar_metrics.values())

                fig = go.Figure()
                # Peer Average trace
                avg_r = [peer_avg[k] for k in keys] + [peer_avg[keys[0]]]
                fig.add_trace(go.Scatterpolar(
                    r=avg_r,
                    theta=labels + [labels[0]],
                    fill='toself',
                    name='Peer Average',
                    line_color='gray',
                    opacity=0.6
                ))

                # Selected company trace
                comp_r = [
                    float(selected_company_data[k]) if pd.notna(selected_company_data.get(k)) else 50
                    for k in keys
                ] + [
                    float(selected_company_data[keys[0]]) if pd.notna(selected_company_data.get(keys[0])) else 50
                ]
                fig.add_trace(go.Scatterpolar(
                    r=comp_r,
                    theta=labels + [labels[0]],
                    fill='toself',
                    name=selected_company_name,
                    line_color='#1f77b4'
                ))

                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=True,
                    height=450
                )
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### KPI Comparison Table")

    with st.spinner("Fetching absolute metrics..."):
        df_raw = get_screener_data()

    if not df_raw.empty:
        # Merge raw KPIs for companies in this peer group
        group_raw_data = group_data[['company_id', 'company_name', 'is_benchmark']].merge(
            df_raw, on='company_id', how='inner'
        )

        if not group_raw_data.empty:
            display_cols = [
                'company_name', 'is_benchmark', 'composite_quality_score',
                'roe', 'roce', 'net_margin', 'debt_equity', 'revenue_cagr_5yr', 'pe'
            ]
            display_df = group_raw_data[[c for c in display_cols if c in group_raw_data.columns]].copy()

            # Round numeric columns
            for col in display_df.select_dtypes(include='float').columns:
                display_df[col] = display_df[col].round(2)

            def highlight_benchmark(row):
                is_bm = row.get('is_benchmark', 0)
                if is_bm == 1:
                    return ['background-color: rgba(255, 215, 0, 0.2)'] * len(row)
                return [''] * len(row)

            st.dataframe(
                display_df.style.apply(highlight_benchmark, axis=1),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Raw KPI data not available for this peer group.")
    else:
        st.info("Screener data not loaded.")
