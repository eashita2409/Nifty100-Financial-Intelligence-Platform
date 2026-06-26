-- Nifty100 Financial Intelligence Platform
-- Sprint 1 Day 4: SQLite Database Schema

PRAGMA foreign_keys = ON;

-- 1. companies
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    company_logo TEXT,
    company_name TEXT NOT NULL,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);

-- 2. sectors
CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    broad_sector TEXT,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_sectors_company ON sectors(company_id);

-- 3. peer_groups
CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_group_name TEXT NOT NULL,
    company_id TEXT NOT NULL,
    is_benchmark BOOLEAN,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_peer_groups_company ON peer_groups(company_id);

-- 4. prosandcons
CREATE TABLE IF NOT EXISTS prosandcons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_prosandcons_company ON prosandcons(company_id);

-- 5. analysis
CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_analysis_company ON analysis(company_id);

-- 6. profitandloss
CREATE TABLE IF NOT EXISTS profitandloss (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year REAL,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE (company_id, year),
    CHECK (year >= 1990 OR year IS NULL)
);
CREATE INDEX IF NOT EXISTS idx_pnl_company_year ON profitandloss(company_id, year);

-- 7. balancesheet
CREATE TABLE IF NOT EXISTS balancesheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year REAL,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE (company_id, year),
    CHECK (year >= 1990 OR year IS NULL)
);
CREATE INDEX IF NOT EXISTS idx_bs_company_year ON balancesheet(company_id, year);

-- 8. cashflow
CREATE TABLE IF NOT EXISTS cashflow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year REAL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE (company_id, year),
    CHECK (year >= 1990 OR year IS NULL)
);
CREATE INDEX IF NOT EXISTS idx_cf_company_year ON cashflow(company_id, year);

-- 9. financial_ratios
CREATE TABLE IF NOT EXISTS financial_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year REAL,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,
    return_on_capital_employed_pct REAL,
    return_on_assets_pct REAL,
    sector_relative_roce BOOLEAN,
    high_leverage_flag BOOLEAN,
    debt_free_label BOOLEAN,
    icr_warning_flag BOOLEAN,
    net_debt_cr REAL,
    revenue_cagr_3yr REAL,
    revenue_cagr_5yr REAL,
    revenue_cagr_10yr REAL,
    revenue_cagr_anomaly TEXT,
    pat_cagr_3yr REAL,
    pat_cagr_5yr REAL,
    pat_cagr_10yr REAL,
    pat_cagr_anomaly TEXT,
    eps_cagr_3yr REAL,
    eps_cagr_5yr REAL,
    eps_cagr_10yr REAL,
    eps_cagr_anomaly TEXT,
    cfo_quality_score REAL,
    capex_intensity REAL,
    fcf_conversion REAL,
    capital_allocation_pattern TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE (company_id, year),
    CHECK (year >= 1990 OR year IS NULL)
);
CREATE INDEX IF NOT EXISTS idx_fr_company_year ON financial_ratios(company_id, year);

-- 10. market_cap
CREATE TABLE IF NOT EXISTS market_cap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year REAL,
    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE (company_id, year),
    CHECK (year >= 1990 OR year IS NULL),
    CHECK (market_cap_crore IS NULL OR market_cap_crore >= 0)
);
CREATE INDEX IF NOT EXISTS idx_mc_company_year ON market_cap(company_id, year);

-- 11. documents
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year REAL,
    annual_report TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE (company_id, year),
    CHECK (year >= 1990 OR year IS NULL)
);
CREATE INDEX IF NOT EXISTS idx_doc_company_year ON documents(company_id, year);

-- 12. stock_prices
CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume REAL,
    adjusted_close REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE (company_id, date),
    CHECK (close_price >= 0 OR close_price IS NULL)
);
CREATE INDEX IF NOT EXISTS idx_sp_company_date ON stock_prices(company_id, date);
