import pytest
from src.api.schemas import RecommendRequest

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"

def test_version(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()

def test_get_companies(client):
    response = client.get("/companies")
    assert response.status_code == 200
    data = response.json()
    assert "companies" in data
    assert data["total"] >= 0

def test_get_company(client):
    response = client.get("/company/RELIANCE")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "RELIANCE"

def test_get_company_not_found(client):
    response = client.get("/company/INVALID_TICKER")
    assert response.status_code == 404
    assert response.json()["detail"] == "Company with ticker INVALID_TICKER not found"

def test_get_ratios(client):
    response = client.get("/ratios/RELIANCE")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "RELIANCE"
    assert isinstance(data["ratios"], list)

def test_get_valuation(client):
    response = client.get("/valuation/RELIANCE")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "RELIANCE"
    assert isinstance(data["valuations"], list)

def test_get_cashflow(client):
    response = client.get("/cashflow/RELIANCE")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "RELIANCE"
    assert isinstance(data["cashflows"], list)

def test_get_balance_sheet(client):
    response = client.get("/balance-sheet/RELIANCE")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "RELIANCE"
    assert isinstance(data["balance_sheets"], list)

def test_get_profit_loss(client):
    response = client.get("/profit-loss/RELIANCE")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "RELIANCE"
    assert isinstance(data["profit_loss"], list)

def test_get_pros_cons(client):
    response = client.get("/pros-cons/RELIANCE")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "RELIANCE"
    assert isinstance(data["pros"], list)
    assert isinstance(data["cons"], list)

def test_get_peer(client):
    response = client.get("/peer/RELIANCE")
    assert response.status_code == 200
    data = response.json()
    assert "sector" in data
    assert isinstance(data["peers"], list)

def test_get_sector(client):
    response = client.get("/sector/Energy")
    assert response.status_code == 200
    data = response.json()
    assert data["sector"] == "Energy"
    assert "company_count" in data

def test_get_dashboard_summary(client):
    response = client.get("/dashboard-summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_companies" in data
    assert "total_market_cap" in data
    assert "sectors_count" in data

def test_get_cluster(client):
    # Depending on generated CSV, this might return 404 or 200
    # The requirement is just to test endpoints, so we check valid responses
    response = client.get("/cluster/Fund_11")
    assert response.status_code in (200, 404)

def test_screener(client):
    response = client.get("/screener?min_market_cap=10000")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_recommend(client):
    response = client.post("/recommend", json={"risk_profile": "Low"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["recommendations"], list)

def test_swagger_ui(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()

def test_redoc(client):
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "redoc" in response.text.lower()
