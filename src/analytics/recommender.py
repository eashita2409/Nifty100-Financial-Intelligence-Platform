import pandas as pd
import numpy as np
import os

def recommend_funds(risk_profile: str, top_n: int = 3):
    """
    Recommend Top N schemes for a given risk profile ('Low', 'Moderate', 'High')
    using Highest Sharpe ratio.
    Output columns: Scheme, Sharpe, CAGR, Volatility, Risk Grade.
    """
    funds_df = pd.read_csv('data/processed/mutual_funds.csv')
    
    # Filter by risk grade
    filtered = funds_df[funds_df['risk_grade'].str.lower() == risk_profile.lower()]
    
    if filtered.empty:
        return pd.DataFrame()
        
    # Sort by Sharpe Ratio descending
    recommended = filtered.sort_values(by='Sharpe', ascending=False).head(top_n)
    
    # Select and rename columns as requested
    result = recommended[['scheme_name', 'Sharpe', 'CAGR', 'Volatility', 'risk_grade']]
    result = result.rename(columns={'scheme_name': 'Scheme', 'risk_grade': 'Risk Grade'})
    
    return result

def compute_portfolio_concentration(weights):
    """
    Compute Herfindahl-Hirschman Index (HHI) for portfolio concentration.
    HHI = sum(w^2) where w are the weights (0 to 1).
    Classify as Diversified, Moderate, or Highly Concentrated.
    """
    hhi = np.sum(np.square(weights))
    
    if hhi < 0.15:
        classification = "Diversified"
    elif hhi <= 0.25:
        classification = "Moderate"
    else:
        classification = "Highly Concentrated"
        
    return hhi, classification

def test_recommender():
    os.makedirs('output', exist_ok=True)
    
    print("--- Fund Recommendation Engine ---")
    for profile in ['Low', 'Moderate', 'High']:
        recs = recommend_funds(profile)
        print(f"\nRecommendations for {profile} Risk:")
        print(recs.to_string(index=False))
        recs.to_csv(f'output/recommendations_{profile.lower()}.csv', index=False)
        
    print("\n--- Portfolio Concentration ---")
    # Simulate an equity portfolio with 5 funds, random weights summing to 1
    np.random.seed(42)
    raw_weights = np.random.rand(5)
    weights = raw_weights / np.sum(raw_weights)
    
    hhi, cls = compute_portfolio_concentration(weights)
    print(f"Simulated Portfolio Weights: {[round(w, 3) for w in weights]}")
    print(f"HHI: {hhi:.4f}")
    print(f"Classification: {cls}")

if __name__ == "__main__":
    test_recommender()
