import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import seaborn as sns
import os
import sqlite3
import matplotlib
matplotlib.use('Agg')

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

def assign_archetypes(profile_df):
    names = {}
    used_names = set()
    
    for c_id in profile_df.index:
        p = profile_df.loc[c_id]
        
        # Simple heuristic assignment
        if p['return_on_equity_pct'] >= profile_df['return_on_equity_pct'].median() and p['revenue_cagr_5yr'] >= profile_df['revenue_cagr_5yr'].median():
            name = "High Growth Leaders"
        elif p['debt_to_equity'] >= profile_df['debt_to_equity'].quantile(0.75):
            name = "Highly Leveraged"
        elif p['fcf_cagr_5yr'] >= profile_df['fcf_cagr_5yr'].median() and p['return_on_equity_pct'] >= profile_df['return_on_equity_pct'].median():
            name = "Cash Generators"
        elif p['operating_profit_margin_pct'] <= profile_df['operating_profit_margin_pct'].quantile(0.25):
            name = "Low Margin Laggards"
        elif p['return_on_equity_pct'] < profile_df['return_on_equity_pct'].median() and p['revenue_cagr_5yr'] < profile_df['revenue_cagr_5yr'].median():
            name = "Struggling Decline"
        else:
            name = "Steady Performers"
            
        # Ensure uniqueness
        original_name = name
        counter = 1
        while name in used_names:
            name = f"{original_name} {counter}"
            counter += 1
        used_names.add(name)
        names[c_id] = name
        
    return names

def run_clustering():
    os.makedirs('output', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    # 1. Load Data
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
    conn.close()
    
    # Normalize company_id
    df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()
    df = df.dropna(subset=['year'])
    
    # Get latest year for each company
    latest = df.sort_values('year').groupby('company_id').tail(1).copy()
    history = df.set_index(['company_id', 'year'])['free_cash_flow_cr'].to_dict()
    
    # Compute FCF CAGR 5yr
    fcf_cagrs = []
    for _, row in latest.iterrows():
        cid = row['company_id']
        curr_year = row['year']
        hist_year = curr_year - 5
        val = calculate_cagr(history.get((cid, hist_year)), row['free_cash_flow_cr'], 5)
        fcf_cagrs.append(val)
    latest['fcf_cagr_5yr'] = fcf_cagrs
    
    features = ['return_on_equity_pct', 'debt_to_equity', 'revenue_cagr_5yr', 'fcf_cagr_5yr', 'operating_profit_margin_pct']
    
    # Impute missing using sector median
    for feat in features:
        latest[feat] = latest.groupby('sector')[feat].transform(lambda x: x.fillna(x.median()))
        latest[feat] = latest[feat].fillna(latest[feat].median()) # Fallback if sector median is NaN
        
    X = latest[features].copy()
    
    # 5. Apply StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 6. Generate elbow_plot.png
    inertias = []
    K_range = range(2, 11)
    for k in K_range:
        kmeans_temp = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans_temp.fit(X_scaled)
        inertias.append(kmeans_temp.inertia_)
        
    plt.figure(figsize=(8, 5))
    plt.plot(K_range, inertias, marker='o', linestyle='--')
    plt.title('Elbow Plot for K-Means Clustering')
    plt.xlabel('Number of Clusters (k)')
    plt.ylabel('Inertia')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('reports/elbow_plot.png')
    plt.close()
    
    # Apply KMeans (n_clusters=5, random_state=42)
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    # Distances from centroid
    distances = kmeans.transform(X_scaled)
    dist_to_centroid = [distances[i, c] for i, c in enumerate(clusters)]
    
    latest['cluster_id'] = clusters
    latest['distance_from_centroid'] = dist_to_centroid
    
    # Profile clusters
    profile_mean = latest.groupby('cluster_id')[features].mean()
    cluster_names = assign_archetypes(profile_mean)
    
    latest['cluster_name'] = latest['cluster_id'].map(cluster_names)
    
    # 7. Generate output/cluster_labels.csv
    output_df = latest[['company_id', 'cluster_id', 'cluster_name', 'distance_from_centroid']]
    output_df.to_csv('output/cluster_labels.csv', index=False)
    
    # 10. Profile the 5 clusters using mean and median values (portfolio_stats.csv)
    portfolio_stats = latest.groupby('cluster_id')[features].agg(['mean', 'median'])
    portfolio_stats.to_csv('output/portfolio_stats.csv')
    
    # Outlier report
    threshold = latest['distance_from_centroid'].quantile(0.9)
    outliers = latest[latest['distance_from_centroid'] > threshold]
    outliers.to_csv('output/outlier_report.csv', index=False)
    
    # Correlation heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(latest[features].corr(), annot=True, cmap='coolwarm', center=0, fmt=".2f")
    plt.title('Feature Correlation Heatmap')
    plt.tight_layout()
    plt.savefig('reports/correlation_heatmap.png')
    plt.close()

if __name__ == "__main__":
    run_clustering()
