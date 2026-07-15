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

from src.dashboard.utils.db import get_screener_data, get_sectors, get_ratios

st.title("Nifty 100 Analytics — Home")

# Sidebar
st.sidebar.header("Filters")
selected_year = st.sidebar.selectbox(
    "Select Year",
    options=[2024, 2023, 2022, 2021, 2020, 2019],
    index=0
)

# Fetch data for the selected year
with st.spinner("Fetching data..."):
    df = get_screener_data(target_year=selected_year)

if df.empty:
    st.warning("No data available for the selected year.")
else:
    # Calculate KPIs
    avg_roe = df['roe'].mean() if 'roe' in df.columns else None
    median_pe = df['pe'].median() if 'pe' in df.columns else None
    median_de = df['debt_equity'].median() if 'debt_equity' in df.columns else None
    total_companies = len(df)
    median_rev_cagr = df['revenue_cagr_5yr'].median() if 'revenue_cagr_5yr' in df.columns else None
    debt_free_count = int(df['debt_free_label'].sum()) if 'debt_free_label' in df.columns else 0

    # Render KPIs
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Avg ROE", f"{avg_roe:.2f}%" if avg_roe is not None and pd.notna(avg_roe) else "N/A")
    col2.metric("Median PE", f"{median_pe:.2f}" if median_pe is not None and pd.notna(median_pe) else "N/A")
    col3.metric("Median D/E", f"{median_de:.2f}" if median_de is not None and pd.notna(median_de) else "N/A")
    col4.metric("Total Companies", f"{total_companies}")
    col5.metric("Median Rev CAGR", f"{median_rev_cagr:.2f}%" if median_rev_cagr is not None and pd.notna(median_rev_cagr) else "N/A")
    col6.metric("Debt Free", f"{debt_free_count}")

    st.markdown("---")

    col_chart, col_table = st.columns([1, 1])

    with col_chart:
        st.subheader("Sector Distribution")
        if 'broad_sector' in df.columns:
            sector_counts = df['broad_sector'].value_counts().reset_index()
            sector_counts.columns = ['Sector', 'Count']
            fig = px.pie(sector_counts, names='Sector', values='Count', hole=0.4)
            fig.update_layout(legend=dict(orientation="v", x=1.05))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sector information not available.")

    with col_table:
        st.subheader("Top 10 Companies by Quality Score")
        if 'composite_quality_score' in df.columns:
            top_10 = df.sort_values('composite_quality_score', ascending=False).head(10)
            display_cols = ['company_name', 'broad_sector', 'composite_quality_score', 'roe', 'pe']
            display_df = top_10[[c for c in display_cols if c in top_10.columns]].copy()
            for col in display_df.select_dtypes(include='float').columns:
                display_df[col] = display_df[col].round(2)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Quality score not calculated.")

    st.markdown("---")

    # Quality Score Distribution
    if 'composite_quality_score' in df.columns:
        st.subheader("Quality Score Distribution")
        fig_hist = px.histogram(
            df, x='composite_quality_score', nbins=20,
            title="Distribution of Composite Quality Scores",
            labels={'composite_quality_score': 'Quality Score'},
            color_discrete_sequence=['#1f77b4']
        )
        fig_hist.update_layout(bargap=0.1)
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")

    # ROE vs PE scatter
    if 'roe' in df.columns and 'pe' in df.columns:
        st.subheader("ROE vs PE — Universe View")
        scatter_data = df.dropna(subset=['roe', 'pe']).copy()
        scatter_data = scatter_data[(scatter_data['pe'] > 0) & (scatter_data['pe'] < 200)]
        if not scatter_data.empty:
            color_col = 'broad_sector' if 'broad_sector' in scatter_data.columns else 'company_name'
            fig_scatter = px.scatter(
                scatter_data,
                x='pe', y='roe',
                color=color_col,
                hover_name='company_name' if 'company_name' in scatter_data.columns else None,
                labels={'pe': 'P/E Ratio', 'roe': 'ROE (%)', 'broad_sector': 'Sector'},
                title=f"ROE vs PE for all Nifty 100 Companies ({selected_year})"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
