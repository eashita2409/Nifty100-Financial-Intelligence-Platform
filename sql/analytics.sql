-- Nifty100 Financial Intelligence Platform
-- Sprint 1 Day 5: Financial Analytics Queries
-- Note: Each query must be preceded by exactly '-- QUERY: <query_name>'

-- QUERY: 01_top_10_revenue_latest_year
-- Identifies the top 10 companies by revenue in the most recent year available for each company
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM profitandloss
    GROUP BY company_id
)
SELECT c.company_name, p.year, p.sales
FROM profitandloss p
JOIN LatestYear l ON p.company_id = l.company_id AND p.year = l.max_year
JOIN companies c ON p.company_id = c.id
ORDER BY p.sales DESC
LIMIT 10;

-- QUERY: 02_highest_roe_companies
-- Top 15 companies by Return on Equity (ROE) based on the companies master table
SELECT company_name, roe_percentage
FROM companies
WHERE roe_percentage IS NOT NULL
ORDER BY roe_percentage DESC
LIMIT 15;

-- QUERY: 03_highest_roce_companies
-- Top 15 companies by Return on Capital Employed (ROCE)
SELECT company_name, roce_percentage
FROM companies
WHERE roce_percentage IS NOT NULL
ORDER BY roce_percentage DESC
LIMIT 15;

-- QUERY: 04_debt_to_equity_ranking
-- Ranks companies by Debt-to-Equity ratio (lowest first) for the latest year
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM financial_ratios
    GROUP BY company_id
)
SELECT c.company_name, f.year, f.debt_to_equity
FROM financial_ratios f
JOIN LatestYear l ON f.company_id = l.company_id AND f.year = l.max_year
JOIN companies c ON f.company_id = c.id
WHERE f.debt_to_equity IS NOT NULL
ORDER BY f.debt_to_equity ASC;

-- QUERY: 05_top_10_sales_cagr
-- Top 10 companies by compounded sales growth (needs parsing since it's text in the analysis table, e.g., '10%')
SELECT c.company_name, a.compounded_sales_growth
FROM analysis a
JOIN companies c ON a.company_id = c.id
WHERE a.compounded_sales_growth IS NOT NULL
ORDER BY CAST(REPLACE(a.compounded_sales_growth, '%', '') AS REAL) DESC
LIMIT 10;

-- QUERY: 06_average_eps_growth
-- Calculates the Average EPS across the last 3 available years per company
SELECT c.company_name, AVG(p.eps) as avg_eps
FROM profitandloss p
JOIN companies c ON p.company_id = c.id
WHERE p.eps IS NOT NULL
GROUP BY p.company_id, c.company_name
ORDER BY avg_eps DESC
LIMIT 20;

-- QUERY: 07_highest_market_cap
-- Top 15 companies by Market Capitalization in the latest year
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM market_cap
    GROUP BY company_id
)
SELECT c.company_name, m.market_cap_crore
FROM market_cap m
JOIN LatestYear l ON m.company_id = l.company_id AND m.year = l.max_year
JOIN companies c ON m.company_id = c.id
ORDER BY m.market_cap_crore DESC
LIMIT 15;

-- QUERY: 08_sector_wise_market_cap_averages
-- Calculates the average market cap per broad sector
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM market_cap
    GROUP BY company_id
)
SELECT s.broad_sector, COUNT(s.company_id) as num_companies, AVG(m.market_cap_crore) as avg_market_cap_crore
FROM sectors s
JOIN market_cap m ON s.company_id = m.company_id
JOIN LatestYear l ON m.company_id = l.company_id AND m.year = l.max_year
GROUP BY s.broad_sector
ORDER BY avg_market_cap_crore DESC;

-- QUERY: 09_highest_operating_margin
-- Top companies by operating profit margin for the latest year
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM profitandloss
    GROUP BY company_id
)
SELECT c.company_name, p.opm_percentage
FROM profitandloss p
JOIN LatestYear l ON p.company_id = l.company_id AND p.year = l.max_year
JOIN companies c ON p.company_id = c.id
ORDER BY p.opm_percentage DESC
LIMIT 15;

-- QUERY: 10_lowest_debt_companies
-- Companies with the lowest absolute total debt
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM financial_ratios
    GROUP BY company_id
)
SELECT c.company_name, f.total_debt_cr
FROM financial_ratios f
JOIN LatestYear l ON f.company_id = l.company_id AND f.year = l.max_year
JOIN companies c ON f.company_id = c.id
ORDER BY f.total_debt_cr ASC
LIMIT 15;

-- QUERY: 11_highest_dividend_yield
-- Top companies by Dividend Yield percentage
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM market_cap
    GROUP BY company_id
)
SELECT c.company_name, m.dividend_yield_pct
FROM market_cap m
JOIN LatestYear l ON m.company_id = l.company_id AND m.year = l.max_year
JOIN companies c ON m.company_id = c.id
WHERE m.dividend_yield_pct IS NOT NULL
ORDER BY m.dividend_yield_pct DESC
LIMIT 15;

-- QUERY: 12_companies_with_declining_profits
-- Identifies companies where the latest year net profit is lower than the previous year
WITH RankedProfits AS (
    SELECT company_id, year, net_profit,
           LAG(net_profit) OVER (PARTITION BY company_id ORDER BY year) as prev_net_profit,
           ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
    FROM profitandloss
)
SELECT c.company_name, r.year, r.prev_net_profit, r.net_profit, (r.net_profit - r.prev_net_profit) as profit_change
FROM RankedProfits r
JOIN companies c ON r.company_id = c.id
WHERE r.rn = 1 AND r.net_profit < r.prev_net_profit;

-- QUERY: 13_top_cash_generators
-- Top 15 companies by Free Cash Flow in the latest year
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM financial_ratios
    GROUP BY company_id
)
SELECT c.company_name, f.free_cash_flow_cr
FROM financial_ratios f
JOIN LatestYear l ON f.company_id = l.company_id AND f.year = l.max_year
JOIN companies c ON f.company_id = c.id
ORDER BY f.free_cash_flow_cr DESC
LIMIT 15;

-- QUERY: 14_price_trends_volatility
-- Calculates the price volatility (High - Low) as a percentage of Open for a specific date or on average
SELECT c.company_name, AVG((s.high_price - s.low_price) / s.open_price * 100) as avg_daily_volatility_pct
FROM stock_prices s
JOIN companies c ON s.company_id = c.id
WHERE s.open_price > 0
GROUP BY s.company_id, c.company_name
ORDER BY avg_daily_volatility_pct DESC
LIMIT 15;

-- QUERY: 15_market_cap_distribution
-- Groups companies into Market Cap categories
SELECT market_cap_category, COUNT(*) as number_of_companies
FROM sectors
GROUP BY market_cap_category
ORDER BY number_of_companies DESC;

-- QUERY: 16_zero_debt_companies
-- Companies with exactly zero total debt in the latest year
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM financial_ratios
    GROUP BY company_id
)
SELECT c.company_name, f.total_debt_cr
FROM financial_ratios f
JOIN LatestYear l ON f.company_id = l.company_id AND f.year = l.max_year
JOIN companies c ON f.company_id = c.id
WHERE f.total_debt_cr = 0;

-- QUERY: 17_highest_dividend_payout_ratio
-- Top companies returning profits as dividends
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM financial_ratios
    GROUP BY company_id
)
SELECT c.company_name, f.dividend_payout_ratio_pct
FROM financial_ratios f
JOIN LatestYear l ON f.company_id = l.company_id AND f.year = l.max_year
JOIN companies c ON f.company_id = c.id
ORDER BY f.dividend_payout_ratio_pct DESC
LIMIT 15;

-- QUERY: 18_lowest_pe_ratio_value_stocks
-- Identifies value stocks by lowest P/E ratio (filtering out negative P/E)
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM market_cap
    GROUP BY company_id
)
SELECT c.company_name, m.pe_ratio
FROM market_cap m
JOIN LatestYear l ON m.company_id = l.company_id AND m.year = l.max_year
JOIN companies c ON m.company_id = c.id
WHERE m.pe_ratio > 0
ORDER BY m.pe_ratio ASC
LIMIT 15;

-- QUERY: 19_highest_pb_ratio
-- Top companies by Price to Book ratio
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM market_cap
    GROUP BY company_id
)
SELECT c.company_name, m.pb_ratio
FROM market_cap m
JOIN LatestYear l ON m.company_id = l.company_id AND m.year = l.max_year
JOIN companies c ON m.company_id = c.id
ORDER BY m.pb_ratio DESC
LIMIT 15;

-- QUERY: 20_best_asset_turnover
-- Top companies efficiently using assets to generate sales
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM financial_ratios
    GROUP BY company_id
)
SELECT c.company_name, f.asset_turnover
FROM financial_ratios f
JOIN LatestYear l ON f.company_id = l.company_id AND f.year = l.max_year
JOIN companies c ON f.company_id = c.id
ORDER BY f.asset_turnover DESC
LIMIT 15;

-- QUERY: 21_highest_eps
-- Top companies by absolute Earnings Per Share
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM financial_ratios
    GROUP BY company_id
)
SELECT c.company_name, f.earnings_per_share
FROM financial_ratios f
JOIN LatestYear l ON f.company_id = l.company_id AND f.year = l.max_year
JOIN companies c ON f.company_id = c.id
ORDER BY f.earnings_per_share DESC
LIMIT 15;

-- QUERY: 22_strongest_interest_coverage
-- Top companies by Interest Coverage ratio (ability to pay interest)
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM financial_ratios
    GROUP BY company_id
)
SELECT c.company_name, f.interest_coverage
FROM financial_ratios f
JOIN LatestYear l ON f.company_id = l.company_id AND f.year = l.max_year
JOIN companies c ON f.company_id = c.id
WHERE f.interest_coverage > 0
ORDER BY f.interest_coverage DESC
LIMIT 15;

-- QUERY: 23_largest_capex_spenders
-- Companies spending the most on Capital Expenditures
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM financial_ratios
    GROUP BY company_id
)
SELECT c.company_name, f.capex_cr
FROM financial_ratios f
JOIN LatestYear l ON f.company_id = l.company_id AND f.year = l.max_year
JOIN companies c ON f.company_id = c.id
ORDER BY f.capex_cr DESC
LIMIT 15;

-- QUERY: 24_highest_ev_ebitda
-- Top companies by EV/EBITDA ratio
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM market_cap
    GROUP BY company_id
)
SELECT c.company_name, m.ev_ebitda
FROM market_cap m
JOIN LatestYear l ON m.company_id = l.company_id AND m.year = l.max_year
JOIN companies c ON m.company_id = c.id
WHERE m.ev_ebitda > 0
ORDER BY m.ev_ebitda DESC
LIMIT 15;

-- QUERY: 25_companies_below_book_value
-- Value stocks trading below their book value (P/B < 1)
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM market_cap
    GROUP BY company_id
)
SELECT c.company_name, m.pb_ratio
FROM market_cap m
JOIN LatestYear l ON m.company_id = l.company_id AND m.year = l.max_year
JOIN companies c ON m.company_id = c.id
WHERE m.pb_ratio > 0 AND m.pb_ratio < 1
ORDER BY m.pb_ratio ASC;

-- QUERY: 26_sector_wise_revenue
-- Calculates the total and average revenue per sector for the latest year
WITH LatestYear AS (
    SELECT company_id, MAX(year) as max_year
    FROM profitandloss
    GROUP BY company_id
)
SELECT s.broad_sector, SUM(p.sales) as total_sector_revenue, AVG(p.sales) as avg_company_revenue
FROM profitandloss p
JOIN LatestYear l ON p.company_id = l.company_id AND p.year = l.max_year
JOIN sectors s ON p.company_id = s.company_id
GROUP BY s.broad_sector
ORDER BY total_sector_revenue DESC;
