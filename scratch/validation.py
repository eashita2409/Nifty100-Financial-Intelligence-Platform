import pandas as pd
import os
import sys

def validate():
    fails = []
    
    # 6. Generate reports/elbow_plot.png
    if not os.path.exists('reports/elbow_plot.png'):
        fails.append('reports/elbow_plot.png missing')
        
    # 7. Generate output/cluster_labels.csv
    if not os.path.exists('output/cluster_labels.csv'):
        fails.append('output/cluster_labels.csv missing')
    else:
        df = pd.read_csv('output/cluster_labels.csv')
        cols = set(df.columns)
        req_cols = {'company_id', 'cluster_id', 'cluster_name', 'distance_from_centroid'}
        if not req_cols.issubset(cols):
            fails.append(f'cluster_labels.csv missing cols: {req_cols - cols}')
        
        # 8. exactly 5 clusters 0-4
        clusters = set(df['cluster_id'].unique())
        if clusters != {0, 1, 2, 3, 4}:
            fails.append(f'cluster_id not exactly 0-4. Found: {clusters}')
            
        # 9, 13. exactly 92 unique companies, no duplicates, no missing
        if len(df) != 92:
            fails.append(f'Total rows != 92 (found {len(df)})')
        if df['company_id'].nunique() != 92:
            fails.append('Not 92 unique companies')
        if df['cluster_id'].isna().sum() > 0:
            fails.append('Missing cluster_id found')
            
    # 12. Generate reports/correlation_heatmap.png, output/outlier_report.csv, output/portfolio_stats.csv
    if not os.path.exists('reports/correlation_heatmap.png'):
        fails.append('reports/correlation_heatmap.png missing')
    if not os.path.exists('output/outlier_report.csv'):
        fails.append('output/outlier_report.csv missing')
    if not os.path.exists('output/portfolio_stats.csv'):
        fails.append('output/portfolio_stats.csv missing')

    if fails:
        for f in fails:
            print(f"FAIL: {f}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)

if __name__ == '__main__':
    validate()
