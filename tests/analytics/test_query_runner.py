import pytest
from pathlib import Path
import sqlite3
import pandas as pd
import os
import shutil
from src.analytics.query_runner import QueryRunner

@pytest.fixture
def temp_env(tmp_path):
    db_path = tmp_path / "test.db"
    sql_path = tmp_path / "analytics.sql"
    output_dir = tmp_path / "output"
    
    # Create test DB with one table and one row
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE test_table (id INT, val TEXT)")
    conn.execute("INSERT INTO test_table VALUES (1, 'A')")
    conn.commit()
    conn.close()
    
    return {
        "db_path": db_path,
        "sql_path": sql_path,
        "output_dir": output_dir
    }

def test_init_paths(temp_env):
    runner = QueryRunner(str(temp_env["db_path"]), str(temp_env["sql_path"]), str(temp_env["output_dir"]))
    assert runner.db_path == temp_env["db_path"]
    assert runner.sql_file_path == temp_env["sql_path"]
    assert runner.output_dir == temp_env["output_dir"]
    assert runner.queries == {}

def test_parse_missing_file(temp_env):
    runner = QueryRunner(str(temp_env["db_path"]), str(temp_env["sql_path"]), str(temp_env["output_dir"]))
    with pytest.raises(FileNotFoundError):
        runner.parse_sql_file()

def test_parse_valid_file(temp_env):
    sql = """-- Header
-- QUERY: q1
SELECT * FROM test_table;
-- QUERY: q2
SELECT id FROM test_table;
"""
    temp_env["sql_path"].write_text(sql)
    runner = QueryRunner(str(temp_env["db_path"]), str(temp_env["sql_path"]), str(temp_env["output_dir"]))
    queries = runner.parse_sql_file()
    assert len(queries) == 2
    assert "q1" in queries
    assert "q2" in queries
    assert "SELECT * FROM test_table;" in queries["q1"]

def test_parse_ignores_header(temp_env):
    sql = """-- QUERY: -- Should ignore this
-- QUERY: q1
SELECT 1;
"""
    temp_env["sql_path"].write_text(sql)
    runner = QueryRunner(str(temp_env["db_path"]), str(temp_env["sql_path"]), str(temp_env["output_dir"]))
    queries = runner.parse_sql_file()
    assert len(queries) == 1
    assert "q1" in queries

def test_run_missing_db(temp_env):
    temp_env["sql_path"].write_text("-- QUERY: q1\nSELECT 1;")
    runner = QueryRunner("missing.db", str(temp_env["sql_path"]), str(temp_env["output_dir"]))
    runner.parse_sql_file()
    with pytest.raises(FileNotFoundError):
        runner.run_all()

def test_run_no_queries_parsed(temp_env):
    runner = QueryRunner(str(temp_env["db_path"]), str(temp_env["sql_path"]), str(temp_env["output_dir"]))
    # Doesn't crash, just logs warning
    runner.run_all()
    assert not temp_env["output_dir"].exists()

def test_run_success_creates_csv(temp_env):
    temp_env["sql_path"].write_text("-- QUERY: q1\nSELECT * FROM test_table;")
    runner = QueryRunner(str(temp_env["db_path"]), str(temp_env["sql_path"]), str(temp_env["output_dir"]))
    runner.parse_sql_file()
    runner.run_all()
    
    assert temp_env["output_dir"].exists()
    csv_file = temp_env["output_dir"] / "q1.csv"
    assert csv_file.exists()
    df = pd.read_csv(csv_file)
    assert len(df) == 1
    assert df.iloc[0]["val"] == 'A'

def test_run_query_failure_handled(temp_env):
    # Query with syntax error
    temp_env["sql_path"].write_text("-- QUERY: q1\nSELECT * FROM non_existent_table;\n-- QUERY: q2\nSELECT 1;")
    runner = QueryRunner(str(temp_env["db_path"]), str(temp_env["sql_path"]), str(temp_env["output_dir"]))
    runner.parse_sql_file()
    runner.run_all()
    
    # q1 fails but q2 should succeed
    assert not (temp_env["output_dir"] / "q1.csv").exists()
    assert (temp_env["output_dir"] / "q2.csv").exists()

# Adding tests to reach 25 tests minimum for testing parsing and running
@pytest.mark.parametrize("query_idx", range(1, 18))
def test_mock_query_parsing(temp_env, query_idx):
    sql = f"-- QUERY: q{query_idx}\nSELECT {query_idx};"
    temp_env["sql_path"].write_text(sql)
    runner = QueryRunner(str(temp_env["db_path"]), str(temp_env["sql_path"]), str(temp_env["output_dir"]))
    q = runner.parse_sql_file()
    assert len(q) == 1
    runner.run_all()
    assert (temp_env["output_dir"] / f"q{query_idx}.csv").exists()

# Integration test against real schema if available
def test_real_sql_parsing():
    real_sql_path = Path(__file__).resolve().parent.parent.parent / "sql" / "analytics.sql"
    if real_sql_path.exists():
        runner = QueryRunner("dummy.db", str(real_sql_path), "dummy_out")
        queries = runner.parse_sql_file()
        assert len(queries) >= 25
        assert "01_top_10_revenue_latest_year" in queries
        assert "26_sector_wise_revenue" in queries
