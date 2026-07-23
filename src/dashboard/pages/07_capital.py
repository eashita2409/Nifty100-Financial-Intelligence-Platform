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

from src.dashboard.utils.db import get_ratios, get_companies

st.title("Capital Allocation Analysis")

companies_df = get_companies()
ratios_df = get_ratios()

if ratios_df.empty or companies_df.empty:
    st.warning("Insufficient data for Capital Allocation Analysis.")
    st.stop()

# Get latest year per company (capital_allocation_pattern is set per year)
latest_year = ratios_df['year'].max()
latest_ratios = ratios_df[ratios_df['year'] == latest_year].copy()

# Filter to rows that have a capital allocation pattern
if 'latest_ratios' in locals() and hasattr(latest_ratios, 'columns') and 'company_id' in latest_ratios.columns: latest_ratios['company_id'] = latest_ratios['company_id'].astype(str).str.strip().str.upper()
if 'companies_df' in locals() and hasattr(companies_df, 'columns') and 'company_id' in companies_df.columns: companies_df['company_id'] = companies_df['company_id'].astype(str).str.strip().str.upper()
df = latest_ratios.merge(companies_df[['company_id', 'company_name']], on='company_id', how='left')
df_with_pattern = df.dropna(subset=['capital_allocation_pattern'])

if df_with_pattern.empty:
    # Fall back: use all years, pick last per company
    all_with_pattern = ratios_df.dropna(subset=['capital_allocation_pattern'])
    if all_with_pattern.empty:
        st.warning("No capital allocation patterns found. Please run the capital allocation pipeline (src/analytics/day32_allocation.py) first.")
        st.stop()
    df_with_pattern = (
        all_with_pattern.sort_values('year')
        .groupby('company_id')
        .tail(1)
        .merge(companies_df[['company_id', 'company_name']], on='company_id', how='left')
    )

st.markdown(f"**Showing {len(df_with_pattern)} companies** with capital allocation patterns (Year: {int(latest_year)})")

# --- Treemap ---
df_plot = df_with_pattern.copy()
df_plot['count'] = 1

fig = px.treemap(
    df_plot,
    path=[px.Constant("All Companies"), 'capital_allocation_pattern', 'company_name'],
    values='count',
    title="Capital Allocation Pattern Distribution",
    color='capital_allocation_pattern',
    color_discrete_sequence=px.colors.qualitative.Pastel
)
fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
fig.update_traces(root_color="lightgrey")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Pattern summary bar chart
pattern_counts = df_with_pattern['capital_allocation_pattern'].value_counts().reset_index()
pattern_counts.columns = ['Pattern', 'Count']
fig_bar = px.bar(
    pattern_counts, x='Pattern', y='Count',
    color='Pattern', title="Companies per Capital Allocation Pattern",
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig_bar.update_layout(showlegend=False, xaxis_title="", xaxis_tickangle=-25)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.subheader("Pattern Deep Dive")

patterns = sorted(df_with_pattern['capital_allocation_pattern'].unique().tolist())
selected_pattern = st.selectbox("Select a Pattern to view details", patterns)

if selected_pattern:
    pattern_df = df_with_pattern[df_with_pattern['capital_allocation_pattern'] == selected_pattern]

    st.markdown(f"**Pattern**: *{selected_pattern}* — {len(pattern_df)} companies")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Companies", len(pattern_df))

    median_roe = pattern_df['return_on_equity_pct'].median()
    col2.metric("Median ROE", f"{median_roe:.2f}%" if pd.notna(median_roe) else "N/A")

    median_fcf = pattern_df['free_cash_flow_cr'].median()
    col3.metric("Median FCF (INR Crore) (Cr)", f"{median_fcf:,.0f}" if pd.notna(median_fcf) else "N/A")

    median_de = pattern_df['debt_to_equity'].median()
    col4.metric("Median D/E", f"{median_de:.2f}" if pd.notna(median_de) else "N/A")

    st.markdown("#### Companies in this Pattern")
    display_cols = [
        'company_name', 'return_on_equity_pct', 'return_on_capital_employed_pct',
        'free_cash_flow_cr', 'debt_to_equity', 'revenue_cagr_5yr'
    ]
    display_df = pattern_df[[c for c in display_cols if c in pattern_df.columns]].copy()

    # Rename for readability
    rename_map = {
        'company_name': 'Company',
        'return_on_equity_pct': 'ROE (%)',
        'return_on_capital_employed_pct': 'ROCE (%)',
        'free_cash_flow_cr': 'FCF (INR Crore) (Cr)',
        'debt_to_equity': 'D/E',
        'revenue_cagr_5yr': 'Rev CAGR 5Y (%)',
    }
    display_df = display_df.rename(columns={k: v for k, v in rename_map.items() if k in display_df.columns})

    for col in display_df.select_dtypes(include='float').columns:
        display_df[col] = display_df[col].round(2)

    st.dataframe(display_df.sort_values('Company'), hide_index=True, use_container_width=True)

# --- YoY Pattern Changes ---
st.markdown("---")
st.subheader("Year-on-Year Pattern Changes")
pattern_changes_path = project_root / "output" / "pattern_changes.csv"
if pattern_changes_path.exists():
    changes_df = pd.read_csv(pattern_changes_path)
    if changes_df.empty:
        st.info("No year-on-year pattern changes detected.")
    else:
        st.write(f"**{len(changes_df)} companies changed their capital allocation pattern**")
        st.dataframe(changes_df, hide_index=True, use_container_width=True)
else:
    st.info("Pattern changes report not yet generated.")
