import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("KPIEngine")

class KPIEngine:
    def __init__(self, db_path: str, output_path: str):
        self.db_path = Path(db_path)
        self.output_path = Path(output_path)
        self.conn = None
        
    def connect(self):
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        if self.conn:
            self.conn.close()

    def _calc_growth(self, df: pd.DataFrame, col: str, new_col: str) -> pd.DataFrame:
        """Calculates YoY growth for a specific column, handling negative bases."""
        # Sort values by company and year to ensure correct chronological order
        df = df.sort_values(['company_id', 'year'])
        
        # Calculate growth: (current - prev) / abs(prev)
        df[f'{col}_prev'] = df.groupby('company_id')[col].shift(1)
        
        # Avoid division by zero
        df[new_col] = np.where(
            df[f'{col}_prev'] == 0, 
            np.nan, 
            (df[col] - df[f'{col}_prev']) / df[f'{col}_prev'].abs() * 100
        )
        return df

    def calculate_kpis(self) -> pd.DataFrame:
        """Fetch data and calculate all 20 KPIs."""
        logger.info("Fetching data from Data Warehouse...")
        
        # Fetch necessary tables
        companies = pd.read_sql_query("SELECT id as company_id, company_name, roce_percentage as source_roce, roe_percentage as source_roe FROM companies", self.conn)
        pnl = pd.read_sql_query("SELECT company_id, year, sales, net_profit, eps, opm_percentage as operating_margin FROM profitandloss", self.conn)
        ratios = pd.read_sql_query("SELECT company_id, year, debt_to_equity, interest_coverage, net_profit_margin_pct as net_margin, free_cash_flow_cr as fcf, return_on_equity_pct as roe, return_on_capital_employed_pct as roce FROM financial_ratios", self.conn)
        bs = pd.read_sql_query("SELECT company_id, year, other_asset, other_liabilities FROM balancesheet", self.conn)
        mc = pd.read_sql_query("SELECT company_id, year, market_cap_crore, pe_ratio as pe, pb_ratio as pb, dividend_yield_pct as dividend_yield, enterprise_value_crore as enterprise_value FROM market_cap", self.conn)
        cashflow = pd.read_sql_query("SELECT company_id, year, net_cash_flow FROM cashflow", self.conn)
        analysis = pd.read_sql_query("SELECT company_id, compounded_sales_growth as five_year_cagr FROM analysis WHERE compounded_sales_growth LIKE '5 Years%'", self.conn)
        
        logger.info("Computing Growth Metrics...")
        # Growth Metrics require historical data before filtering for the latest year
        pnl = self._calc_growth(pnl, 'sales', 'revenue_growth')
        pnl = self._calc_growth(pnl, 'net_profit', 'pat_growth')
        pnl = self._calc_growth(pnl, 'eps', 'eps_growth')
        
        cashflow = self._calc_growth(cashflow, 'net_cash_flow', 'cash_flow_growth')
        mc = self._calc_growth(mc, 'market_cap_crore', 'market_cap_growth')
        
        # Merge all temporal data on company_id and year
        logger.info("Merging datasets...")
        merged = pnl.merge(ratios, on=['company_id', 'year'], how='outer')
        merged = merged.merge(bs, on=['company_id', 'year'], how='outer')
        merged = merged.merge(mc, on=['company_id', 'year'], how='outer')
        merged = merged.merge(cashflow, on=['company_id', 'year'], how='outer')
        
        # Keep only the latest valid year per company
        latest = merged.dropna(subset=['year']).sort_values('year').groupby('company_id').tail(1).copy()
        
        # Merge with non-temporal data (companies, analysis)
        latest = latest.merge(companies, on='company_id', how='left')
        latest = latest.merge(analysis, on='company_id', how='left')
        
        logger.info("Calculating Derived Metrics (Ratios, PEG)...")
        # 1. Current Ratio
        latest['current_ratio'] = np.where(
            latest['other_liabilities'] == 0, 
            np.nan, 
            latest['other_asset'] / latest['other_liabilities']
        )
        
        # 2. Quick Ratio (Proxy using Current Ratio since Inventory is missing)
        latest['quick_ratio'] = latest['current_ratio']
        
        # 3. PEG Ratio (PE / EPS Growth)
        # Handle division by zero or negative EPS growth (PEG usually not meaningful if growth <= 0)
        latest['peg'] = np.where(
            (latest['eps_growth'].isna()) | (latest['eps_growth'] <= 0),
            np.nan,
            latest['pe'] / latest['eps_growth']
        )
        
        # Ensure 5-year CAGR is clean
        if 'five_year_cagr' in latest.columns:
            # Extract number after the colon, e.g., '5 Years: 13%' -> '13'
            extracted = latest['five_year_cagr'].astype(str).str.extract(r':\s*(-?\d+\.?\d*)', expand=False)
            latest['five_year_cagr'] = pd.to_numeric(extracted, errors='coerce')
            
        # Select and rename final 20 metrics
        final_cols = [
            'company_id', 'company_name', 'revenue_growth', 'pat_growth', 'eps_growth',
            'roe', 'roce', 'debt_to_equity', 'current_ratio', 'quick_ratio', 
            'interest_coverage', 'operating_margin', 'net_margin', 'cash_flow_growth', 
            'market_cap_growth', 'peg', 'pe', 'pb', 'dividend_yield', 
            'enterprise_value', 'fcf', 'five_year_cagr'
        ]
        
        # Rename debt_to_equity to debt_equity for consistency with requirements
        latest = latest.rename(columns={'debt_to_equity': 'debt_equity'})
        final_cols[final_cols.index('debt_to_equity')] = 'debt_equity'
        
        # Ensure all columns exist, fill missing with NaN
        for col in final_cols:
            if col not in latest.columns:
                latest[col] = np.nan
                
        result = latest[final_cols]
        logger.info(f"Successfully calculated KPIs for {len(result)} companies.")
        return result

    def generate_report(self):
        self.connect()
        try:
            df = self.calculate_kpis()
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(self.output_path, index=False)
            logger.info(f"KPI Summary successfully exported to {self.output_path.name}")
        finally:
            self.close()

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    db_path = project_root / "data" / "db" / "nifty100.db"
    output_path = project_root / "output" / "kpi_summary.csv"
    
    engine = KPIEngine(str(db_path), str(output_path))
    engine.generate_report()
