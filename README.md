# Nifty100 Financial Intelligence Platform

> **Sprint 1 · Day 1 — Project Setup**  
> Bluestock Fintech | Equity Analytics Division

---

## 🎯 Project Objective

The **Nifty100 Financial Intelligence Platform** is a data engineering and analytics system designed to ingest, validate, transform, and report on financial data for all **Nifty 100 constituents** listed on the National Stock Exchange (NSE) of India.

The platform automates the full data lifecycle — from raw CSV/Excel ingestion through to structured database storage and executive-grade reporting — enabling portfolio managers, quant analysts, and risk teams to make data-driven decisions with confidence.

---

## 🗂 Repository Structure

```
Nifty100_Financial_Intelligence_Platform/
├── data/
│   ├── raw/            # Unmodified source files (NAV CSVs, price data, etc.)
│   ├── processed/      # Cleaned and transformed data ready for DB load
│   └── db/             # SQLite database files (local dev)
├── src/
│   └── etl/            # ETL pipeline modules (extract, transform, load)
├── tests/
│   └── etl/            # Unit and integration tests for ETL modules
├── notebooks/          # Exploratory analysis and prototyping (Jupyter)
├── output/             # Generated reports, charts, and exports
├── docs/               # Project documentation and sprint specs
├── .env.example        # Environment variable template
├── requirements.txt    # Python dependencies
├── Makefile            # Developer workflow commands
└── README.md           # This file
```

---

## 🚀 Sprint 1 Goals

Sprint 1 establishes the **data foundation** of the platform across 5 working days:

| Day | Focus Area | Deliverable |
|-----|-----------|-------------|
| **Day 1** | Project Setup | Folder structure, config, tooling, documentation |
| **Day 2** | ETL Development | Ingest raw NAV/price CSV files into structured format |
| **Day 3** | Data Validation | Schema checks, null handling, outlier detection |
| **Day 4** | Database Load | Persist validated data to SQLite via SQLAlchemy |
| **Day 5** | Reporting | Generate summary reports and visualisations |

### Sprint 1 Acceptance Criteria
- [ ] All Nifty 100 constituent NAV data ingested without data loss
- [ ] Validated dataset stored in `data/db/nifty100.db`
- [ ] Test coverage ≥ 80% for ETL modules
- [ ] Summary report generated in `output/`
- [ ] `make load && make validate && make test && make report` runs end-to-end cleanly

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Data Wrangling | pandas, numpy |
| File I/O | openpyxl (Excel), csv (built-in) |
| Database ORM | SQLAlchemy |
| Testing | pytest |
| Visualisation | matplotlib, seaborn |
| Config Management | python-dotenv |
| Workflow | GNU Make |

---

## ⚡ Quick Start

### 1. Clone and enter the project
```bash
git clone <repo-url>
cd Nifty100_Financial_Intelligence_Platform
```

### 2. Create and activate a virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your local settings
```

### 5. Place raw data files
Drop your Nifty 100 NAV CSV/Excel files into `data/raw/`.

### 6. Run the full pipeline
```bash
make load       # Ingest raw data
make validate   # Run data validation
make test       # Execute test suite
make report     # Generate output reports
```

---

## 🧹 Makefile Commands

| Command | Description |
|---------|-------------|
| `make load` | Run ETL pipeline to ingest raw data |
| `make validate` | Execute data validation checks |
| `make test` | Run the full pytest test suite |
| `make report` | Generate summary reports and charts |
| `make clean` | Remove processed data and generated outputs |

---

## 📄 Data Sources

- **NAV Data**: Mutual fund NAV CSV exports (AMFI format)
- **Price Data**: NSE daily price/volume files
- **Index Composition**: Nifty 100 constituent list (NSE website)

---

## 👥 Team & Sprint

- **Client**: Bluestock Fintech  
- **Sprint**: Sprint 1 (Days 1–5)  
- **Start Date**: 23 June 2026  
- **Status**: 🟡 In Progress — Day 1 Setup

---

## 📝 Licence

Internal project — Bluestock Fintech. All rights reserved.
