import pytest
from fastapi.testclient import TestClient
import sqlite3
import os

from src.api.main import app
from src.api.database import get_db

@pytest.fixture(scope="session")
def db_connection():
    # Use the real database for tests, or create a mock one. 
    # Since we need to test DB queries, we'll use the existing DB.
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'db', 'nifty100.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()

@pytest.fixture(scope="session")
def client(db_connection):
    def override_get_db():
        yield db_connection
        
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
