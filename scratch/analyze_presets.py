import sqlite3
import pandas as pd
import numpy as np
from src.screener.engine import ScreenerEngine

engine = ScreenerEngine()
db_path = 'data/db/nifty100.db'
df = engine.fetch_data(db_path)
df = engine.calculate_composite_quality_score(df)

print(f"Total companies in database: {len(df)}")

# Define proposed presets and count matches
presets = {
    "Quality Compounder": {
        # High profitability, clean balance sheet, strong CAGRs
        'roe_min': 15.0,
        'roce_min': 15.0,
        'debt_equity_max': 1.0,
        'revenue_cagr_5y_min': 10.0
    },
    "Value Pick": {
        # Lower valuation (PE/PB), but still profitable (not a value trap)
        'pe_max': 30.0,
        'pb_max': 5.0,
        'roe_min': 10.0,
        'net_profit_min': 100.0
    },
    "Growth Accelerator": {
        # Strong revenue and PAT growth
        'revenue_cagr_5y_min': 12.0,
        'pat_cagr_5y_min': 12.0,
        'roe_min': 12.0
    },
    "Dividend Champion": {
        # Steady cash flow and good dividend yield
        'dividend_yield_min': 1.5,
        'roe_min': 10.0,
        'fcf_min': 0.0
    },
    "Debt-Free Blue Chip": {
        # Zero or negligible debt, large cap, highly profitable
        'debt_equity_max': 0.1,
        'market_cap_min': 10000.0,
        'roe_min': 15.0
    },
    "Turnaround Watch": {
        # Historically lower/moderate ROE, but positive growth and positive cash flows
        'fcf_min': 300.0, 
        'sales_min': 5000.0, 
        'roe_min': 10.0,
        'debt_equity_max': 1.5
    }
}

for name, config in presets.items():
    res = engine.apply_filters(df, config)
    print(f"{name}: {len(res)} matches (Target: 5 - 50)")
    if len(res) > 0:
        print("  Sample:", res['company_id'].head(5).tolist())
