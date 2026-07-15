import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def check(endpoint: str, method: str = "GET", payload: dict = None):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        else:
            response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print(f"[PASS] {method} {endpoint}")
        else:
            print(f"[FAIL] {method} {endpoint} - Status {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"[ERROR] {method} {endpoint} - {str(e)}")

def run_tests():
    print("Waiting for server to start...")
    time.sleep(5)
    print("Testing 16 API Endpoints...\n")
    
    check("/health")
    check("/version")
    check("/companies")
    check("/company/RELIANCE")
    check("/ratios/RELIANCE")
    check("/valuation/RELIANCE")
    check("/cashflow/RELIANCE")
    check("/balance-sheet/RELIANCE")
    check("/profit-loss/RELIANCE")
    check("/pros-cons/RELIANCE")
    check("/peer/RELIANCE")
    check("/sector/Energy")
    check("/dashboard-summary")
    check("/cluster/Fund_11") # from sprint 6 clustering
    check("/screener?min_market_cap=10000")
    check("/recommend", method="POST", payload={"risk_profile": "Low"})
    
    print("\nTesting 404...")
    url = f"{BASE_URL}/company/NOTFOUND"
    res = requests.get(url)
    if res.status_code == 404:
        print("[PASS] 404 Error handling")
    else:
        print(f"[FAIL] Expected 404, got {res.status_code}")
        
    print("\nTesting Swagger UI...")
    docs_res = requests.get(f"{BASE_URL}/docs")
    if docs_res.status_code == 200:
        print("[PASS] Swagger UI loaded")
    else:
        print(f"[FAIL] Swagger UI failed: {docs_res.status_code}")

if __name__ == "__main__":
    run_tests()
