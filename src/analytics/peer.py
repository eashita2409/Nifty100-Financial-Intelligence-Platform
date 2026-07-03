import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Any

def init_db_schema(conn: sqlite3.Connection):
    """Initializes the database schema for the peer_percentiles table."""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS peer_percentiles (
        company_id TEXT,
        year REAL,
        roe_rank REAL,
        roce_rank REAL,
        npm_rank REAL,
        debt_equity_rank REAL,
        fcf_rank REAL,
        revenue_cagr_rank REAL,
        pat_cagr_rank REAL,
        eps_cagr_rank REAL,
        icr_rank REAL,
        asset_turnover_rank REAL,
        PRIMARY KEY (company_id, year),
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    );
    """)
    conn.commit()

def clean_interest_coverage(val: Any, is_debt_free: bool) -> float:
    if is_debt_free:
        return float('inf')
    if val is None or pd.isna(val):
        return np.nan
    if isinstance(val, str):
        if val.strip().lower() == 'debt free':
            return float('inf')
        try:
            return float(val)
        except ValueError:
            return np.nan
    return float(val)

def calculate_peer_percentiles(db_path: str):
    """Calculates percentile rankings within peer groups and updates SQLite database."""
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")
        
    conn = sqlite3.connect(path)
    init_db_schema(conn)
    
    try:
        # Load ratios and join with peer group definitions
        query = """
        SELECT 
            fr.company_id, fr.year,
            fr.return_on_equity_pct as roe,
            fr.return_on_capital_employed_pct as roce,
            fr.net_profit_margin_pct as npm,
            fr.debt_to_equity as debt_equity,
            fr.free_cash_flow_cr as fcf,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            fr.eps_cagr_5yr,
            fr.interest_coverage,
            fr.asset_turnover,
            fr.debt_free_label,
            pg.peer_group_name
        FROM financial_ratios fr
        LEFT JOIN peer_groups pg ON fr.company_id = pg.company_id
        """
        df = pd.read_sql_query(query, conn)
        
        if len(df) == 0:
            return
            
        # Normalize interest coverage
        df['icr_clean'] = [
            clean_interest_coverage(row['interest_coverage'], row.get('debt_free_label') == 1)
            for _, row in df.iterrows()
        ]
        
        # Mappings of metric name to db column and whether ascending is True
        metric_mappings = {
            'roe_rank': ('roe', True),
            'roce_rank': ('roce', True),
            'npm_rank': ('npm', True),
            'debt_equity_rank': ('debt_equity', False),  # lower D/E is better
            'fcf_rank': ('fcf', True),
            'revenue_cagr_rank': ('revenue_cagr_5yr', True),
            'pat_cagr_rank': ('pat_cagr_5yr', True),
            'eps_cagr_rank': ('eps_cagr_5yr', True),
            'icr_rank': ('icr_clean', True),
            'asset_turnover_rank': ('asset_turnover', True)
        }
        
        # Initialize result columns
        for rank_col in metric_mappings.keys():
            df[rank_col] = np.nan
            
        # Group by year and calculate rankings
        for year, year_group in df.groupby('year'):
            # 1. Process companies WITH a peer group
            with_peers = year_group[year_group['peer_group_name'].notna()].copy()
            if len(with_peers) > 0:
                for pg_name, pg_group in with_peers.groupby('peer_group_name'):
                    # Skip calculation if group has only 1 company with non-null values
                    for rank_col, (src_col, ascending) in metric_mappings.items():
                        non_null = pg_group[src_col].dropna()
                        if len(non_null) > 0:
                            # Percentile rank (0-100)
                            ranks = pg_group[src_col].rank(pct=True, ascending=ascending) * 100
                            df.loc[ranks.index, rank_col] = ranks.round(2)
                            
            # 2. Process companies WITHOUT a peer group
            no_peers = year_group[year_group['peer_group_name'].isna()].copy()
            if len(no_peers) > 0:
                # Calculate global fallback rankings across the entire year group
                for rank_col, (src_col, ascending) in metric_mappings.items():
                    non_null = year_group[src_col].dropna()
                    if len(non_null) > 0:
                        global_ranks = year_group[src_col].rank(pct=True, ascending=ascending) * 100
                        # Assign only to the ones without peers
                        df.loc[no_peers.index, rank_col] = global_ranks.loc[no_peers.index].round(2)

        # Build list of insert values
        insert_records = []
        for _, row in df.iterrows():
            insert_records.append((
                row['company_id'],
                row['year'],
                None if pd.isna(row['roe_rank']) else float(row['roe_rank']),
                None if pd.isna(row['roce_rank']) else float(row['roce_rank']),
                None if pd.isna(row['npm_rank']) else float(row['npm_rank']),
                None if pd.isna(row['debt_equity_rank']) else float(row['debt_equity_rank']),
                None if pd.isna(row['fcf_rank']) else float(row['fcf_rank']),
                None if pd.isna(row['revenue_cagr_rank']) else float(row['revenue_cagr_rank']),
                None if pd.isna(row['pat_cagr_rank']) else float(row['pat_cagr_rank']),
                None if pd.isna(row['eps_cagr_rank']) else float(row['eps_cagr_rank']),
                None if pd.isna(row['icr_rank']) else float(row['icr_rank']),
                None if pd.isna(row['asset_turnover_rank']) else float(row['asset_turnover_rank'])
            ))
            
        # Write to SQLite
        cursor = conn.cursor()
        cursor.executemany("""
        INSERT OR REPLACE INTO peer_percentiles (
            company_id, year, roe_rank, roce_rank, npm_rank, debt_equity_rank,
            fcf_rank, revenue_cagr_rank, pat_cagr_rank, eps_cagr_rank, icr_rank,
            asset_turnover_rank
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, insert_records)
        
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = "data/db/nifty100.db"
    calculate_peer_percentiles(db_path)
    print("Peer percentiles calculation complete.")
