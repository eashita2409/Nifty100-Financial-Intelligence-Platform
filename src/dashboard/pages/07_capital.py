import streamlit as st
import plotly.express as px
import pandas as pd
from src.dashboard.utils.db import get_ratios, get_companies

st.set_page_config(page_title="Capital Allocation", layout="wide")
st.title("Capital Allocation Analysis")

companies_df = get_companies()
ratios_df = get_ratios()

if ratios_df.empty or companies_df.empty:
    st.warning("Insufficient data for Capital Allocation Analysis.")
    st.stop()

latest_year = ratios_df['year'].max()
latest_ratios = ratios_df[ratios_df['year'] == latest_year]

df = latest_ratios.merge(companies_df[['id', 'company_name']], left_on='company_id', right_on='id')
df = df.dropna(subset=['capital_allocation_pattern'])

if df.empty:
    st.warning("No capital allocation patterns found in the dataset.")
    st.stop()

df['count'] = 1
fig = px.treemap(
    df,
    path=[px.Constant("All Companies"), 'capital_allocation_pattern', 'company_name'],
    values='count',
    title="Capital Allocation Pattern Distribution",
    color='capital_allocation_pattern'
)
fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
fig.update_traces(root_color="lightgrey")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("Pattern Deep Dive")

patterns = sorted(df['capital_allocation_pattern'].unique().tolist())
selected_pattern = st.selectbox("Select a Pattern to view details", patterns)

if selected_pattern:
    pattern_df = df[df['capital_allocation_pattern'] == selected_pattern]
    
    st.markdown(f"**Pattern Summary**: An overview of financial metrics for the '{selected_pattern}' cluster.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Number of Companies", len(pattern_df))
    
    median_roe = pattern_df['return_on_equity_pct'].median()
    col2.metric("Median ROE", f"{median_roe:.2f}%" if pd.notna(median_roe) else "N/A")
    
    median_fcf = pattern_df['free_cash_flow_cr'].median()
    col3.metric("Median FCF (Cr)", f"{median_fcf:,.2f}" if pd.notna(median_fcf) else "N/A")
    
    st.markdown("#### Companies in this Pattern")
    display_cols = ['company_name', 'return_on_equity_pct', 'return_on_capital_employed_pct', 'free_cash_flow_cr', 'debt_to_equity']
    
    st.dataframe(
        pattern_df[[c for c in display_cols if c in pattern_df.columns]].sort_values('company_name'), 
        hide_index=True, 
        use_container_width=True
    )
