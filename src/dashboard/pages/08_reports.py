import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Setup path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.dashboard.utils.db import get_documents, get_companies, get_sectors

st.title("Reports & Documents")

companies_df = get_companies()
docs_df = get_documents()
sectors_df = get_sectors()

if companies_df.empty:
    st.warning("Company data not available.")
    st.stop()

# Add sector info for filtering
if not sectors_df.empty:
    companies_enriched = companies_df.merge(sectors_df, on='company_id', how='left')
    broad_sectors = ['All'] + sorted(companies_enriched['broad_sector'].dropna().unique().tolist())
else:
    companies_enriched = companies_df.copy()
    broad_sectors = ['All']

col_filter1, col_filter2 = st.columns([1, 2])

with col_filter1:
    selected_sector_filter = st.selectbox("Filter by Sector", broad_sectors, key="report_sector_filter")

with col_filter2:
    if selected_sector_filter == 'All':
        filtered_companies = companies_enriched
    else:
        filtered_companies = companies_enriched[companies_enriched['broad_sector'] == selected_sector_filter]

    company_options = filtered_companies['company_name'].tolist()
    selected_company = st.selectbox("Search Company", company_options, key="report_company_select")

st.markdown("---")

# --- Tearsheet Download Section ---
tearsheet_dir = project_root / "reports" / "tearsheets"
sector_dir = project_root / "reports" / "sector"

col_tear, col_sector = st.columns(2)

with col_tear:
    st.subheader("Company Tearsheets")
    if tearsheet_dir.exists():
        pdfs = list(tearsheet_dir.glob("*.pdf"))
        st.write(f"**{len(pdfs)} tearsheets available**")

        if selected_company:
            company_id = companies_enriched[companies_enriched['company_name'] == selected_company]['company_id'].values
            if len(company_id) > 0:
                cid = company_id[0]
                # Try both naming conventions
                tearsheet_path = tearsheet_dir / f"{cid}.pdf"
                if not tearsheet_path.exists():
                    tearsheet_path = tearsheet_dir / f"{cid}_tearsheet.pdf"
                if tearsheet_path.exists():
                    with open(tearsheet_path, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        label=f"Download {selected_company} Tearsheet ({len(pdf_bytes)//1024} KB)",
                        data=pdf_bytes,
                        file_name=f"{cid}_tearsheet.pdf",
                        mime="application/pdf",
                        key="tearsheet_download"
                    )
                else:
                    st.info(f"Tearsheet not yet generated for {selected_company}.")
    else:
        st.info("Tearsheets directory not found. Please run the tearsheet generator.")

with col_sector:
    st.subheader("Sector Reports")
    if sector_dir.exists():
        sector_pdfs = list(sector_dir.glob("*.pdf"))
        st.write(f"**{len(sector_pdfs)} sector reports available**")

        if sector_pdfs:
            # Show display names (replace underscores with spaces for readability)
            stem_to_path = {p.stem: p for p in sector_pdfs}
            display_names = sorted([p.stem.replace('_', ' ') for p in sector_pdfs])
            selected_sector_report = st.selectbox(
                "Select Sector Report",
                options=display_names,
                key="sector_report_select"
            )
            if selected_sector_report:
                # Match: try underscore version first, then exact stem
                file_stem_underscore = selected_sector_report.replace(' ', '_')
                match_path = stem_to_path.get(file_stem_underscore) or stem_to_path.get(selected_sector_report)
                if not match_path:
                    # Fuzzy match
                    for stem, path in stem_to_path.items():
                        if stem.replace('_', ' ').lower() == selected_sector_report.lower():
                            match_path = path
                            break
                if match_path:
                    with open(match_path, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        label=f"Download {selected_sector_report} Report ({len(pdf_bytes)//1024} KB)",
                        data=pdf_bytes,
                        file_name=f"{match_path.stem}.pdf",
                        mime="application/pdf",
                        key="sector_download"
                    )
                else:
                    st.warning(f"Could not find PDF for '{selected_sector_report}'.")
    else:
        st.info("Sector reports directory not found. Please run the batch report generator.")

st.markdown("---")

# --- Annual Reports ---
st.subheader("Annual Reports")

if docs_df.empty:
    st.info("No annual report data available in the database.")
elif not selected_company:
    st.info("Please select a company above to see annual reports.")
else:
    company_info = companies_enriched[companies_enriched['company_name'] == selected_company]
    if company_info.empty:
        st.warning("Company not found.")
    else:
        comp_id = company_info.iloc[0]['company_id']
        comp_docs = docs_df[docs_df['company_id'] == comp_id].copy()

        # Sort by year descending, handle NaN years
        comp_docs['year'] = pd.to_numeric(comp_docs['year'], errors='coerce')
        comp_docs = comp_docs.sort_values('year', ascending=False)

        st.markdown(f"#### Annual Reports — {selected_company}")

        if comp_docs.empty:
            st.info("No annual reports found for this company.")
        else:
            available = comp_docs.dropna(subset=['annual_report'])
            available = available[available['annual_report'].astype(str).str.strip() != '']
            unavailable = comp_docs[~comp_docs.index.isin(available.index)]

            if not available.empty:
                for _, row in available.iterrows():
                    year_label = f"FY {int(row['year'])}" if pd.notna(row['year']) else "Year Unknown"
                    link = str(row['annual_report']).strip()
                    cols = st.columns([1, 4])
                    cols[0].markdown(f"**{year_label}**")
                    cols[1].markdown(f"[View BSE Annual Report]({link})", unsafe_allow_html=False)

            if not unavailable.empty:
                with st.expander(f"{len(unavailable)} years with unavailable reports"):
                    for _, row in unavailable.iterrows():
                        year_label = f"FY {int(row['year'])}" if pd.notna(row['year']) else "Year Unknown"
                        st.markdown(f"- {year_label}: Report not available")
