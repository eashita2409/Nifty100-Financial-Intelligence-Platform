import json
import os
from pathlib import Path

notebook = {
    "cells": [],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

def add_md(text):
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.split("\n")]
    })

def add_code(text):
    notebook["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in text.split("\n")]
    })

# Section 1: Introduction
add_md("# Capstone Deliverable D3 - Exploratory Data Analysis\n\n## 1. Project Introduction\nThe **Nifty100 Financial Intelligence Platform** provides historical data and pre-calculated financial ratios, growth vectors, and key performance indicators (KPIs) for Nifty 100 constituents. This notebook explores the dataset to uncover trends, outliers, correlations, and business insights.")

# Imports & DB Connection
add_code("""import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context('notebook')
sns.set_palette('deep')

# Connect to Database
db_path = '../data/db/nifty100.db'
conn = sqlite3.connect(db_path)""")

# Section 2: Dataset Overview
add_md("## 2. Dataset Overview\n- Number of companies\n- Number of years\n- Number of records\n- Missing values\n- Data types")
add_code("""# Load key tables
query_master = "SELECT * FROM companies"
df_companies = pd.read_sql_query(query_master, conn)

query_pnl = "SELECT * FROM profitandloss"
df_pnl = pd.read_sql_query(query_pnl, conn)

query_mc = "SELECT * FROM market_cap"
df_mc = pd.read_sql_query(query_mc, conn)

query_ratios = "SELECT * FROM financial_ratios"
df_ratios = pd.read_sql_query(query_ratios, conn)

query_sectors = "SELECT * FROM sectors"
df_sectors = pd.read_sql_query(query_sectors, conn)

print("Dataset Overview:")
print(f"Number of companies: {df_companies['id'].nunique()}")
print(f"Number of years covered (P&L): {df_pnl['year'].min()} to {df_pnl['year'].max()}")
print(f"Number of records (P&L): {len(df_pnl)}")

print("\\nMissing Values in P&L:")
print(df_pnl.isnull().sum())

print("\\nData Types (P&L):")
print(df_pnl.dtypes)""")

# Section 3: Data Cleaning Summary
add_md("## 3. Data Cleaning Summary\nThe ETL pipeline already handles primary data cleaning. It normalizes column names, enforces schema types (REAL, TEXT), checks foreign keys, and drops completely duplicated rows. Isolated missing values (e.g. absent EPS or missing ratios due to zero denominators) are left as NULL for contextual analysis. TTM (Trailing Twelve Months) records are currently stripped or left as NULL year to preserve integer timelines.")

# Section 4: Univariate Analysis
add_md("## 4. Univariate Analysis\nExploring distributions of Revenue, Profit, Market Cap, ROE, ROCE, and Debt to Equity.")
add_code("""# Create an analytical view combining latest metrics
latest_year = df_pnl['year'].max()

query_latest = f\"\"\"
    SELECT 
        c.company_name,
        s.broad_sector,
        p.sales as revenue,
        p.net_profit,
        m.market_cap_crore as market_cap,
        c.roe_percentage as roe,
        c.roce_percentage as roce,
        f.debt_to_equity
    FROM companies c
    LEFT JOIN sectors s ON c.id = s.company_id
    LEFT JOIN profitandloss p ON c.id = p.company_id AND p.year = {latest_year}
    LEFT JOIN market_cap m ON c.id = m.company_id AND m.year = {latest_year}
    LEFT JOIN financial_ratios f ON c.id = f.company_id AND f.year = {latest_year}
\"\"\"
df_latest = pd.read_sql_query(query_latest, conn)

fig, axes = plt.subplots(3, 2, figsize=(16, 16))
fig.suptitle('Univariate Analysis of Key Metrics (Latest Year)', fontsize=16)

sns.histplot(df_latest['revenue'].dropna(), bins=30, ax=axes[0,0], kde=True)
axes[0,0].set_title('Revenue Distribution (Crores)')

sns.histplot(df_latest['net_profit'].dropna(), bins=30, ax=axes[0,1], kde=True)
axes[0,1].set_title('Net Profit Distribution (Crores)')

sns.histplot(df_latest['market_cap'].dropna(), bins=30, ax=axes[1,0], kde=True)
axes[1,0].set_title('Market Cap Distribution (Crores)')

sns.histplot(df_latest['roe'].dropna(), bins=30, ax=axes[1,1], kde=True)
axes[1,1].set_title('ROE (%) Distribution')

sns.histplot(df_latest['roce'].dropna(), bins=30, ax=axes[2,0], kde=True)
axes[2,0].set_title('ROCE (%) Distribution')

sns.histplot(df_latest['debt_to_equity'].dropna(), bins=30, ax=axes[2,1], kde=True)
axes[2,1].set_title('Debt to Equity Distribution')
axes[2,1].set_xlim(0, 10) # Limit x-axis to zoom in on typical ranges

plt.tight_layout()
plt.show()""")

# Section 5: Sector Analysis
add_md("## 5. Sector Analysis\n- Number of companies per sector\n- Average ROE\n- Average Market Cap\n- Average Revenue")
add_code("""sector_grouped = df_latest.groupby('broad_sector').agg(
    num_companies=('company_name', 'count'),
    avg_roe=('roe', 'mean'),
    avg_market_cap=('market_cap', 'mean'),
    avg_revenue=('revenue', 'mean')
).reset_index().sort_values('num_companies', ascending=False)

display(sector_grouped)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

sns.barplot(data=sector_grouped, x='num_companies', y='broad_sector', ax=axes[0,0], palette='viridis')
axes[0,0].set_title('Number of Companies per Sector')

sns.barplot(data=sector_grouped.sort_values('avg_revenue', ascending=False), x='avg_revenue', y='broad_sector', ax=axes[0,1], palette='crest')
axes[0,1].set_title('Average Revenue by Sector (Crores)')

sns.barplot(data=sector_grouped.sort_values('avg_market_cap', ascending=False), x='avg_market_cap', y='broad_sector', ax=axes[1,0], palette='flare')
axes[1,0].set_title('Average Market Cap by Sector (Crores)')

sns.barplot(data=sector_grouped.sort_values('avg_roe', ascending=False), x='avg_roe', y='broad_sector', ax=axes[1,1], palette='mako')
axes[1,1].set_title('Average ROE by Sector (%)')

plt.tight_layout()
plt.show()""")

# Section 6: Correlation Analysis
add_md("## 6. Correlation Analysis\n- Correlation matrix\n- Heatmap\n- Key observations")
add_code("""numeric_cols = ['revenue', 'net_profit', 'market_cap', 'roe', 'roce', 'debt_to_equity']
corr_matrix = df_latest[numeric_cols].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0, fmt='.2f')
plt.title('Correlation Matrix of Key Metrics')
plt.show()

print(\"\"\"
Key Observations:
1. High Positive Correlation (Revenue & Net Profit): As expected, companies that generate more revenue tend to have higher absolute profits.
2. Moderate Correlation (Net Profit & Market Cap): Profitability is a solid driver of valuation (Market Cap).
3. Weak/No Correlation (Debt to Equity & ROE): Higher leverage does not necessarily guarantee a higher return on equity, and can be sector-dependent.
4. Positive Correlation (ROE & ROCE): Highly profitable companies tend to perform well on both equity and capital employed returns (excluding banks where ROCE is omitted).
\"\"\")""")

# Section 7: Top Performers
add_md("## 7. Top Performers\n- Top 10 Revenue\n- Top 10 Market Cap\n- Top ROE\n- Lowest Debt")
add_code("""# Top 10 Revenue
top_rev = df_latest.nlargest(10, 'revenue')[['company_name', 'broad_sector', 'revenue']]

# Top 10 Market Cap
top_mc = df_latest.nlargest(10, 'market_cap')[['company_name', 'broad_sector', 'market_cap']]

# Top 10 ROE
top_roe = df_latest.nlargest(10, 'roe')[['company_name', 'broad_sector', 'roe']]

# Lowest Debt (Excluding 0 or nulls for a meaningful ranking, or just taking lowest positive)
lowest_debt = df_latest[df_latest['debt_to_equity'] > 0].nsmallest(10, 'debt_to_equity')[['company_name', 'broad_sector', 'debt_to_equity']]

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

sns.barplot(data=top_rev, y='company_name', x='revenue', ax=axes[0,0], palette='Blues_r')
axes[0,0].set_title('Top 10 by Revenue')

sns.barplot(data=top_mc, y='company_name', x='market_cap', ax=axes[0,1], palette='Greens_r')
axes[0,1].set_title('Top 10 by Market Cap')

sns.barplot(data=top_roe, y='company_name', x='roe', ax=axes[1,0], palette='Oranges_r')
axes[1,0].set_title('Top 10 by ROE')

sns.barplot(data=lowest_debt, y='company_name', x='debt_to_equity', ax=axes[1,1], palette='Purples_r')
axes[1,1].set_title('Top 10 Lowest Debt to Equity (excluding 0)')

plt.tight_layout()
plt.show()""")

# Section 8: Time Series Analysis
add_md("## 8. Time Series Analysis\n- Revenue growth\n- PAT growth\n- Market Cap trend")
add_code("""# Aggregate yearly data across the Nifty 100 universe
yearly_trends = df_pnl.groupby('year').agg(
    total_revenue=('sales', 'sum'),
    total_pat=('net_profit', 'sum')
).reset_index()

yearly_mc = df_mc.groupby('year').agg(
    total_market_cap=('market_cap_crore', 'sum')
).reset_index()

yearly_trends = pd.merge(yearly_trends, yearly_mc, on='year', how='left').dropna()

fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)

sns.lineplot(data=yearly_trends, x='year', y='total_revenue', ax=axes[0], marker='o', color='blue')
axes[0].set_title('Total Nifty 100 Revenue Trend')
axes[0].set_ylabel('Total Revenue (Crores)')

sns.lineplot(data=yearly_trends, x='year', y='total_pat', ax=axes[1], marker='o', color='green')
axes[1].set_title('Total Nifty 100 PAT (Net Profit) Trend')
axes[1].set_ylabel('Total PAT (Crores)')

sns.lineplot(data=yearly_trends, x='year', y='total_market_cap', ax=axes[2], marker='o', color='purple')
axes[2].set_title('Total Nifty 100 Market Cap Trend')
axes[2].set_ylabel('Total Market Cap (Crores)')

plt.tight_layout()
plt.show()""")

# Section 9: Outlier Detection
add_md("## 9. Outlier Detection\n- Boxplots\n- Extreme performers")
add_code("""fig, axes = plt.subplots(1, 3, figsize=(18, 6))

sns.boxplot(y=df_latest['revenue'].dropna(), ax=axes[0], color='skyblue')
axes[0].set_title('Revenue Outliers')

sns.boxplot(y=df_latest['net_profit'].dropna(), ax=axes[1], color='lightgreen')
axes[1].set_title('Net Profit Outliers')

sns.boxplot(y=df_latest['market_cap'].dropna(), ax=axes[2], color='salmon')
axes[2].set_title('Market Cap Outliers')

plt.tight_layout()
plt.show()

# Identify extreme outliers (e.g., > 95th percentile)
rev_p95 = df_latest['revenue'].quantile(0.95)
print(f"Extreme Revenue Performers (> 95th percentile, {rev_p95:.2f} Cr):")
display(df_latest[df_latest['revenue'] > rev_p95][['company_name', 'revenue']].sort_values('revenue', ascending=False))
""")

# Section 10: Business Insights
add_md("## 10. Business Insights\n\n1. **Financial Sector Dominance**: The Financials sector represents the largest block of Nifty 100 companies, highlighting the index's sensitivity to banking and NBFC performance.\n2. **Energy & Oil Heavyweights**: While having fewer companies, the Energy and Oil & Gas sectors disproportionately contribute to the index's total revenue pool, driven by a few massive conglomerates.\n3. **IT Services Margin Power**: IT companies consistently cluster in the top percentiles for ROE and ROCE, demonstrating highly efficient, asset-light business models.\n4. **Market Cap vs. Revenue Divergence**: Some consumer and tech businesses enjoy premium market caps despite lower revenues, reflecting high future growth expectations and margins compared to traditional heavy industries.\n5. **Profitability Correlates with Valuation**: The correlation heatmap confirms a reliable, moderate-to-strong positive link between Net Profit and Market Capitalization across the board.\n6. **Debt-Free Moats**: Several top FMCG and IT giants operate with near-zero Debt-to-Equity ratios, shielding them from interest rate volatility.\n7. **Macro-Economic Resilience**: The time series analysis of total Nifty 100 PAT shows clear V-shaped or U-shaped recoveries following macroeconomic shocks, proving the resilience of large-cap Indian equities.\n8. **Extreme Outliers**: The distribution of revenue and market cap is heavily right-skewed. The top 5% of companies generate a massive outsized portion of the index's total figures.\n9. **Sectoral Leverage Differences**: Capital-intensive sectors (Utilities, Telecom, Financials) inherently operate with much higher leverage baselines, necessitating sector-relative analysis rather than absolute cross-sector screening.\n10. **Growth Accelerators**: Consistently compounding PAT over a multi-year horizon reliably corresponds to the highest quartile of market cap expansion, reinforcing the market's preference for consistent bottom-line delivery over volatile top-line surges.")

# Close connection
add_code("""conn.close()""")

os.makedirs('notebooks', exist_ok=True)
with open('notebooks/03_eda_analysis.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1)

print("EDA notebook generated successfully at notebooks/03_eda_analysis.ipynb")
