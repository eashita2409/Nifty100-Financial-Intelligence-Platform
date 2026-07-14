# Nifty100 Financial Intelligence Platform

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-300%2B%20passing-brightgreen)
![Version](https://img.shields.io/badge/version-v4.0.0--sprint4-blue)
![Streamlit](https://img.shields.io/badge/dashboard-Streamlit-red)

> **Sprint 4 — Complete**  
> Bluestock Fintech | Equity Analytics Division

---

## 🎯 Project Objective

The **Nifty100 Financial Intelligence Platform** is a data engineering and analytics system designed to ingest, validate, transform, and report on financial data for all **Nifty 100 constituents** listed on the National Stock Exchange (NSE) of India.

The platform automates the full data lifecycle — from raw CSV/Excel ingestion through to structured database storage, quantitative analytics, and an interactive **Streamlit analytics dashboard** — enabling portfolio managers, quant analysts, and risk teams to make data-driven decisions with confidence.

---

## 👥 Team & Sprint

- **Client**: Bluestock Fintech
- **Progress**: Sprint 1 ✓ | Sprint 2 ✓ | Sprint 3 ✓ | Sprint 4 ✓
- **Current Status**: Sprint 4 Complete
- **Release**: v4.0.0-sprint4

---

## 📈 Project Progress

| Sprint | Status | Major Deliverables |
|--------|--------|--------------------|
| Sprint 1 | ✅ Complete | ETL Pipeline, Data Validation, SQLite Warehouse, Data Quality Framework |
| Sprint 2 | ✅ Complete | Financial Ratio Engine, CAGR Engine, Cash Flow KPIs, 50+ KPIs, Edge Case Handling |
| Sprint 3 | ✅ Complete | Financial Screener, Composite Quality Score, Peer Comparison Engine, Radar Charts, Excel Reports |
| Sprint 4 | ✅ Complete | Streamlit Dashboard (8 screens), Valuation Engine, Sector Analysis, Capital Allocation, Annual Reports |

---

## 📊 Platform Statistics

| Metric | Value |
|--------|-------|
| Companies Tracked | 92 (Nifty 100) |
| Company-Year Records | 1,169+ |
| Financial KPIs | 50+ |
| Preset Screeners | 6 |
| Peer Groups | 11 |
| Analytics Modules | 20+ |
| Automated Tests | 300+ |
| Dashboard Pages | 8 |

---

## 🚀 Quick Start

### 1. Clone and enter the project
```bash
git clone <repo-url>
cd Nifty100_Financial_Intelligence_Platform
```

### 2. Environment Setup
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
```

### 3. Launch the Dashboard
```bash
streamlit run src/dashboard/app.py
```

The dashboard will open at `http://localhost:8501`.

### 4. Run the Valuation Engine
```bash
python src/analytics/valuation.py
```

Outputs:
- `output/valuation_summary.xlsx` — All 92 companies with PE flags
- `output/valuation_flags.csv` — Discount & Caution companies only

### 5. Run the Full Analytics Pipeline
```bash
python -m src.etl.loader
python -m src.etl.validator
python -m src.etl.database_loader
python -m src.analytics.query_runner
python -m src.analytics.kpi_engine
python src/analytics/valuation.py
```

### 6. Run the Test Suite
```bash
python -m pytest tests -v
```

---

## 🗂 Repository Structure

```text
Nifty100_Financial_Intelligence_Platform/
├── config/
│   └── screener_config.yaml        # 6 preset screener configurations
├── data/
│   ├── raw/                        # Unmodified source files
│   ├── processed/                  # Cleaned and transformed data
│   └── db/
│       └── nifty100.db             # SQLite warehouse (15+ tables)
├── src/
│   ├── etl/                        # ETL pipeline (loader, normalizer, validator, DB builder)
│   ├── analytics/                  # KPI Engine, Screener, Peer Engine, Valuation
│   │   ├── kpi_engine.py
│   │   ├── leverage.py
│   │   ├── peer.py
│   │   └── valuation.py            # NEW: FCF yield & PE benchmarking
│   ├── screener/
│   │   └── engine.py               # Composite Quality Score, filter logic
│   └── dashboard/                  # Streamlit dashboard (Sprint 4)
│       ├── app.py                  # Entry point
│       ├── pages/
│       │   ├── 01_home.py
│       │   ├── 02_profile.py
│       │   ├── 03_screener.py
│       │   ├── 04_peers.py
│       │   ├── 05_trends.py
│       │   ├── 06_sectors.py
│       │   ├── 07_capital.py
│       │   └── 08_reports.py
│       └── utils/
│           └── db.py               # Cached SQLite data access layer
├── tests/                          # 300+ unit and integration tests
├── reports/
│   └── radar_charts/
├── output/
│   ├── screener_output.xlsx
│   ├── peer_comparison.xlsx
│   ├── valuation_summary.xlsx      # NEW: 92-company valuation flags
│   └── valuation_flags.csv         # NEW: Discount & Caution companies
├── docs/                           # Project documentation and sprint specs
├── sql/                            # SQLite schemas and analytical queries
├── requirements.txt
├── Makefile
└── README.md
```

---

## 📊 Dashboard Screens

The Streamlit dashboard provides 8 interactive analytics screens accessible from the sidebar.

### 1. 🏠 Home

**Purpose**: Market-level summary and snapshot  
**Features**:
- 6 KPI cards: Average ROE, Median PE, Median D/E, Total Companies, Median Revenue CAGR, Debt-Free Count
- Year selector (2019–2024) in sidebar
- Sector distribution donut chart (Plotly Express)
- Top 5 Companies by Composite Quality Score

### 2. 👤 Company Profile

**Purpose**: Deep-dive analytics for a single company  
**Features**:
- Searchable dropdown (Ticker + Company Name)
- 6 KPI cards: ROE, ROCE, Net Profit Margin, Debt/Equity, Revenue CAGR (5Y), Latest FCF
- 10-year Revenue & PAT bar chart
- ROE vs. ROCE trend line chart
- Auto-generated Pros & Cons based on threshold rules
- Graceful N/A fallback for missing data

**Performance**: Average load time < 0.5s (Target: <3s) ✅

### 3. 🔍 Screener

**Purpose**: Filter Nifty 100 companies by financial criteria  
**Features**:
- 6 preset buttons: Quality, Value, Growth, Dividend, Debt Free, Turnaround
- Manual sliders for all parameters (ROE, ROCE, D/E, FCF, Revenue CAGR, PAT CAGR, PE, PB, Dividend Yield)
- Real-time filtered results table with Composite Quality Score ranking
- CSV download of filtered results
- Sector breakdown chart of screened universe

### 4. 👥 Peer Comparison

**Purpose**: Compare a company against its peer group  
**Features**:
- Peer group dropdown (11 groups)
- Interactive Plotly radar chart overlaying company percentiles vs. peer average
- KPI comparison table with benchmark company highlighting
- 6 dimensions: ROE, ROCE, Net Margin, D/E, FCF, Revenue CAGR

### 5. 📈 Trend Analysis

**Purpose**: 10-year historical financial trends for a company  
**Features**:
- Company search (full name or ticker)
- Multi-select metric picker (up to 3 simultaneous metrics)
- Available metrics: Revenue, Net Profit, ROE, ROCE, OPM, Revenue CAGR, PAT CAGR, FCF, D/E, Asset Turnover
- Plotly line chart with YoY % change annotations on each data point
- Shows "Data available for X years" notification
- Handles companies with <10 years of data gracefully
- Raw data expandable table

### 6. 🏭 Sector Analysis

**Purpose**: Cross-sector and intra-sector performance benchmarking  
**Features**:
- Broad sector dropdown filter
- **Bubble Chart** (Plotly Express): X=Revenue, Y=ROE, Size=Market Cap, Color=Sub Sector
- **Sub-sector Median KPI Charts** (2×3 bar chart grid):
  - Median ROE | Median ROCE | Median Revenue CAGR
  - Median PAT CAGR | Median D/E | Median FCF
- Raw medians data expandable table

### 7. 🌳 Capital Allocation

**Purpose**: Visualize how companies deploy capital  
**Features**:
- **Plotly Treemap**: All companies clustered by `capital_allocation_pattern`
  - Patterns: Aggressive Expansion, Cash Cow/Returner, Balanced, Cash Burn, etc.
- Pattern deep-dive panel:
  - Company count
  - Median ROE
  - Median FCF
  - Sortable company table with ROE, ROCE, FCF, D/E

### 8. 📄 Annual Reports

**Purpose**: Direct access to BSE-filed annual reports  
**Features**:
- Company search by name
- Lists all available report years for the company
- **Clickable BSE Annual Report links** (opens in browser)
- Red **"Report unavailable"** badge when no URL is stored
- Data sourced directly from `documents` SQLite table

---

## 🏗 Architecture

### Data Flow

```
Raw CSVs/Excel
      ↓
ETL Pipeline (src/etl/)
      ↓
SQLite Warehouse (nifty100.db)
      ├── companies
      ├── profitandloss
      ├── balancesheet
      ├── cashflow
      ├── financial_ratios
      ├── market_cap
      ├── sectors
      ├── peer_groups
      ├── peer_percentiles
      └── documents
      ↓
Analytics Engine (src/analytics/)
├── kpi_engine.py      → Calculated KPIs stored back to DB
├── leverage.py        → Leverage analysis
├── peer.py            → Peer percentile ranking
└── valuation.py       → FCF yield, PE benchmarking, flag generation
      ↓
Dashboard Layer (src/dashboard/)
├── utils/db.py        → @st.cache_data SQLite access functions
└── pages/             → 8 Streamlit pages
```

### Dashboard Caching Strategy
All database query functions in `src/dashboard/utils/db.py` are decorated with `@st.cache_data(ttl=600)`. This means:
- Data is fetched from SQLite once per session and cached for 10 minutes
- Page interactions (selectbox changes, button clicks) do NOT re-query the database
- Cache is invalidated after 600 seconds to pick up any new data loads

### Screener Architecture
```
User selects sliders / preset button
      ↓
Session State stores threshold parameters
      ↓
ScreenerEngine.fetch_data() → Joins financial_ratios + sectors + market_cap
      ↓
ScreenerEngine.calculate_composite_quality_score() → 0–100 quality score
      ↓
ScreenerEngine.apply_filters() → Applies threshold filters
      ↓
Filtered results displayed + CSV export enabled
```

---

## 📉 Valuation Engine

`src/analytics/valuation.py` runs as a standalone script to generate valuation intelligence.

### Metrics Calculated

| Metric | Formula |
|--------|---------|
| FCF Yield (%) | `(FCF / Market Cap) × 100` |
| Sector Median PE | Median PE for all companies in each broad sector (latest year) |
| PE vs. Sector Median | `((PE / Sector Median PE) - 1) × 100` |

### Flagging Rules

| Flag | Condition |
|------|-----------|
| **Caution** | PE > 1.5 × Sector Median PE |
| **Discount** | PE < 0.7 × Sector Median PE |
| **Fair** | Otherwise |

### Output Files

| File | Description |
|------|-------------|
| `output/valuation_summary.xlsx` | All 92 companies: PE, PB, EV_EBITDA, FCF Yield, flag |
| `output/valuation_flags.csv` | Only Discount & Caution companies (44 rows) |

**FY2024 Flag Distribution**: Fair: 48 | Discount: 30 | Caution: 14

---

## 🔄 Dashboard Workflow

### Typical Analyst Workflow

1. **Start at Home** → Get a market snapshot, check which sectors are performing  
2. **Go to Screener** → Click "Quality" preset or set manual thresholds → Download CSV  
3. **Open a company** → Switch to Company Profile → Review KPIs, trend charts, pros/cons  
4. **Check peers** → Switch to Peer Comparison → Select peer group → View radar chart  
5. **Dig into trends** → Switch to Trend Analysis → Overlay Revenue + ROE + FCF over 10 years  
6. **Validate sector positioning** → Switch to Sector Analysis → View bubble chart  
7. **Understand capital strategy** → Switch to Capital Allocation → Explore treemap  
8. **Download filings** → Switch to Annual Reports → Access BSE PDFs  

---

## 💡 UX Decisions

1. **Sidebar navigation** (Streamlit multi-page): Users don't need to remember page names — all 8 are visible in the sidebar at all times.
2. **Multi-select metric comparison (max 3)**: Limiting to 3 metrics prevents chart clutter while still allowing meaningful overlays.
3. **YoY % annotations on Trend charts**: Instead of forcing users to calculate year-over-year manually, the Trend page annotates the % change directly on the data point.
4. **Preset buttons on Screener**: One-click preset activation replaces the need to set 9 sliders manually, dramatically improving the time-to-insight.
5. **Red badge for missing reports**: Rather than showing an empty row or error, the Reports page shows a visually distinct red pill badge to communicate clearly that no report is available.
6. **Treemap → Table drill-down on Capital Allocation**: The treemap provides the macro overview; the pattern dropdown provides the micro detail — avoiding information overload.
7. **Graceful N/A rendering**: All KPI displays use a `safe_fmt()` helper that returns `"N/A"` for NaN values. No page crashes on missing data.

---

## ⚡ Performance Optimizations

| Optimization | Impact |
|---|---|
| `@st.cache_data(ttl=600)` on all DB functions | Eliminates redundant SQLite queries across page reloads |
| `fillna(0)` on screener data | Prevents NaN-induced filter failures |
| `dropna(subset=['year'])` on ratio/PL queries | Ensures latest-year detection is accurate |
| Single-company search in Trend Analysis | Avoids loading all companies' 10-year data simultaneously |
| Sector median pre-aggregation in Valuation Engine | Pre-computes medians once rather than row-by-row |

---

## 🛡 Edge Cases Handled

| Scenario | Handling |
|----------|----------|
| Company with <10 years of data | Trend page shows "Data available for X years" notification |
| Missing annual report URL | Red "Report unavailable" badge on Reports page |
| Financial sector companies (high D/E) | D/E filter bypassed for financials in Screener presets |
| NaN KPIs in Company Profile | `safe_fmt()` returns "N/A" gracefully |
| Empty screener results | Warning message with instructions to relax filters |
| Missing market cap (zero/null) | FCF Yield excluded from Valuation output for that company |
| Missing sector mapping | Sector shown as "N/A" in Company Profile |
| Bubble chart negative market cap | Filtered out before rendering to avoid Plotly ValueError |

---

## ⚠️ Known Limitations

1. **Real-time data**: The database contains static historical data up to FY2024. Live prices are not fetched.
2. **`use_container_width` deprecation**: Streamlit 1.59+ recommends `width='stretch'`; current code uses the deprecated parameter. Functionality is not impacted — only a console warning appears.
3. **Screener performance**: The Screener fetches the full screener dataset on each preset click due to Streamlit's execution model. This is mitigated by `@st.cache_data`.
4. **Peer group static assignment**: Peer groups are defined during Sprint 3 data processing and are not dynamically recalculated in the dashboard.

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Dashboard | Streamlit 1.59 |
| Charts | Plotly Express & Plotly Graph Objects |
| Data Wrangling | pandas, numpy |
| Database | SQLite3 |
| Valuation Output | openpyxl (Excel), CSV |
| Testing | pytest, Streamlit AppTest |
| Workflow | GNU Make |

---

## 📋 Sprint 4 Retrospective

### What Went Well
- All 8 Streamlit pages implemented with real SQLite data and zero placeholder content
- `@st.cache_data` caching strategy dramatically reduced repeated database hits
- Plotly treemap, scatter (bubble), and radar chart implementations worked cleanly
- Valuation engine produced accurate PE benchmarking and flags for all 92 companies
- Company Profile average load time achieved **0.37s**, well under the 3s target
- All edge cases (missing data, financial sector D/E, <10 year companies) handled gracefully

### Challenges Overcome
- **ModuleNotFoundError**: Resolved by ensuring `src/` was always at the top of `sys.path` for all page imports
- **Screener returning 0 results**: Fixed by applying `fillna(0)` to the screener dataset before filter logic
- **N/A KPI values in Profile**: Fixed by adding `dropna(subset=['year'])` to all ratio queries, preventing incorrect latest-year resolution
- **Session state conflicts on Screener sliders**: Resolved preset-to-slider state synchronization

### Sprint 4 Exit Criteria

| Criteria | Status |
|----------|--------|
| All 8 screens load without errors | ✅ |
| Company profile loads in <3s | ✅ (avg 0.37s) |
| CSV export generates valid file | ✅ |
| valuation_summary.xlsx has 92 companies | ✅ |
| valuation_flags.csv generated | ✅ (44 rows) |
| No runtime/import errors | ✅ |
| No SQL errors | ✅ |
| No Plotly errors | ✅ |
| Missing values display N/A | ✅ |
| No page crashes | ✅ |

**Sprint 4 Status: ✅ COMPLETE**

---

## 🎯 Releases

| Version | Status | Notes |
|---------|--------|-------|
| v1.0.0-sprint1 | ✅ Complete | ETL, Validation, SQLite |
| v2.0.0-sprint2 | ✅ Complete | Ratio Engine, KPI Engine |
| v3.0.0-sprint3 | ✅ Complete | Screener, Peer Analytics, Excel Reports |
| v4.0.0-sprint4 | ✅ Complete | Streamlit Dashboard, Valuation Engine |

---

## 📝 Licence

Internal project — Bluestock Fintech. All rights reserved.
