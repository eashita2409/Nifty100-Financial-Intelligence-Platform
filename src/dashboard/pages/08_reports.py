import streamlit as st
from src.dashboard.utils.db import get_screener_data, get_companies
import pandas as pd

st.set_page_config(page_title="Reports", layout="wide")
st.title("Custom Reports")

st.write("Generate and download comprehensive data reports across all companies.")

with st.spinner("Loading report data..."):
    df = get_screener_data() # Gets latest year by default
    report_df = df.copy()

# Reorder columns
cols = ['company_name', 'company_id'] + [c for c in report_df.columns if c not in ['company_name', 'company_id', 'id']]
report_df = report_df[cols]

st.markdown(f"### Master Report ({report_df['year'].max() if not report_df.empty else 'N/A'})")

# Allow selecting columns
all_cols = report_df.columns.tolist()
default_cols = ['company_name', 'composite_quality_score', 'roe', 'roce', 'net_margin', 'pe', 'debt_equity']
selected_cols = st.multiselect("Select Columns to Include", all_cols, default=[c for c in default_cols if c in all_cols])

if selected_cols:
    final_df = report_df[selected_cols]
    st.dataframe(final_df, use_container_width=True, hide_index=True)
    
    # CSV Download
    csv = final_df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV Report",
        data=csv,
        file_name="master_report.csv",
        mime="text/csv"
    )
else:
    st.info("Please select at least one column.")
