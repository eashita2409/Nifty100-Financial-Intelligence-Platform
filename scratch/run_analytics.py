import sys
from pathlib import Path

db_path = str(Path("data/db/nifty100.db").absolute())

from src.analytics.ratios import populate_profitability_ratios
from src.analytics.leverage import populate_leverage_ratios
from src.analytics.cagr import populate_cagr_metrics
from src.analytics.cashflow_kpis import populate_cashflow_kpis

print(f"Using DB path: {db_path}")
populate_profitability_ratios(db_path)
populate_leverage_ratios(db_path)
populate_cagr_metrics(db_path)
populate_cashflow_kpis(db_path)

print("Ratio engine fully executed and populated database.")
