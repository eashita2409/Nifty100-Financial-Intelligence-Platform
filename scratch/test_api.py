import sys
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

endpoints = [
    ("GET", "/api/v1/health", 200),
    ("GET", "/api/v1/companies", 200),
    ("GET", "/api/v1/companies/RELIANCE", 200),
    ("GET", "/api/v1/companies/RELIANCE/pl", 200),
    ("GET", "/api/v1/companies/RELIANCE/bs", 200),
    ("GET", "/api/v1/companies/RELIANCE/cashflow", 200),
    ("GET", "/api/v1/companies/RELIANCE/ratios", 200),
    ("GET", "/api/v1/companies/RELIANCE/tearsheet", 200),
    ("GET", "/api/v1/screener?min_market_cap=10000", 200),
    ("GET", "/api/v1/screener?min_market_cap=200&max_market_cap=100", 400), # Invalid
    ("GET", "/api/v1/sectors", 200),
    ("GET", "/api/v1/sectors/Energy/companies", 200),
    ("GET", "/api/v1/peers/some_group", 404), # Group not found, but proper 404
    ("GET", "/api/v1/companies/RELIANCE/peers/compare", 200),
    ("GET", "/api/v1/market-cap/RELIANCE", 200),
    ("GET", "/api/v1/portfolio/stats", 200),
    ("GET", "/api/v1/companies/RELIANCE/documents", 200),
    ("GET", "/api/v1/companies/INVALIDCOMPANY", 404)
]

print(f"{'endpoint':<50} | {'expected status':<15} | {'actual status':<15} | {'PASS/FAIL'}")
print("-" * 100)

all_pass = True
for method, url, expected in endpoints:
    if method == "GET":
        resp = client.get(url)
        actual = resp.status_code
        status = "PASS" if actual == expected else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"{url:<50} | {expected:<15} | {actual:<15} | {status}")

sys.exit(0 if all_pass else 1)
