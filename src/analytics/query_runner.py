import sqlite3
import pandas as pd
from pathlib import Path
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("QueryRunner")

class QueryRunner:
    def __init__(self, db_path: str, sql_file_path: str, output_dir: str):
        self.db_path = Path(db_path)
        self.sql_file_path = Path(sql_file_path)
        self.output_dir = Path(output_dir)
        self.queries = {}
        
    def parse_sql_file(self):
        """Parse the SQL file and extract individual queries."""
        if not self.sql_file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {self.sql_file_path}")
            
        with open(self.sql_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Split by the QUERY marker
        parts = content.split("-- QUERY: ")
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # First line is the query name
            lines = part.split('\n')
            query_name = lines[0].strip()
            
            # Skip if it's the header block
            if query_name.startswith("--") or not query_name:
                continue
                
            # The rest is the SQL query (including other comments)
            query_sql = '\n'.join(lines[1:]).strip()
            
            if query_name and query_sql:
                self.queries[query_name] = query_sql
                
        logger.info(f"Parsed {len(self.queries)} queries from {self.sql_file_path.name}")
        return self.queries

    def run_all(self):
        """Run all parsed queries and export to CSV."""
        if not self.queries:
            logger.warning("No queries to run. Did you parse the SQL file?")
            return
            
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
            
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            for name, sql in self.queries.items():
                logger.info(f"Executing query: {name}")
                try:
                    df = pd.read_sql_query(sql, conn)
                    output_file = self.output_dir / f"{name}.csv"
                    df.to_csv(output_file, index=False)
                    logger.info(f"-> Saved {len(df)} rows to {output_file.name}")
                except Exception as e:
                    logger.error(f"Error executing query '{name}': {e}")
                    
        finally:
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    db_path = project_root / "data" / "db" / "nifty100.db"
    sql_path = project_root / "sql" / "analytics.sql"
    output_dir = project_root / "output" / "query_results"
    
    runner = QueryRunner(str(db_path), str(sql_path), str(output_dir))
    runner.parse_sql_file()
    runner.run_all()
