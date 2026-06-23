# =============================================================================
# Nifty100 Financial Intelligence Platform — Makefile
# Bluestock Fintech | Sprint 1
# =============================================================================
# Usage:
#   make load       - Ingest raw data files into the processed layer
#   make validate   - Run data validation checks on processed data
#   make test       - Execute the full pytest test suite
#   make report     - Generate summary reports and visualisations
#   make clean      - Remove generated files (processed data + outputs)
# =============================================================================

PYTHON      := python
PIP         := pip
SRC_DIR     := src
TEST_DIR    := tests
OUTPUT_DIR  := output
PROCESSED   := data/processed
DB_DIR      := data/db

.PHONY: all load validate test report clean install help

# ── Default target ────────────────────────────────────────────────────────────
all: load validate test report

# ── Install dependencies ──────────────────────────────────────────────────────
install:
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt
	@echo "Done."

# ── Load: Run ETL pipeline to ingest raw data ─────────────────────────────────
load:
	@echo "============================================================"
	@echo " LOAD — Ingesting raw data files..."
	@echo "============================================================"
	$(PYTHON) -m src.etl.load
	@echo "Load complete."

# ── Validate: Run data quality checks ─────────────────────────────────────────
validate:
	@echo "============================================================"
	@echo " VALIDATE — Running data validation checks..."
	@echo "============================================================"
	$(PYTHON) -m src.etl.validate
	@echo "Validation complete."

# ── Test: Execute pytest suite ────────────────────────────────────────────────
test:
	@echo "============================================================"
	@echo " TEST — Running pytest suite..."
	@echo "============================================================"
	$(PYTHON) -m pytest $(TEST_DIR)/ -v --tb=short
	@echo "Tests complete."

# ── Report: Generate output reports and charts ────────────────────────────────
report:
	@echo "============================================================"
	@echo " REPORT — Generating reports and visualisations..."
	@echo "============================================================"
	$(PYTHON) -m src.etl.report
	@echo "Reports saved to $(OUTPUT_DIR)/"

# ── Clean: Remove generated and processed files ───────────────────────────────
clean:
	@echo "============================================================"
	@echo " CLEAN — Removing generated files..."
	@echo "============================================================"
	@if exist $(PROCESSED)\* del /Q $(PROCESSED)\*
	@if exist $(OUTPUT_DIR)\* del /Q $(OUTPUT_DIR)\*
	@if exist $(DB_DIR)\*.db del /Q $(DB_DIR)\*.db
	@echo "Clean complete."

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "Nifty100 Financial Intelligence Platform — Available Commands"
	@echo "──────────────────────────────────────────────────────────────"
	@echo "  make install   Install Python dependencies from requirements.txt"
	@echo "  make load      Ingest raw data files (ETL extract + transform)"
	@echo "  make validate  Run data validation and quality checks"
	@echo "  make test      Execute pytest unit and integration tests"
	@echo "  make report    Generate summary reports and charts to output/"
	@echo "  make clean     Remove processed data, DB files, and outputs"
	@echo "  make all       Run: load → validate → test → report"
	@echo ""
