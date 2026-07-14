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

# We need a baseline to reset to. If screener config is missing things, default them.
default_config = {
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
    if k in default_config:
        default_config[k] = v

# Initialize session state for sliders
if 'screener_params' not in st.session_state:
    st.session_state.screener_params = default_config.copy()

def apply_preset(preset_name):
    new_params = default_config.copy()
    
    # Map UI button names to config preset names
    name_map = {
        'Quality': 'Quality Compounder',
        'Value': 'Value Pick',
        'Growth': 'Growth Accelerator',
        'Dividend': 'Dividend Champion',
        'Debt Free': 'Debt-Free Blue Chip',
        'Turnaround': 'Turnaround Watch'
    }
    
    actual_name = name_map.get(preset_name)
    if actual_name and actual_name in presets:
        preset_vals = presets[actual_name]
        key_map = {
            'roe_min': 'roe',
            'roce_min': 'roce',
            'debt_equity_max': 'de',
            'fcf_min': 'fcf',
            'revenue_cagr_5y_min': 'rev_cagr',
            'pat_cagr_5y_min': 'pat_cagr',
            'pe_max': 'pe',
            'pb_max': 'pb',
            'dividend_yield_min': 'div'
        }
        for k, v in preset_vals.items():
            if k in new_params:
                new_params[k] = v
                if k in key_map:
                    st.session_state[key_map[k]] = float(v)
                
    st.session_state.screener_params = new_params

# Preset buttons
st.write("### Quick Presets")
cols = st.columns(6)
button_names = ['Quality', 'Value', 'Growth', 'Dividend', 'Debt Free', 'Turnaround']
for i, b in enumerate(button_names):
    if cols[i].button(b):
        apply_preset(b)

st.markdown("---")

col_filters, col_results = st.columns([1, 3])

with col_filters:
    st.header("Filters")
    params = st.session_state.screener_params
    
    # Define sliders for all metrics
    params['roe_min'] = st.slider("Min ROE (%)", 0.0, 50.0, float(params.get('roe_min', 0.0)), key="roe")
    params['roce_min'] = st.slider("Min ROCE (%)", 0.0, 50.0, float(params.get('roce_min', 0.0)), key="roce")
    params['debt_equity_max'] = st.slider("Max Debt/Equity", 0.0, 5.0, float(params.get('debt_equity_max', 5.0)), key="de")
    params['fcf_min'] = st.slider("Min FCF (Cr)", -1000.0, 10000.0, float(params.get('fcf_min', -1000.0)), key="fcf")
    params['revenue_cagr_5y_min'] = st.slider("Min Rev CAGR (%)", 0.0, 50.0, float(params.get('revenue_cagr_5y_min', 0.0)), key="rev_cagr")
    params['pat_cagr_5y_min'] = st.slider("Min PAT CAGR (%)", 0.0, 50.0, float(params.get('pat_cagr_5y_min', 0.0)), key="pat_cagr")
    params['pe_max'] = st.slider("Max PE", 0.0, 100.0, float(params.get('pe_max', 100.0)), key="pe")
    params['pb_max'] = st.slider("Max PB", 0.0, 20.0, float(params.get('pb_max', 20.0)), key="pb")
    params['dividend_yield_min'] = st.slider("Min Div Yield (%)", 0.0, 10.0, float(params.get('dividend_yield_min', 0.0)), key="div")
    
    st.session_state.screener_params = params

with col_results:
    st.header("Results")
    with st.spinner("Applying filters..."):
        df = get_screener_data() # Gets latest year by default
        if not df.empty:
            engine = ScreenerEngine()
            filtered_df = engine.apply_filters(df, params)
            
            if 'composite_quality_score' in filtered_df.columns:
                filtered_df = filtered_df.sort_values('composite_quality_score', ascending=False)
                
            st.write(f"**Found {len(filtered_df)} companies**")
            
            display_cols = ['company_name', 'broad_sector', 'composite_quality_score', 'roe', 'roce', 'debt_equity', 'pe', 'revenue_cagr_5yr']
            st.dataframe(filtered_df[[c for c in display_cols if c in filtered_df.columns]], use_container_width=True, hide_index=True)
            
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", data=csv, file_name="screener_results.csv", mime="text/csv")
        else:
            st.warning("No data available to screen.")
