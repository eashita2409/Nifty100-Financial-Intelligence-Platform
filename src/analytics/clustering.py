import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import os
import matplotlib
matplotlib.use('Agg')

def run_clustering():
    os.makedirs('output', exist_ok=True)
    
    # 1. Load Data
    funds_df = pd.read_csv('data/processed/mutual_funds.csv')
    
    # Features for clustering
    features = ['CAGR', 'Sharpe', 'Volatility', 'Expense_Ratio', 'Drawdown']
    X = funds_df[features]
    
    # Normalize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Apply KMeans (Let's choose 3 clusters)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    funds_df['Cluster'] = clusters
    
    # Save output
    output_df = funds_df[['scheme_name', 'Cluster', 'risk_grade', 'Sharpe', 'CAGR']]
    output_df = output_df.rename(columns={'scheme_name': 'Scheme', 'risk_grade': 'Risk Grade'})
    output_df.to_csv('output/cluster_labels.csv', index=False)
    print("Cluster labels saved to output/cluster_labels.csv")
    
    # Visualizations
    
    # A) PCA Visualization (2D)
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=clusters, cmap='viridis', s=100, alpha=0.7)
    plt.title('PCA of Mutual Fund Clusters')
    plt.xlabel(f'Principal Component 1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')
    plt.ylabel(f'Principal Component 2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')
    
    # Add a legend for clusters
    handles, labels = scatter.legend_elements()
    plt.legend(handles, [f'Cluster {i}' for i in range(3)], title="Clusters")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('output/cluster_pca_plot.png')
    plt.close()
    print("PCA plot saved to output/cluster_pca_plot.png")
    
    # B) Cluster Scatter Plot (Volatility vs CAGR)
    plt.figure(figsize=(10, 6))
    scatter2 = plt.scatter(funds_df['Volatility'], funds_df['CAGR'], c=clusters, cmap='plasma', s=100, alpha=0.7)
    plt.title('Mutual Fund Clusters (Volatility vs CAGR)')
    plt.xlabel('Volatility (%)')
    plt.ylabel('CAGR (%)')
    
    handles2, labels2 = scatter2.legend_elements()
    plt.legend(handles2, [f'Cluster {i}' for i in range(3)], title="Clusters")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('output/cluster_scatter_plot.png')
    plt.close()
    print("Cluster scatter plot saved to output/cluster_scatter_plot.png")

if __name__ == "__main__":
    run_clustering()
