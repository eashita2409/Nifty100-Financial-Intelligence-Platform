"""
STEP 8: PIPELINE VALIDATION (corrected)
"""
import traceback
from pathlib import Path

stages = []

# Stage 1: Loader
print("=" * 60)
print("STAGE 1: ETL Loader")
print("=" * 60)
try:
    from src.etl.loader import run_pipeline
    results = run_pipeline()
    print(f"  Pipeline completed successfully")
    stages.append(("ETL Loader", "PASS"))
except Exception as e:
    print(f"  ERROR: {e}")
    stages.append(("ETL Loader", f"FAIL: {e}"))

# Stage 2: Validator
print("\n" + "=" * 60)
print("STAGE 2: Validator")
print("=" * 60)
try:
    from src.etl.validator import run_validation
    summary, failures = run_validation(
        processed_dir=Path('data/processed'),
        failures_path=Path('output/validation_failures.csv'),
        summary_path=Path('output/dq_summary.csv')
    )
    total_rules = len(summary)
    total_failures = len(failures)
    print(f"  Rules executed: {total_rules}")
    print(f"  Failures found: {total_failures}")
    stages.append(("Validator", "PASS"))
except Exception as e:
    print(f"  ERROR: {e}")
    traceback.print_exc()
    stages.append(("Validator", f"FAIL: {e}"))

# Stage 3: Database Loader
print("\n" + "=" * 60)
print("STAGE 3: Database Loader")
print("=" * 60)
try:
    from src.etl.database_loader import SQLiteLoader
    loader = SQLiteLoader(
        db_path='data/db/nifty100.db',
        schema_path='db/schema.sql',
        audit_path='data/processed/pipeline_audit.csv'
    )
    loader.connect()
    loader.init_schema()
    print(f"  Schema verified successfully")
    loader.close()
    stages.append(("Database Loader", "PASS"))
except Exception as e:
    print(f"  ERROR: {e}")
    traceback.print_exc()
    stages.append(("Database Loader", f"FAIL: {e}"))

# Stage 4: Ratio Engines
print("\n" + "=" * 60)
print("STAGE 4: Ratio Engine")
print("=" * 60)
try:
    from src.analytics.ratios import populate_profitability_ratios
    from src.analytics.leverage import populate_leverage_ratios
    populate_leverage_ratios('data/db/nifty100.db')
    populate_profitability_ratios('data/db/nifty100.db')
    print(f"  Profitability and Leverage ratios populated")
    stages.append(("Ratio Engine", "PASS"))
except Exception as e:
    print(f"  ERROR: {e}")
    stages.append(("Ratio Engine", f"FAIL: {e}"))

# Stage 5: KPI Engine
print("\n" + "=" * 60)
print("STAGE 5: KPI Engine")
print("=" * 60)
try:
    from src.analytics.kpi_engine import KPIEngine
    engine = KPIEngine('data/db/nifty100.db', 'output/kpi_summary.csv')
    engine.generate_report()
    print(f"  KPI report generated successfully")
    stages.append(("KPI Engine", "PASS"))
except Exception as e:
    print(f"  ERROR: {e}")
    stages.append(("KPI Engine", f"FAIL: {e}"))

# Summary
print("\n" + "=" * 60)
print("PIPELINE SUMMARY")
print("=" * 60)
all_pass = True
for name, status in stages:
    icon = "PASS" if status == "PASS" else "FAIL"
    print(f"  [{icon}] {name}: {status}")
    if status != "PASS":
        all_pass = False

print(f"\nOverall: {'ALL STAGES PASSED' if all_pass else 'SOME STAGES FAILED'}")
