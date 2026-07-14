import streamlit as st
import plotly.express as px
from src.dashboard.utils.db import get_cf, get_companies

st.set_page_config(page_title="Capital Allocation", layout="wide")
st.title("Capital Allocation")

companies_df = get_companies()
cf_df = get_cf()

merged_cf = cf_df.merge(companies_df[['id', 'company_name']], left_on='company_id', right_on='id')

company_options = companies_df['company_name'].tolist()
selected_company = st.selectbox("Select Company", company_options)

if selected_company:
    company_data = merged_cf[merged_cf['company_name'] == selected_company].sort_values('year')
    
    if company_data.empty:
        st.warning("No cash flow data available for this company.")
    else:
        st.markdown("### Free Cash Flow Trend")
        
        fig = px.bar(company_data, x='year', y='net_cash_flow',
                     title=f"Net Cash Flow (Cr) - {selected_company}",
                     labels={'net_cash_flow': 'NCF (Cr)', 'year': 'Year'},
                     color='net_cash_flow',
                     color_continuous_scale=px.colors.diverging.RdYlGn)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Raw Cash Flow Data")
        st.dataframe(company_data[['year', 'operating_activity', 'investing_activity', 'financing_activity', 'net_cash_flow']], use_container_width=True, hide_index=True)
