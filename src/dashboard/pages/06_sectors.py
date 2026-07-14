import streamlit as st
import plotly.express as px
from src.dashboard.utils.db import get_sectors, get_ratios, get_companies

st.set_page_config(page_title="Sector Analysis", layout="wide")
st.title("Sector Analysis")

sectors_df = get_sectors()
ratios_df = get_ratios()

# Get latest year data
latest_year = ratios_df['year'].max()
latest_ratios = ratios_df[ratios_df['year'] == latest_year]

# Merge sectors with ratios
sector_data = sectors_df.merge(latest_ratios, on='company_id', how='inner')

if sector_data.empty:
    st.warning("No sector data available.")
else:
    st.markdown(f"### Sector Averages ({latest_year})")
    
    # Aggregate by broad_sector
    agg_df = sector_data.groupby('broad_sector').agg({
        'return_on_equity_pct': 'mean',
        'return_on_capital_employed_pct': 'mean',
        'debt_to_equity': 'mean',
        'company_id': 'count'
    }).reset_index().rename(columns={'company_id': 'company_count'})
    
    # Remove any completely null rows just in case
    agg_df = agg_df.dropna(subset=['broad_sector'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.bar(agg_df, x='broad_sector', y='return_on_equity_pct', 
                      title='Average ROE by Sector',
                      labels={'return_on_equity_pct': 'Average ROE (%)', 'broad_sector': 'Sector'})
        st.plotly_chart(fig1, use_container_width=True)
        
    with col2:
        fig2 = px.bar(agg_df, x='broad_sector', y='debt_to_equity', 
                      title='Average Debt to Equity by Sector',
                      labels={'debt_to_equity': 'Avg D/E', 'broad_sector': 'Sector'})
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### Sector Data Table")
    st.dataframe(agg_df.style.format({
        'return_on_equity_pct': '{:.2f}%',
        'return_on_capital_employed_pct': '{:.2f}%',
        'debt_to_equity': '{:.2f}'
    }), use_container_width=True, hide_index=True)
