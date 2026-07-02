import pandas as pd
from src.analytics.kpi_engine import KPIEngine
engine = KPIEngine('data/db/nifty100.db', 'output/kpi_summary.csv')
engine.connect()
pnl = pd.read_sql_query("SELECT company_id, year, sales, net_profit, eps, opm_percentage as operating_margin FROM profitandloss", engine.conn)
ratios = pd.read_sql_query("SELECT company_id, year, debt_to_equity, interest_coverage, net_profit_margin_pct as net_margin, free_cash_flow_cr as fcf, return_on_equity_pct as roe, return_on_capital_employed_pct as roce FROM financial_ratios", engine.conn)
print(pnl['year'].dtype, ratios['year'].dtype)
merged = pnl.merge(ratios, on=['company_id', 'year'], how='outer')
print(merged[merged['company_id']=='INFY'][['year', 'roe']])
