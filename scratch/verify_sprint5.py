"""Sprint 5 Days 29-31 Verification"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"

PASS = "[PASS]"
FAIL = "[FAIL]"
issues = []

def check(cond, label, detail=""):
    status = PASS if cond else FAIL
    print(f"  {status} {label}" + (f": {detail}" if detail else ""))
    if not cond:
        issues.append(f"{label}: {detail}")

print("=" * 60)
print("DAY 29 — analysis_parsed.csv")
print("=" * 60)
df_parsed = pd.read_csv(OUTPUT / "analysis_parsed.csv")
check(len(df_parsed) > 0, "Has rows", f"{len(df_parsed)} rows")
check(list(df_parsed.columns) == ["company_id","metric_type","period_years","value_pct"], 
      "Correct columns", str(df_parsed.columns.tolist()))
check(df_parsed['company_id'].nunique() > 0, "Has companies", str(df_parsed['company_id'].unique()))
check((df_parsed['period_years'].isin([0,1,3,5,10])).all(), "Valid periods")
check((df_parsed['value_pct'] >= 0).all(), "Non-negative values")
print()
print("  Metrics breakdown:")
print(df_parsed.groupby('metric_type')['period_years'].count().to_string())

print()
print("=" * 60)
print("DAY 29 — parse_failures.csv")
print("=" * 60)
df_fail = pd.read_csv(OUTPUT / "parse_failures.csv")
check("company_id" in df_fail.columns, "Has company_id column")
check("reason" in df_fail.columns, "Has reason column")
print(f"  Failures: {len(df_fail)}")
if len(df_fail):
    print(df_fail.to_string())

print()
print("=" * 60)
print("DAY 30 — pros_cons_generated.csv")
print("=" * 60)
df_pc = pd.read_csv(OUTPUT / "pros_cons_generated.csv")
required_cols = ["company_id","type","rule_id","text","confidence_pct"]
check(all(c in df_pc.columns for c in required_cols), "Correct columns")
check((df_pc['type'].isin(['PRO','CON'])).all(), "Only PRO/CON types")
check((df_pc['confidence_pct'] > 60).all(), "All confidence > 60")
n_companies = df_pc['company_id'].nunique()
check(n_companies == 92, "All 92 companies covered", f"{n_companies} companies")
# Verify every company has at least 1 PRO and 1 CON
pros = set(df_pc[df_pc['type']=='PRO']['company_id'])
cons = set(df_pc[df_pc['type']=='CON']['company_id'])
all_cos = set(df_pc['company_id'])
missing_pro = all_cos - pros
missing_con = all_cos - cons
check(len(missing_pro) == 0, "Every company has >= 1 PRO", f"Missing: {missing_pro}")
check(len(missing_con) == 0, "Every company has >= 1 CON", f"Missing: {missing_con}")
print(f"  Total rules: {len(df_pc)} | PROs: {(df_pc['type']=='PRO').sum()} | CONs: {(df_pc['type']=='CON').sum()}")
print(f"  Rule IDs used: {sorted(df_pc['rule_id'].unique())}")

print()
print("=" * 60)
print("DAY 31 — cashflow_intelligence.xlsx")
print("=" * 60)
xl = pd.read_excel(OUTPUT / "cashflow_intelligence.xlsx", sheet_name=None)
check("Cashflow_Intelligence" in xl, "Sheet: Cashflow_Intelligence")
check("Latest_Snapshot" in xl, "Sheet: Latest_Snapshot")
check("Distress_Alerts" in xl, "Sheet: Distress_Alerts")
check("Deleveraging" in xl, "Sheet: Deleveraging")

df_intel = xl["Cashflow_Intelligence"]
required_intel_cols = ["company_id","year","cfo_quality_score","capex_intensity",
                        "fcf_conversion","distress_signal","deleveraging_flag","capital_allocation_pattern"]
for col in required_intel_cols:
    check(col in df_intel.columns, f"Column '{col}' present")
check(len(df_intel) > 0, "Has rows", f"{len(df_intel)} rows")
check(df_intel['company_id'].nunique() == 92, "All 92 companies", f"{df_intel['company_id'].nunique()}")

df_latest = xl["Latest_Snapshot"]
check(df_latest['company_id'].nunique() == 92, "Latest snapshot: 92 companies")
print(f"  Distressed (latest yr): {df_latest['distress_signal'].sum()}")
print(f"  Deleveraging (latest yr): {df_latest['deleveraging_flag'].sum()}")
print(f"  Capital patterns: {df_latest['capital_allocation_pattern'].value_counts().to_dict()}")

print()
print("=" * 60)
print("DAY 31 — distress_alerts.csv")
print("=" * 60)
df_dist = pd.read_csv(OUTPUT / "distress_alerts.csv")
check("company_id" in df_dist.columns, "Has company_id column")
check("distress_signal" in df_dist.columns, "Has distress_signal column")
print(f"  Distress alerts: {len(df_dist)} companies")

print()
print("=" * 60)
print("FINAL SUMMARY")
print("=" * 60)
if not issues:
    print("  [ALL CHECKS PASSED] Sprint 5 Days 29-31 COMPLETE")
else:
    print(f"  {len(issues)} ISSUE(S) FOUND:")
    for i in issues:
        print(f"    - {i}")
