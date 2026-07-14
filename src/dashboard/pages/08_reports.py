import streamlit as st
import pandas as pd
from src.dashboard.utils.db import get_documents, get_companies

st.set_page_config(page_title="Annual Reports", layout="wide")
st.title("Annual Reports")

companies_df = get_companies()
docs_df = get_documents()

if companies_df.empty or docs_df.empty:
    st.warning("Insufficient data for Annual Reports.")
    st.stop()

company_options = companies_df['company_name'].tolist()
selected_company = st.selectbox("Search Company", company_options)

if selected_company:
    company_info = companies_df[companies_df['company_name'] == selected_company].iloc[0]
    comp_id = company_info['id']
    
    comp_docs = docs_df[docs_df['company_id'] == comp_id].sort_values('year', ascending=False)
    
    st.markdown(f"### Annual Reports for {selected_company}")
    
    if comp_docs.empty:
        st.info("No annual reports found for this company.")
    else:
        for _, row in comp_docs.iterrows():
            year = int(row['year']) if pd.notna(row['year']) else "Unknown Year"
            link = row['annual_report']
            
            with st.container():
                cols = st.columns([1, 4])
                cols[0].markdown(f"**FY {year}**")
                
                if pd.notna(link) and str(link).strip() != "":
                    cols[1].markdown(f"[View BSE Annual Report]({link})")
                else:
                    cols[1].markdown('<span style="color:white; background-color:red; padding: 2px 6px; border-radius: 4px; font-size: 14px;">Report unavailable</span>', unsafe_allow_html=True)
                
                st.markdown("---")
