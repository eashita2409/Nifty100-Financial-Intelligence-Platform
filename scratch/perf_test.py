import asyncio
import time
import httpx
import statistics

async def fetch_screener(client):
    start = time.perf_counter()
    resp = await client.get("http://localhost:8000/api/v1/screener?min_market_cap=10000")
    end = time.perf_counter()
    return end - start

async def run_screener_test():
    async with httpx.AsyncClient() as client:
        start_total = time.perf_counter()
        tasks = [fetch_screener(client) for _ in range(10)]
        times = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_total
        
        print("--- Screener Concurrent Test ---")
        print(f"Total time for 10 concurrent requests: {total_time:.4f}s")
        print(f"Requirement met: {total_time < 10}")
        print(f"Min: {min(times):.4f}s")
        print(f"Max: {max(times):.4f}s")
        print(f"Mean: {statistics.mean(times):.4f}s")
        print(f"Median: {statistics.median(times):.4f}s")
        print()
        return total_time < 10

async def fetch_company_profile(client, ticker):
    start = time.perf_counter()
    # Profile hits tearsheet, pl, bs, cashflow, ratios
    endpoints = [
        f"/api/v1/companies/{ticker}",
        f"/api/v1/companies/{ticker}/pl",
        f"/api/v1/companies/{ticker}/bs",
        f"/api/v1/companies/{ticker}/cashflow",
        f"/api/v1/companies/{ticker}/ratios",
        f"/api/v1/companies/{ticker}/tearsheet"
    ]
    for ep in endpoints:
        resp = await client.get(f"http://localhost:8000{ep}")
    end = time.perf_counter()
    return end - start

async def run_profile_test():
    tickers = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ITC"] # From different sectors roughly
    async with httpx.AsyncClient() as client:
        print("--- Company Profile Load Time Test ---")
        all_pass = True
        for ticker in tickers:
            t = await fetch_company_profile(client, ticker)
            print(f"{ticker}: {t:.4f}s")
            if t > 3:
                all_pass = False
        print(f"Requirement met (<3s each): {all_pass}")
        print()
        return all_pass

async def main():
    screener_pass = await run_screener_test()
    profile_pass = await run_profile_test()

if __name__ == "__main__":
    asyncio.run(main())
