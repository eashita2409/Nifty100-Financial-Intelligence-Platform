import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set matplotlib to use 'Agg' backend for non-GUI environments
import matplotlib
matplotlib.use('Agg')

def run_risk_analytics():
    os.makedirs('output', exist_ok=True)
    
    # 1. Load data
    funds_df = pd.read_csv('data/processed/mutual_funds.csv')
    returns_df = pd.read_csv('data/processed/fund_returns.csv', parse_dates=['Date'])
    
    # 2. Compute VaR and CVaR
    var_95 = {}
    cvar_95 = {}
    
    for col in returns_df.columns:
        if col == 'Date':
            continue
        
        returns = returns_df[col]
        
        # Historical VaR (95%) - 5th percentile
        var = np.percentile(returns.dropna(), 5)
        var_95[col] = var
        
        # CVaR (95%) - mean of returns below VaR
        cvar = returns[returns < var].mean()
        cvar_95[col] = cvar
        
    var_cvar_df = pd.DataFrame({
        'scheme_name': list(var_95.keys()),
        'historical_var_95': list(var_95.values()),
        'cvar_95': list(cvar_95.values())
    })
    
    # Merge with risk grade
    report_df = pd.merge(var_cvar_df, funds_df[['scheme_name', 'risk_grade']], on='scheme_name', how='left')
    
    # Reorder columns as requested
    report_df = report_df[['scheme_name', 'risk_grade', 'historical_var_95', 'cvar_95']]
    report_df.to_csv('output/var_cvar_report.csv', index=False)
    print("VaR/CVaR report saved to output/var_cvar_report.csv")
    
    # 3. Rolling Sharpe Ratio
    # Pick 5 representative funds (e.g. first 5)
    selected_funds = funds_df['scheme_name'].head(5).tolist()
    
    plt.figure(figsize=(12, 6))
    
    for fund in selected_funds:
        # Calculate 90-day rolling mean and std
        rolling_mean = returns_df[fund].rolling(window=90).mean()
        rolling_std = returns_df[fund].rolling(window=90).std()
        
        # Annualized rolling Sharpe
        rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(252)
        
        plt.plot(returns_df['Date'], rolling_sharpe, label=fund, linewidth=1.5)
        
    plt.title('90-Day Rolling Sharpe Ratio (5 Representative Funds)')
    plt.xlabel('Date')
    plt.ylabel('Rolling Sharpe Ratio (Annualized)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('output/rolling_sharpe_chart.png')
    plt.close()
    print("Rolling Sharpe chart saved to output/rolling_sharpe_chart.png")

if __name__ == "__main__":
    run_risk_analytics()
