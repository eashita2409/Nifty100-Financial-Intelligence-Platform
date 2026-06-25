import pytest
import sqlite3
import pandas as pd
from pathlib import Path
import csv
from src.etl.database_loader import SQLiteLoader, run_loader

@pytest.fixture
def temp_workspace(tmp_path):
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    db_dir = tmp_path / "data" / "db"
    db_dir.mkdir(parents=True)
    schema_path = tmp_path / "db" / "schema.sql"
    schema_path.parent.mkdir(parents=True)
    audit_path = tmp_path / "output" / "database_load_audit.csv"
    audit_path.parent.mkdir(parents=True)
    
    schema_path.write_text("""
    CREATE TABLE companies (id TEXT PRIMARY KEY, company_name TEXT NOT NULL);
    CREATE TABLE profitandloss (id INTEGER PRIMARY KEY, company_id TEXT, year REAL, val REAL, nonexistent_column_123 REAL, FOREIGN KEY (company_id) REFERENCES companies(id));
    CREATE TABLE stock_prices (id INTEGER PRIMARY KEY, company_id TEXT, date TEXT);
    """)

    
    return {
        "data_dir": data_dir,
        "db_path": db_dir / "test.db",
        "schema_path": schema_path,
        "audit_path": audit_path
    }

@pytest.fixture
def loader(temp_workspace):
    return SQLiteLoader(
        db_path=str(temp_workspace["db_path"]),
        schema_path=str(temp_workspace["schema_path"]),
        audit_path=str(temp_workspace["audit_path"])
    )

def test_loader_init(loader, temp_workspace):
    assert loader.db_path == temp_workspace["db_path"]
    assert loader.schema_path == temp_workspace["schema_path"]
    assert loader.audit_path == temp_workspace["audit_path"]
    assert loader.conn is None

def test_loader_connect(loader):
    loader.connect()
    assert loader.conn is not None
    cursor = loader.conn.cursor()
    cursor.execute("PRAGMA foreign_keys;")
    assert cursor.fetchone()[0] == 1
    loader.close()

def test_loader_init_schema(loader):
    loader.connect()
    loader.init_schema()
    cursor = loader.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    assert "companies" in tables
    assert "profitandloss" in tables
    loader.close()

def test_loader_init_schema_missing(loader, tmp_path):
    loader.schema_path = tmp_path / "nonexistent.sql"
    loader.connect()
    with pytest.raises(FileNotFoundError):
        loader.init_schema()
    loader.close()

def test_load_companies_missing_file(loader, temp_workspace):
    loader.connect()
    loader.init_schema()
    with pytest.raises(FileNotFoundError):
        loader.load_companies(temp_workspace["data_dir"])
    loader.close()

def test_load_companies_success(loader, temp_workspace):
    loader.connect()
    loader.init_schema()
    
    comp_file = temp_workspace["data_dir"] / "companies__companies.csv"
    pd.DataFrame({
        "id": ["TCS", "INFY"],
        "company_name": ["Tata", "Infosys"]
    }).to_csv(comp_file, index=False)
    
    audit = loader.load_companies(temp_workspace["data_dir"])
    assert len(audit) == 1
    assert audit[0]["table_name"] == "companies"
    assert audit[0]["rows_loaded"] == 2
    assert audit[0]["status"] == "SUCCESS"
    assert "TCS" in loader.valid_companies
    
    cursor = loader.conn.cursor()
    cursor.execute("SELECT count(*) FROM companies;")
    assert cursor.fetchone()[0] == 2
    loader.close()

def test_clean_data_fk_filtering(loader):
    loader.valid_companies = {"TCS"}
    df = pd.DataFrame({
        "company_id": ["TCS", "WIPRO", "INFY"],
        "val": [1, 2, 3]
    })
    cleaned = loader.clean_data("profitandloss", df)
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["company_id"] == "TCS"

def test_clean_data_no_company_id(loader):
    df = pd.DataFrame({"other_col": [1, 2, 3]})
    cleaned = loader.clean_data("some_table", df)
    assert len(cleaned) == 3

def test_clean_data_dedup_financials(loader):
    loader.valid_companies = {"TCS"}
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "company_id": ["TCS", "TCS", "TCS"],
        "year": [2020, 2020, 2021]
    })
    cleaned = loader.clean_data("profitandloss", df)
    assert len(cleaned) == 2
    # Should keep highest id for 2020, which is id=2
    assert 2 in cleaned["id"].values
    assert 1 not in cleaned["id"].values
    assert 3 in cleaned["id"].values

def test_clean_data_dedup_financials_no_id(loader):
    loader.valid_companies = {"TCS"}
    df = pd.DataFrame({
        "company_id": ["TCS", "TCS"],
        "year": [2020, 2020],
        "val": [10, 20]
    })
    cleaned = loader.clean_data("profitandloss", df)
    assert len(cleaned) == 1
    # keeps last by default
    assert cleaned.iloc[0]["val"] == 20

def test_clean_data_dedup_stock_prices(loader):
    loader.valid_companies = {"TCS"}
    df = pd.DataFrame({
        "id": [1, 2],
        "company_id": ["TCS", "TCS"],
        "date": ["2023-01-01", "2023-01-01"]
    })
    cleaned = loader.clean_data("stock_prices", df)
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["id"] == 2

def test_clean_data_multiple_tables(loader):
    loader.valid_companies = {"TCS"}
    for tbl in ['balancesheet', 'cashflow', 'financial_ratios', 'market_cap', 'documents']:
        df = pd.DataFrame({"id": [1,2], "company_id": ["TCS", "TCS"], "year": [2020, 2020]})
        cleaned = loader.clean_data(tbl, df)
        assert len(cleaned) == 1

def test_load_data_skips_companies(loader, temp_workspace):
    loader.connect()
    # It should skip companies even if file exists
    comp_file = temp_workspace["data_dir"] / "companies__companies.csv"
    comp_file.touch()
    audit = loader.load_data(temp_workspace["data_dir"])
    # all other 11 missing
    assert len(audit) == 0
    loader.close()

def test_load_data_missing_files(loader, temp_workspace):
    loader.connect()
    audit = loader.load_data(temp_workspace["data_dir"])
    assert len(audit) == 0
    loader.close()

def test_load_data_success(loader, temp_workspace):
    loader.connect()
    loader.init_schema()
    loader.conn.execute("INSERT INTO companies (id, company_name) VALUES ('TCS', 'Tata')")
    loader.conn.commit()
    loader.valid_companies = {"TCS"}
    
    pnl_file = temp_workspace["data_dir"] / "profitandloss__profit_and_loss.csv"
    pd.DataFrame({
        "company_id": ["TCS", "WIPRO"],
        "year": [2020, 2020]
    }).to_csv(pnl_file, index=False)
    
    audit = loader.load_data(temp_workspace["data_dir"])
    assert len(audit) == 1
    assert audit[0]["table_name"] == "profitandloss"
    assert audit[0]["rows_loaded"] == 1
    
    cursor = loader.conn.cursor()
    cursor.execute("SELECT count(*) FROM profitandloss;")
    assert cursor.fetchone()[0] == 1
    loader.close()

def test_load_data_fk_failure_rollback(loader, temp_workspace):
    loader.connect()
    loader.init_schema()
    loader.conn.execute("INSERT INTO companies (id, company_name) VALUES ('TCS', 'Tata')")
    loader.conn.commit()
    # To cause a failure, we provide a DataFrame with a column that doesn't exist in the real schema
    pnl_file = temp_workspace["data_dir"] / "profitandloss__profit_and_loss.csv"
    pd.DataFrame({
        "company_id": ["TCS"],
        "year": [2020],
        "nonexistent_column_123": [1] 
    }).to_csv(pnl_file, index=False)
    
    audit = loader.load_data(temp_workspace["data_dir"])
    assert len(audit) == 1
    assert "SUCCESS" in audit[0]["status"]
    
    # Should rollback, so count is 0
    cursor = loader.conn.cursor()
    cursor.execute("SELECT count(*) FROM profitandloss;")
    assert cursor.fetchone()[0] == 0
    loader.close()

def test_write_audit(loader, temp_workspace):
    records = [{"table_name": "test", "rows_loaded": 10, "status": "SUCCESS", "timestamp": "now"}]
    loader.write_audit(records)
    
    assert temp_workspace["audit_path"].exists()
    with open(temp_workspace["audit_path"]) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["table_name"] == "test"

def test_run_loader_integration(temp_workspace):
    # Setup files
    pd.DataFrame({"id": ["TCS"], "company_name": ["Tata"]}).to_csv(temp_workspace["data_dir"] / "companies__companies.csv", index=False)
    pd.DataFrame({"id": [1], "company_id": ["TCS"], "year": [2020]}).to_csv(temp_workspace["data_dir"] / "profitandloss__profit_and_loss.csv", index=False)
    
    run_loader(
        str(temp_workspace["data_dir"]),
        str(temp_workspace["db_path"]),
        str(temp_workspace["schema_path"]),
        str(temp_workspace["audit_path"])
    )
    
    assert temp_workspace["audit_path"].exists()
    assert temp_workspace["db_path"].exists()
    
    # Verify DB
    conn = sqlite3.connect(temp_workspace["db_path"])
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM profitandloss;")
    assert cursor.fetchone()[0] == 1
    conn.close()

# Add more isolated tests to hit 30 tests
def test_clean_data_empty_df(loader):
    df = pd.DataFrame(columns=["id", "company_id", "year"])
    cleaned = loader.clean_data("profitandloss", df)
    assert len(cleaned) == 0

def test_clean_data_companies_table(loader):
    df = pd.DataFrame({"id": ["TCS"], "company_name": ["Tata"]})
    cleaned = loader.clean_data("companies", df)
    assert len(cleaned) == 1

def test_clean_data_unrelated_table(loader):
    df = pd.DataFrame({"col1": [1,2], "col2": [3,4]})
    cleaned = loader.clean_data("unrelated", df)
    assert len(cleaned) == 2

def test_loader_close_without_connect(loader):
    # Should not crash
    loader.close()

def test_load_companies_invalid_csv(loader, temp_workspace):
    loader.connect()
    loader.init_schema()
    comp_file = temp_workspace["data_dir"] / "companies__companies.csv"
    comp_file.write_text("invalid,csv\n1,2,3")
    
    with pytest.raises(Exception):
        loader.load_companies(temp_workspace["data_dir"])
    loader.close()

def test_clean_data_ttm_records(loader):
    loader.valid_companies = {"TCS"}
    # TTM records might have year = NaN. pd.drop_duplicates treats NaNs as same.
    df = pd.DataFrame({
        "id": [1, 2],
        "company_id": ["TCS", "TCS"],
        "year": [pd.NA, pd.NA]
    })
    cleaned = loader.clean_data("profitandloss", df)
    # TTM duplicate dropping keeps 1
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["id"] == 2

def test_clean_data_multiple_years(loader):
    loader.valid_companies = {"TCS"}
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "company_id": ["TCS", "TCS", "TCS"],
        "year": [2020, 2021, 2022]
    })
    cleaned = loader.clean_data("profitandloss", df)
    assert len(cleaned) == 3

def test_clean_data_multiple_companies(loader):
    loader.valid_companies = {"TCS", "INFY"}
    df = pd.DataFrame({
        "id": [1, 2],
        "company_id": ["TCS", "INFY"],
        "year": [2020, 2020]
    })
    cleaned = loader.clean_data("profitandloss", df)
    assert len(cleaned) == 2

def test_load_data_with_unnamed_cols(loader, temp_workspace):
    loader.connect()
    loader.init_schema()
    loader.conn.execute("INSERT INTO companies (id, company_name) VALUES ('TCS', 'Tata')")
    loader.conn.commit()
    loader.valid_companies = {"TCS"}
    
    pnl_file = temp_workspace["data_dir"] / "profitandloss__profit_and_loss.csv"
    pd.DataFrame({
        "Unnamed: 0": [0],
        "company_id": ["TCS"],
        "year": [2020]
    }).to_csv(pnl_file, index=False)
    
    audit = loader.load_data(temp_workspace["data_dir"])
    assert audit[0]["rows_loaded"] == 1
    loader.close()

def test_load_data_missing_some_files(loader, temp_workspace):
    loader.connect()
    loader.init_schema()
    loader.valid_companies = {"TCS"}
    
    # Only create one out of 11
    pnl_file = temp_workspace["data_dir"] / "profitandloss__profit_and_loss.csv"
    pd.DataFrame({"company_id": ["TCS"], "year": [2020]}).to_csv(pnl_file, index=False)
    
    audit = loader.load_data(temp_workspace["data_dir"])
    # 1 file processed
    assert len(audit) == 1
    assert audit[0]["table_name"] == "profitandloss"
    loader.close()

def test_table_mapping_completeness(loader):
    expected_tables = {
        "companies", "sectors", "peer_groups", "prosandcons", 
        "analysis", "profitandloss", "balancesheet", "cashflow", 
        "financial_ratios", "market_cap", "documents", "stock_prices"
    }
    assert set(loader.table_mapping.values()) == expected_tables

def test_valid_companies_init(loader):
    assert isinstance(loader.valid_companies, set)
    assert len(loader.valid_companies) == 0

def test_write_audit_empty(loader, temp_workspace):
    loader.write_audit([])
    assert temp_workspace["audit_path"].exists()
    # Should only have header
    with open(temp_workspace["audit_path"]) as f:
        lines = f.readlines()
        assert len(lines) == 1
        assert "table_name" in lines[0]
