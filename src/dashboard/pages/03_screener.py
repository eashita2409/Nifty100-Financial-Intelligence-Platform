import streamlit as st
import pandas as pd
import yaml
import sys
from pathlib import Path

# Setup path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.dashboard.utils.db import get_screener_data
from src.screener.engine import ScreenerEngine

st.title("Stock Screener")

# Load config
config_path = project_root / "config" / "screener_config.yaml"
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
except FileNotFoundError:
    config_data = {'screener': {}, 'presets': {}}

presets = config_data.get('presets', {})

DEFAULT_PARAMS = {
    'roe_min': 0.0,
    'roce_min': 0.0,
    'debt_equity_max': 5.0,
    'fcf_min': -1000.0,
    'revenue_cagr_5y_min': 0.0,
    'pat_cagr_5y_min': 0.0,
    'pe_max': 100.0,
    'pb_max': 20.0,
    'dividend_yield_min': 0.0
}

# Override with yaml screener config
for k, v in config_data.get('screener', {}).items():
    if k in DEFAULT_PARAMS:
        DEFAULT_PARAMS[k] = v

# Initialize session state
if 'screener_params' not in st.session_state:
    st.session_state.screener_params = DEFAULT_PARAMS.copy()

PRESET_NAME_MAP = {
    'Quality': 'Quality Compounder',
    'Value': 'Value Pick',
    'Growth': 'Growth Accelerator',
    'Dividend': 'Dividend Champion',
    'Debt Free': 'Debt-Free Blue Chip',
    'Turnaround': 'Turnaround Watch'
}

# Preset buttons
st.write("### Quick Presets")
cols_btn = st.columns(6)
button_names = ['Quality', 'Value', 'Growth', 'Dividend', 'Debt Free', 'Turnaround']
for i, b in enumerate(button_names):
    if cols_btn[i].button(b, key=f"preset_{b}"):
        actual_name = PRESET_NAME_MAP.get(b)
        if actual_name and actual_name in presets:
            new_params = DEFAULT_PARAMS.copy()
            for k, v in presets[actual_name].items():
                if k in new_params:
                    new_params[k] = v
            st.session_state.screener_params = new_params
            st.rerun()

st.markdown("---")

col_filters, col_results = st.columns([1, 3])

with col_filters:
    st.header("Filters")
    p = st.session_state.screener_params

    roe_min = st.slider("Min ROE (%)", 0.0, 50.0, float(p.get('roe_min', 0.0)), key="sl_roe")
    roce_min = st.slider("Min ROCE (%)", 0.0, 50.0, float(p.get('roce_min', 0.0)), key="sl_roce")
    debt_equity_max = st.slider("Max Debt/Equity", 0.0, 5.0, float(p.get('debt_equity_max', 5.0)), key="sl_de")
    fcf_min = st.slider("Min FCF (Cr)", -1000.0, 10000.0, float(p.get('fcf_min', -1000.0)), key="sl_fcf")
    revenue_cagr_5y_min = st.slider("Min Rev CAGR (%)", 0.0, 50.0, float(p.get('revenue_cagr_5y_min', 0.0)), key="sl_rev_cagr")
    pat_cagr_5y_min = st.slider("Min PAT CAGR (%)", 0.0, 50.0, float(p.get('pat_cagr_5y_min', 0.0)), key="sl_pat_cagr")
    pe_max = st.slider("Max PE", 0.0, 100.0, float(p.get('pe_max', 100.0)), key="sl_pe")
    pb_max = st.slider("Max PB", 0.0, 20.0, float(p.get('pb_max', 20.0)), key="sl_pb")
    dividend_yield_min = st.slider("Min Div Yield (%)", 0.0, 10.0, float(p.get('dividend_yield_min', 0.0)), key="sl_div")

    # Update session state params from sliders
    st.session_state.screener_params = {
        'roe_min': roe_min,
        'roce_min': roce_min,
        'debt_equity_max': debt_equity_max,
        'fcf_min': fcf_min,
        'revenue_cagr_5y_min': revenue_cagr_5y_min,
        'pat_cagr_5y_min': pat_cagr_5y_min,
        'pe_max': pe_max,
        'pb_max': pb_max,
        'dividend_yield_min': dividend_yield_min,
    }

with col_results:
    st.header("Results")
    with st.spinner("Applying filters..."):
        df = get_screener_data()
        if not df.empty:
            engine = ScreenerEngine()
            filter_params = st.session_state.screener_params
            filtered_df = engine.apply_filters(df, filter_params)

            if 'composite_quality_score' in filtered_df.columns:
                filtered_df = filtered_df.sort_values('composite_quality_score', ascending=False)

            st.write(f"**Found {len(filtered_df)} companies**")

            display_cols = [
                'company_name', 'broad_sector', 'composite_quality_score',
                'roe', 'roce', 'debt_equity', 'pe', 'revenue_cagr_5yr'
            ]
            st.dataframe(
                filtered_df[[c for c in display_cols if c in filtered_df.columns]],
                use_container_width=True,
                hide_index=True
            )

            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download CSV",
                data=csv,
                file_name="screener_results.csv",
                mime="text/csv",
                key="screener_download"
            )
        else:
            st.warning("No data available to screen.")
