import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from math import pi

# 1. Load data
df = pd.read_excel('output/screener_output.xlsx')

# Define metrics to plot
metrics = {
    'ROE': 'roe',
    'ROCE': 'roce',
    'NPM': 'net_margin',
    'Debt/Equity': 'debt_equity',
    'FCF': 'fcf',
    'Revenue CAGR': 'revenue_growth',
    'PAT CAGR': 'pat_growth',
    'Composite Score': 'composite_quality_score'
}

# 2. Get Sectors for peer average
conn = sqlite3.connect('data/db/nifty100.db')
sectors_df = pd.read_sql_query('SELECT company_id, broad_sector FROM sectors', conn)
conn.close()

df = df.merge(sectors_df, on='company_id', how='left')

# Impute broad_sector if missing
df['broad_sector'] = df['broad_sector'].fillna('Unknown')

# 3. Normalize data (0 to 1) for the radar chart
# We use min-max scaling for all metrics
df_scaled = df.copy()
for label, col in metrics.items():
    min_val = df[col].min()
    max_val = df[col].max()
    if pd.isna(min_val) or pd.isna(max_val) or max_val - min_val == 0:
        df_scaled[col] = 0
    else:
        df_scaled[col] = (df[col] - min_val) / (max_val - min_val)

# 4. Calculate peer averages for scaled metrics
peer_avg = df_scaled.groupby('broad_sector')[[col for col in metrics.values()]].mean().reset_index()

# 5. Generate Radar Charts
output_dir = 'reports/radar_charts'
os.makedirs(output_dir, exist_ok=True)

categories = list(metrics.keys())
N = len(categories)

# What will be the angle of each axis in the plot?
angles = [n / float(N) * 2 * pi for n in range(N)]
angles += angles[:1] # close the loop

def plot_radar(company_id, company_data, peer_data, company_name):
    # Initialise the spider plot
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    # Draw one axe per variable + add labels
    plt.xticks(angles[:-1], categories, color='grey', size=8)
    
    # Draw ylabels
    ax.set_rlabel_position(0)
    plt.yticks([0.25, 0.5, 0.75], ["0.25","0.50","0.75"], color="grey", size=7)
    plt.ylim(0, 1)
    
    # Plot company data
    values = [0 if pd.isna(company_data[col]) else company_data[col] for col in metrics.values()]
    values += values[:1] # close the loop
    ax.plot(angles, values, linewidth=1, linestyle='solid', label=company_name)
    ax.fill(angles, values, 'b', alpha=0.1)
    
    # Plot peer average
    peer_values = [0 if pd.isna(peer_data[col]) else peer_data[col] for col in metrics.values()]
    peer_values += peer_values[:1]
    ax.plot(angles, peer_values, linewidth=1, linestyle='dashed', label='Peer Average')
    
    # Add legend
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.title(f"{company_name} Radar Chart", size=11, color='black', y=1.1)
    
    # The prompt explicitly asked to "Save as companyname_radar.png". 
    # But often company_name has spaces, maybe company_id is safer?
    # I will follow instruction "Save as companyname_radar.png" literally, but substituting spaces with underscores might be good, or just using raw company_name. 
    # I will use the company_id or clean company_name to be safe. "companyname" usually implies the ID or ticker.
    # The prompt says: "Save as companyname_radar.png". Let's use `company_id`.
    plt.savefig(os.path.join(output_dir, f"{company_id}_radar.png"), bbox_inches='tight')
    plt.close()

for idx, row in df_scaled.iterrows():
    company_id = row['company_id']
    company_name = row['company_name']
    sector = row['broad_sector']
    
    # Get peer average
    peer_data = peer_avg[peer_avg['broad_sector'] == sector].iloc[0]
    
    # Plot
    plot_radar(company_id, row, peer_data, company_name)

print("Generated radar charts for all companies.")
