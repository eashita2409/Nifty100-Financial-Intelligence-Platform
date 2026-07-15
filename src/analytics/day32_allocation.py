import sqlite3
import pandas as pd
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = _ROOT / "data" / "db" / "nifty100.db"
OUTPUT_DIR = _ROOT / "output"
EXCEL_PATH = OUTPUT_DIR / "cashflow_intelligence.xlsx"
PATTERN_CHANGES_CSV = OUTPUT_DIR / "pattern_changes.csv"

def classify_8_patterns(o, i, f):
    """Classify into one of 8 standard capital allocation/cashflow profiles."""
    if o >= 0 and i >= 0 and f >= 0:
        return "1: Liquidating / All Positive"
    elif o >= 0 and i >= 0 and f < 0:
        return "2: Restructuring / Debt Repayment"
    elif o >= 0 and i < 0 and f >= 0:
        return "3: Growing / Expanding"
    elif o >= 0 and i < 0 and f < 0:
        return "4: Healthy / Mature"
    elif o < 0 and i >= 0 and f >= 0:
        return "5: Struggling / Selling Assets"
    elif o < 0 and i >= 0 and f < 0:
        return "6: Bankrupt / Liquidation"
    elif o < 0 and i < 0 and f >= 0:
        return "7: Start-up / High Growth"
    elif o < 0 and i < 0 and f < 0:
        return "8: Distressed / Cash Burn"
    return "Unknown"

def run_day32():
    conn = sqlite3.connect(DB_PATH)
    
    # Verify Sprint 2 CSV
    sprint2_csv = OUTPUT_DIR / "capital_allocation.csv"
    if sprint2_csv.exists():
        df_sp2 = pd.read_csv(sprint2_csv)
        print(f"Verified {len(df_sp2)} rows in capital_allocation.csv")
    
    # Load all cashflows
    cf_df = pd.read_sql_query("SELECT * FROM cashflow ORDER BY company_id, year", conn)
    names_df = pd.read_sql_query("SELECT id AS company_id, company_name FROM companies", conn)
    
    cf_df["capital_allocation_label"] = cf_df.apply(
        lambda r: classify_8_patterns(r["operating_activity"], r["investing_activity"], r["financing_activity"]), axis=1
    )
    
    # 1. Update cashflow_intelligence.xlsx
    intel_df = pd.read_excel(EXCEL_PATH, sheet_name=None)
    for sheet_name, sheet_df in intel_df.items():
        if "company_id" in sheet_df.columns and "year" in sheet_df.columns:
            # Merge the new label
            sheet_df = sheet_df.merge(cf_df[["company_id", "year", "capital_allocation_label"]], on=["company_id", "year"], how="left")
            intel_df[sheet_name] = sheet_df
            
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        for sheet_name, sheet_df in intel_df.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
    print("Updated cashflow_intelligence.xlsx with capital_allocation_label.")
            
    # 2. Latest year distribution summary
    latest_cf = cf_df.sort_values("year").groupby("company_id").tail(1)
    dist = latest_cf["capital_allocation_label"].value_counts()
    print("\nLatest Year Distribution Summary (8 Patterns):")
    print(dist)
    
    # 3. Detect YoY changes
    cf_df = cf_df.sort_values(["company_id", "year"])
    cf_df["prev_pattern"] = cf_df.groupby("company_id")["capital_allocation_label"].shift(1)
    
    changes = cf_df[
        cf_df["prev_pattern"].notnull() & 
        (cf_df["prev_pattern"] != cf_df["capital_allocation_label"])
    ].copy()
    
    changes = changes.merge(names_df, on="company_id", how="left")
    
    changes_out = changes[["company_id", "company_name", "prev_pattern", "capital_allocation_label", "year"]]
    changes_out.columns = ["company_id", "company_name", "previous_pattern", "current_pattern", "change_year"]
    changes_out.to_csv(PATTERN_CHANGES_CSV, index=False)
    
    print(f"\nDetected {len(changes_out)} pattern changes. Saved to pattern_changes.csv")
    
    # Validate no duplicate company-year
    dups = cf_df.duplicated(subset=["company_id", "year"]).sum()
    print(f"\nDuplicate company-year records: {dups}")

if __name__ == "__main__":
    run_day32()
