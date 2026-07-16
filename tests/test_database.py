import sqlite3

def test_database_connection(db_connection):
    # Verify the connection is active
    cursor = db_connection.cursor()
    cursor.execute("SELECT 1")
    assert cursor.fetchone()[0] == 1

def test_table_existence(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    
    expected_tables = [
        'companies', 'sectors', 'prosandcons', 'analysis', 
        'profitandloss', 'balancesheet', 'cashflow', 
        'financial_ratios', 'market_cap', 'stock_prices'
    ]
    
    for table in expected_tables:
        assert table in tables, f"Table {table} is missing from the database"

def test_foreign_key_integrity(db_connection):
    cursor = db_connection.cursor()
    # Pragma foreign_key_check returns a list of foreign key violations
    # If the list is empty, there are no violations
    cursor.execute("PRAGMA foreign_key_check")
    violations = cursor.fetchall()
    assert len(violations) == 0, f"Found foreign key violations: {violations}"

def test_schema_validation(db_connection):
    # Check that companies table has the right columns
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(companies)")
    columns = [row['name'] for row in cursor.fetchall()]
    
    assert 'id' in columns
    assert 'company_name' in columns
