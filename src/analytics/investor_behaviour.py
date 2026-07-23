import pandas as pd
import numpy as np
import os

def run_investor_behaviour_analytics():
    os.makedirs('output', exist_ok=True)
    
    # 1. Load Data
    investors_df = pd.read_csv('data/processed/investors.csv')
    transactions_df = pd.read_csv('data/processed/sip_transactions.csv', parse_dates=['date'])
    
    # Merge transactions with investor cohort info
    if 'pd' in locals() and hasattr(pd, 'columns') and 'company_id' in pd.columns: pd['company_id'] = pd['company_id'].astype(str).str.strip().str.upper()
    if 'transactions_df' in locals() and hasattr(transactions_df, 'columns') and 'company_id' in transactions_df.columns: transactions_df['company_id'] = transactions_df['company_id'].astype(str).str.strip().str.upper()
    df = pd.merge(transactions_df, investors_df, on='investor_id', how='left')
    
    # ---------------------------------------------------------
    # Cohort Analysis
    # ---------------------------------------------------------
    cohorts = []
    
    for year, group in df.groupby('first_transaction_year'):
        investor_count = group['investor_id'].nunique()
        avg_sip_amount = group['amount'].mean()
        total_invested = group['amount'].sum()
        
        # Favorite fund for cohort (most frequent scheme_name)
        favourite_fund = group['scheme_name'].mode()[0] if not group.empty else "N/A"
        
        # Average corpus (total invested / investor count)
        avg_corpus = total_invested / investor_count if investor_count > 0 else 0
        
        cohorts.append({
            'cohort_year': year,
            'investor_count': investor_count,
            'avg_sip_amount': round(avg_sip_amount, 2),
            'total_invested': round(total_invested, 2),
            'favourite_fund': favourite_fund,
            'avg_corpus': round(avg_corpus, 2)
        })
        
    cohorts_df = pd.DataFrame(cohorts)
    cohorts_df.to_csv('output/cohort_analysis.csv', index=False)
    print("Cohort Analysis saved to output/cohort_analysis.csv")
    
    # ---------------------------------------------------------
    # SIP Continuity Analysis
    # ---------------------------------------------------------
    # Group by investor to find those with >= 6 transactions
    tx_counts = df.groupby('investor_id').size()
    eligible_investors = tx_counts[tx_counts >= 6].index
    
    continuity_data = []
    
    for inv_id in eligible_investors:
        inv_tx = df[df['investor_id'] == inv_id].sort_values('date')
        
        # Calculate date gaps in days
        inv_tx['gap_days'] = inv_tx['date'].diff().dt.days
        
        avg_gap = inv_tx['gap_days'].mean()
        max_gap = inv_tx['gap_days'].max()
        
        # Flag AT_RISK if average gap > 35 days (as per requirement, could also be max gap, going with mean > 35 or any gap > 35)
        # Requirement: "Flag: gap > 35 days as AT_RISK"
        # We will check if the maximum gap or average gap is > 35. Let's use max gap or any gap > 35 to flag.
        at_risk = True if (inv_tx['gap_days'] > 35).any() else False
        
        continuity_data.append({
            'investor_id': inv_id,
            'transaction_count': len(inv_tx),
            'avg_gap_days': round(avg_gap, 2) if pd.notna(avg_gap) else 0,
            'max_gap_days': max_gap if pd.notna(max_gap) else 0,
            'status': 'AT_RISK' if at_risk else 'HEALTHY'
        })
        
    continuity_df = pd.DataFrame(continuity_data)
    continuity_df.to_csv('output/sip_continuity.csv', index=False)
    
    # Summary statistics
    status_counts = continuity_df['status'].value_counts().to_dict()
    print("SIP Continuity Analysis saved to output/sip_continuity.csv")
    print(f"SIP Continuity Summary: {status_counts}")

if __name__ == "__main__":
    run_investor_behaviour_analytics()
