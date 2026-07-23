import pandas as pd
import sqlite3
import numpy as np

def calculate_cagr(start_val, end_val, years):
    if years <= 0 or start_val is None or end_val is None or pd.isna(start_val) or pd.isna(end_val):
        return np.nan
    if start_val == 0:
        return np.nan
    if start_val > 0 and end_val > 0:
        return round((((end_val / start_val) ** (1 / years)) - 1) * 100, 2)
    if start_val > 0 and end_val == 0:
        return -100.0
    return np.nan

conn = sqlite3.connect('data/db/nifty100.db')
query = """
SELECT 
    fr.company_id,
    s.broad_sector as sector,
    fr.year,
    fr.return_on_equity_pct,
    fr.debt_to_equity,
    fr.revenue_cagr_5yr,
    fr.operating_profit_margin_pct,
    fr.free_cash_flow_cr
FROM financial_ratios fr
LEFT JOIN sectors s ON fr.company_id = s.company_id
ORDER BY fr.company_id, fr.year
"""
df = pd.read_sql_query(query, conn)
df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()

# get the latest year for each company (ignoring NaN years)
df = df.dropna(subset=['year'])
latest = df.sort_values('year').groupby('company_id').tail(1).copy()
print("Total unique companies latest:", len(latest))

# compute fcf_cagr_5yr
history = df.set_index(['company_id', 'year'])['free_cash_flow_cr'].to_dict()

fcf_cagrs = []
for _, row in latest.iterrows():
    cid = row['company_id']
    curr_year = row['year']
    hist_year = curr_year - 5
    curr_val = row['free_cash_flow_cr']
    hist_val = history.get((cid, hist_year))
    
    val = calculate_cagr(hist_val, curr_val, 5)
    fcf_cagrs.append(val)

latest['fcf_cagr_5yr'] = fcf_cagrs

print("Missing fcf_cagr_5yr before imputation:", latest['fcf_cagr_5yr'].isna().sum())
print("Missing before impute:", latest[['return_on_equity_pct', 'debt_to_equity', 'revenue_cagr_5yr', 'operating_profit_margin_pct']].isna().sum())

# keep only required columns
features = ['return_on_equity_pct', 'debt_to_equity', 'revenue_cagr_5yr', 'fcf_cagr_5yr', 'operating_profit_margin_pct']
metrics_df = latest[['company_id', 'sector'] + features].copy()

# impute missing
for feat in features:
    metrics_df[feat] = metrics_df.groupby('sector')[feat].transform(lambda x: x.fillna(x.median()))
    metrics_df[feat] = metrics_df[feat].fillna(metrics_df[feat].median()) # fallback if sector median is NaN

print("Missing after imputation:", metrics_df[features].isna().sum())
print("Total companies after:", len(metrics_df))
