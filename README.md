# Nifty100 Financial Intelligence Platform

An automated end-to-end analytical ecosystem engineered to analyze the fundamental health and metrics of the top 100 Indian companies (Nifty100).

## 🚀 Project Overview

The Nifty100 Financial Intelligence Platform ingests, processes, and visualizes over a decade's worth of fundamental data (Profit & Loss, Cashflow, Balance Sheets, and Market Cap). It transforms raw tabular data into structured SQLite relations, computes 30+ sophisticated Key Performance Indicators (KPIs), applies statistical learning (K-Means Clustering), and generates high-level visual reports. 

## ✨ Features

- **Automated ETL Pipeline**: Cleans missing years, drops bad data, handles NaN interpolations, and normalizes unstructured schemas natively into SQLite.
- **KPI Engine**: Generates dynamic Financial Ratios: ROE, ROCE, P/E, EPS CAGR, FCF Conversion, and CFO Quality.
- **Streamlit Dashboard**: A robust multi-page application with customized Glassmorphic styling providing 8 deep-dive modules (Home, Profile, Screener, Peers, Trends, Sectors, Cashflow, Reports).
- **FastAPI Backend**: A production-ready REST API featuring 16 endpoints to decouple backend logic from UI rendering, ready for cloud-native deployment.
- **Screener & Peer Analytics**: Cross-compares peer groups algorithmically, ranks by Composite Quality Scores, and exposes deep "Value Trap" and "Distress" screeners.
- **NLP Insights Generator**: Produces text-based PROs and CONs directly from raw SQL numerical tables using logic-based confidence scoring.
- **Automated Report Generation**: Single-click PDF tear-sheet production via ReportLab.
- **Automated QA Pipeline**: 350+ `pytest` unit/integration tests running at 79% global coverage guaranteeing 0 regression.

## 📂 Folder Structure

```
Root/
├── data/                    # SQLite databases (nifty100.db) & Raw CSVs
├── docs/                    # Architecture diagrams & Analyst Guide (PDF)
├── output/                  # Generated CSVs, Clustering Data, Excel dumps
├── reports/                 # Auto-generated PDFs (Tearsheets, Sector Reports)
├── src/                     # Core Python Modules
│   ├── analytics/           # KPI, CAGR, Peer, and Clustering logic
│   ├── api/                 # FastAPI configuration (Routers, Services)
│   ├── dashboard/           # Streamlit Web UI Pages & Styling
│   ├── etl/                 # Loaders, Normalizers, Validators
│   ├── nlp/                 # Rule-based natural language generator
│   └── reports/             # ReportLab PDF building logic
├── tests/                   # Extensive Pytest suites
└── README.md                # This file
```

## 🛠️ Installation & Requirements

### Requirements
- Python 3.12 or newer.
- Dependencies defined in `requirements.txt` (FastAPI, Streamlit, Pandas, Scikit-Learn, ReportLab, Pytest).

### Setup Guide
1. Clone this repository locally.
2. Create and activate a Virtual Environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate   # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Seed the database (First run only):
   ```bash
   python src/etl/database_loader.py
   python src/analytics/kpi_engine.py
   ```

## 📊 Dashboard Usage

Launch the full interactive analytical frontend locally:
```bash
streamlit run src/dashboard/app.py
```
*Navigate to `http://localhost:8501`. Use the sidebar to swap between Profile, Sector Analysis, and Peer comparisons.*

## ⚡ FastAPI Backend Usage

Deploy the API server enabling REST access to the Nifty100 models:
```bash
uvicorn src.api.main:app --port 8000
```
*Access interactive documentation at `http://localhost:8000/docs`.*

### Example API Requests

**1. Retrieve Nifty100 Companies List**
```bash
curl http://localhost:8000/companies
```

**2. Fetch Historic Ratios for Reliance**
```bash
curl http://localhost:8000/ratios/RELIANCE
```

**3. Get Sector Aggregates**
```bash
curl http://localhost:8000/sector/Energy
```

## 🧪 Testing

Execute the complete testing and QA pipeline (350+ integration tests):
```bash
pytest tests/ --html=reports/pytest_report.html --cov=src --cov-report=term-missing
```

## 📸 Screenshots

*(Dashboard images generated dynamically. Check `artifacts/` folder for visual UI references.)*

## 📦 Deliverables Summary

1. SQLite Relational Architecture (`data/db/nifty100.db`).
2. Streamlit Analytical Dashboard (`src/dashboard/app.py`).
3. K-Means Risk/Return Models (`output/cluster_labels.csv`).
4. Automated Tear-sheets and PDF pipelines (`reports/portfolio/portfolio_summary.pdf`).
5. Analyst Guide Handover Document (`docs/analyst_guide.pdf`).
6. Zero-regression test pipeline (`tests/`).

## 💻 Technologies Used
**Python 3.12** • **Pandas** • **Streamlit** • **FastAPI** • **SQLite** • **Pytest** • **ReportLab** • **Scikit-Learn** • **Plotly**
