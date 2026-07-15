import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_synthetic_data():
    np.random.seed(42)
    os.makedirs('data/processed', exist_ok=True)
    
    # 1. Mutual Funds Data
    num_funds = 40
    fund_names = [f"Fund_{i:02d}" for i in range(1, num_funds + 1)]
    risk_grades = np.random.choice(['Low', 'Moderate', 'High'], size=num_funds, p=[0.2, 0.5, 0.3])
    
    # Fund metrics based on risk
    cagr = []
    volatility = []
    expense_ratio = []
    drawdown = []
    
    for risk in risk_grades:
        if risk == 'Low':
            cagr.append(np.random.uniform(5, 8))
            volatility.append(np.random.uniform(3, 6))
            drawdown.append(np.random.uniform(-10, -5))
            expense_ratio.append(np.random.uniform(0.1, 0.5))
        elif risk == 'Moderate':
            cagr.append(np.random.uniform(8, 12))
            volatility.append(np.random.uniform(8, 12))
            drawdown.append(np.random.uniform(-20, -10))
            expense_ratio.append(np.random.uniform(0.5, 1.0))
        else: # High
            cagr.append(np.random.uniform(12, 20))
            volatility.append(np.random.uniform(15, 25))
            drawdown.append(np.random.uniform(-40, -20))
            expense_ratio.append(np.random.uniform(1.0, 1.5))
            
    # Calculate Sharpe (assuming 5% risk free rate)
    sharpe = [(c - 5) / v for c, v in zip(cagr, volatility)]
    
    funds_df = pd.DataFrame({
        'scheme_name': fund_names,
        'risk_grade': risk_grades,
        'CAGR': cagr,
        'Volatility': volatility,
        'Expense_Ratio': expense_ratio,
        'Drawdown': drawdown,
        'Sharpe': sharpe
    })
    funds_df.to_csv('data/processed/mutual_funds.csv', index=False)
    
    # 2. Daily Returns (3 years, ~252 trading days/year)
    num_days = 252 * 3
    dates = pd.date_range(end=datetime.today(), periods=num_days, freq='B')
    
    returns_dict = {'Date': dates}
    for i, row in funds_df.iterrows():
        daily_vol = (row['Volatility'] / 100) / np.sqrt(252)
        daily_mean = (row['CAGR'] / 100) / 252
        returns_dict[row['scheme_name']] = np.random.normal(daily_mean, daily_vol, num_days)
        
    returns_df = pd.DataFrame(returns_dict)
    returns_df.to_csv('data/processed/fund_returns.csv', index=False)
    
    # 3. Investors and SIP Transactions
    num_investors = 500
    investor_ids = [f"INV_{i:04d}" for i in range(1, num_investors + 1)]
    first_transaction_years = np.random.choice([2021, 2022, 2023, 2024], size=num_investors)
    
    investors_df = pd.DataFrame({
        'investor_id': investor_ids,
        'first_transaction_year': first_transaction_years
    })
    investors_df.to_csv('data/processed/investors.csv', index=False)
    
    transactions = []
    for inv, year in zip(investor_ids, first_transaction_years):
        num_sips = np.random.randint(1, 36) # random number of sips
        # Introduce some gaps for "AT_RISK"
        gap_prob = np.random.uniform(0, 1)
        
        start_date = datetime(year, np.random.randint(1, 12), np.random.randint(1, 28))
        current_date = start_date
        
        # Select 1 to 3 favourite funds for this investor
        fav_funds = np.random.choice(fund_names, size=np.random.randint(1, 4), replace=False)
        
        for _ in range(num_sips):
            # Normal gap is ~30 days, gap > 35 is AT_RISK
            if gap_prob > 0.8:
                gap = np.random.randint(25, 60) # High chance of gap > 35
            else:
                gap = np.random.randint(28, 33) # Normal monthly SIP
                
            amount = np.random.choice([1000, 2000, 5000, 10000])
            fund = np.random.choice(fav_funds)
            
            transactions.append({
                'investor_id': inv,
                'date': current_date.strftime('%Y-%m-%d'),
                'amount': amount,
                'scheme_name': fund
            })
            current_date += timedelta(days=gap)
            if current_date > datetime.today():
                break
                
    transactions_df = pd.DataFrame(transactions)
    transactions_df.to_csv('data/processed/sip_transactions.csv', index=False)
    print("Synthetic data generated successfully.")

if __name__ == "__main__":
    generate_synthetic_data()
