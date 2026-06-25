import sqlite3
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import csv
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DatabaseLoader")

class SQLiteLoader:
    def __init__(self, db_path: str, schema_path: str, audit_path: str):
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)
        self.audit_path = Path(audit_path)
        self.conn = None
        self.valid_companies = set()
        
        # Mapping CSV filenames to their target tables
        self.table_mapping = {
            "companies__companies.csv": "companies",
            "sectors__sheet1.csv": "sectors",
            "peer_groups__sheet1.csv": "peer_groups",
            "prosandcons__pros_and_cons.csv": "prosandcons",
            "analysis__analysis.csv": "analysis",
            "profitandloss__profit_and_loss.csv": "profitandloss",
            "balancesheet__balance_sheet.csv": "balancesheet",
            "cashflow__cash_flow.csv": "cashflow",
            "financial_ratios__sheet1.csv": "financial_ratios",
            "market_cap__sheet1.csv": "market_cap",
            "documents__documents.csv": "documents",
            "stock_prices__sheet1.csv": "stock_prices"
        }

    def connect(self):
        """Establish connection to SQLite database and enable foreign keys."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        logger.info(f"Connected to database: {self.db_path}")

    def init_schema(self):
        """Initialize the database schema."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        with open(self.schema_path, "r") as f:
            schema_script = f.read()
            
        try:
            self.conn.executescript(schema_script)
            logger.info("Schema initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise

    def load_companies(self, data_dir: Path) -> List[Dict[str, Any]]:
        """Load companies first to establish valid foreign keys."""
        audit_records = []
        companies_file = data_dir / "companies__companies.csv"
        
        if not companies_file.exists():
            raise FileNotFoundError(f"Companies file not found: {companies_file}")
            
        try:
            df = pd.read_csv(companies_file)
            self.valid_companies = set(df['id'].dropna().astype(str))
            
            # Start transaction for companies
            with self.conn:
                df.to_sql("companies", self.conn, if_exists="append", index=False)
                
            rows_loaded = len(df)
            logger.info(f"Loaded {rows_loaded} rows into companies table.")
            audit_records.append({
                "table_name": "companies",
                "rows_loaded": rows_loaded,
                "status": "SUCCESS",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error loading companies: {e}")
            audit_records.append({
                "table_name": "companies",
                "rows_loaded": 0,
                "status": f"FAILED: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
            raise
            
        return audit_records

    def clean_data(self, table_name: str, df: pd.DataFrame) -> pd.DataFrame:
        """Apply table-specific cleaning and deduplication rules."""
        initial_len = len(df)
        
        # 1. Filter out invalid foreign keys
        if 'company_id' in df.columns:
            df = df[df['company_id'].astype(str).isin(self.valid_companies)]
            dropped_fk = initial_len - len(df)
            if dropped_fk > 0:
                logger.warning(f"{table_name}: Dropped {dropped_fk} rows due to missing company_id in companies table.")
                
        # 2. Deduplicate financial tables on (company_id, year) or (company_id, date)
        if 'year' in df.columns and table_name in ['profitandloss', 'balancesheet', 'cashflow', 'financial_ratios', 'market_cap', 'documents']:
            # Sort by id to keep highest id, then drop duplicates on company_id, year
            if 'id' in df.columns:
                df = df.sort_values('id')
            df = df.drop_duplicates(subset=['company_id', 'year'], keep='last')
            dropped_dup = initial_len - len(df) - (dropped_fk if 'company_id' in df.columns else 0)
            if dropped_dup > 0:
                logger.warning(f"{table_name}: Dropped {dropped_dup} duplicate rows on (company_id, year).")
                
        if 'date' in df.columns and table_name == 'stock_prices':
            if 'id' in df.columns:
                df = df.sort_values('id')
            df = df.drop_duplicates(subset=['company_id', 'date'], keep='last')
            dropped_dup = initial_len - len(df) - (dropped_fk if 'company_id' in df.columns else 0)
            if dropped_dup > 0:
                logger.warning(f"{table_name}: Dropped {dropped_dup} duplicate rows on (company_id, date).")

        return df

    def load_data(self, data_dir: Path) -> List[Dict[str, Any]]:
        """Load all other tables with transaction support and rollback."""
        audit_records = []
        
        for filename, table_name in self.table_mapping.items():
            if table_name == "companies":
                continue # Already loaded
                
            file_path = data_dir / filename
            if not file_path.exists():
                logger.warning(f"File not found, skipping: {file_path}")
                continue
                
            logger.info(f"Processing {filename} -> {table_name}")
            try:
                df = pd.read_csv(file_path)
                # Drop unnamed index columns if present
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                
                # Apply data cleaning
                df = self.clean_data(table_name, df)
                
                # Use implicit transaction via context manager. If to_sql fails, it rolls back.
                with self.conn:
                    df.to_sql(table_name, self.conn, if_exists="append", index=False)
                    
                rows_loaded = len(df)
                logger.info(f"Loaded {rows_loaded} rows into {table_name}")
                audit_records.append({
                    "table_name": table_name,
                    "rows_loaded": rows_loaded,
                    "status": "SUCCESS",
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Failed to load {table_name}: {e}")
                audit_records.append({
                    "table_name": table_name,
                    "rows_loaded": 0,
                    "status": f"FAILED: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
                # No raise here; continue loading other tables, but record the failure
                
        return audit_records
        
    def write_audit(self, records: List[Dict[str, Any]]):
        """Write audit records to CSV."""
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        keys = ["table_name", "rows_loaded", "status", "timestamp"]
        with open(self.audit_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(records)
        logger.info(f"Audit log written to {self.audit_path}")

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")

def run_loader(data_dir: str, db_path: str, schema_path: str, audit_path: str):
    loader = SQLiteLoader(db_path, schema_path, audit_path)
    audit_records = []
    try:
        loader.connect()
        loader.init_schema()
        # Load companies first
        comp_records = loader.load_companies(Path(data_dir))
        audit_records.extend(comp_records)
        # Load the rest
        other_records = loader.load_data(Path(data_dir))
        audit_records.extend(other_records)
    finally:
        loader.write_audit(audit_records)
        loader.close()

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data" / "processed"
    db_path = project_root / "data" / "db" / "nifty100.db"
    schema_path = project_root / "db" / "schema.sql"
    audit_path = project_root / "output" / "database_load_audit.csv"
    
    run_loader(str(data_dir), str(db_path), str(schema_path), str(audit_path))
