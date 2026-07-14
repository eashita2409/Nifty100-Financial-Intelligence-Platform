import streamlit as st
import plotly.express as px
from src.dashboard.utils.db import get_companies, get_ratios, get_pl

st.set_page_config(page_title="Trend Analysis", layout="wide")
st.title("Trend Analysis")

companies_df = get_companies()
ratios_df = get_ratios()
pl_df = get_pl()

# Merge for plotting
merged_ratios = ratios_df.merge(companies_df[['id', 'company_name']], left_on='company_id', right_on='id')
merged_pl = pl_df.merge(companies_df[['id', 'company_name']], left_on='company_id', right_on='id')

st.sidebar.header("Trend Parameters")

metrics = {
    'ROE (%)': ('return_on_equity_pct', merged_ratios),
    'ROCE (%)': ('return_on_capital_employed_pct', merged_ratios),
    'Net Profit Margin (%)': ('net_profit_margin_pct', merged_ratios),
    'Sales (Cr)': ('sales', merged_pl),
    'Net Profit (Cr)': ('net_profit', merged_pl)
}

selected_metric = st.sidebar.selectbox("Select Metric", list(metrics.keys()))
metric_col, metric_df = metrics[selected_metric]

# Multiselect for companies
company_options = companies_df['company_name'].tolist()
# Default to top 3 for demo
default_companies = company_options[:3] if len(company_options) >= 3 else company_options
selected_companies = st.sidebar.multiselect("Select Companies", company_options, default=default_companies)

if not selected_companies:
    st.info("Please select at least one company to view trends.")
else:
    plot_df = metric_df[metric_df['company_name'].isin(selected_companies)].sort_values('year')
    if plot_df.empty:
        st.warning("No data available for the selected companies.")
    else:
        fig = px.line(plot_df, x='year', y=metric_col, color='company_name', markers=True,
                      labels={metric_col: selected_metric, 'year': 'Year', 'company_name': 'Company'},
                      title=f"{selected_metric} Trend Over Time")
        st.plotly_chart(fig, use_container_width=True)
