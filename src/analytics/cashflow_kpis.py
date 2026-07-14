"""
Day 31 — Cash Flow Intelligence
Computes extended cash flow KPIs and generates intelligence reports.

Metrics:
  - CFO Quality Score  (CFO / Net Profit)
  - CapEx Intensity    (CapEx / Sales)
  - FCF Conversion     (FCF / Net Profit)
  - Distress Signal    (CFO < 0 AND Net Profit < 0)
  - Deleveraging Flag  (Financing Activity < 0 AND Net Debt declining YoY)
  - Capital Allocation Label (already computed by cashflow_kpis.py, reused)

Output files:
  output/cashflow_intelligence.xlsx   (full company-year breakdown)
  output/distress_alerts.csv          (companies flagged for distress)
"""

import sqlite3
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# ─── Paths ────────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = _ROOT / "data" / "db" / "nifty100.db"
OUTPUT_DIR = _ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXCEL_PATH = OUTPUT_DIR / "cashflow_intelligence.xlsx"
DISTRESS_CSV = OUTPUT_DIR / "distress_alerts.csv"

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("CashflowIntelligence")


# ─── Data Fetch ───────────────────────────────────────────────────────────────
def fetch_data(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT
            fr.company_id,
            fr.year,
            fr.cash_from_operations_cr      AS cfo,
            fr.capex_cr                     AS capex,
            fr.free_cash_flow_cr            AS fcf,
            fr.total_debt_cr                AS total_debt,
            fr.net_debt_cr                  AS net_debt,
            fr.cfo_quality_score,
            fr.capex_intensity,
            fr.fcf_conversion,
            fr.capital_allocation_pattern,
            cf.operating_activity           AS raw_cfo,
            cf.investing_activity,
            cf.financing_activity,
            p.net_profit,
            p.sales,
            p.interest,
            s.broad_sector
        FROM financial_ratios fr
        LEFT JOIN cashflow cf
            ON fr.company_id = cf.company_id AND fr.year = cf.year
        LEFT JOIN profitandloss p
            ON fr.company_id = p.company_id AND fr.year = p.year
        LEFT JOIN sectors s
            ON fr.company_id = s.company_id
        WHERE fr.year IS NOT NULL
        ORDER BY fr.company_id, fr.year
        """,
        conn,
    )


# ─── KPI Calculations ─────────────────────────────────────────────────────────
def _safe(val, default=np.nan):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    return float(val)


def compute_distress_signal(cfo: float, net_profit: float) -> int:
    """
    Distress Signal = 1 if CFO < 0 AND Net Profit < 0 simultaneously.
    Indicates both operational cash drain and accounting loss.
    """
    if np.isnan(cfo) or np.isnan(net_profit):
        return 0
    return int(cfo < 0 and net_profit < 0)


def compute_deleveraging_flag(financing_activity: float, net_debt: float,
                               prev_net_debt: float) -> int:
    """
    Deleveraging = 1 if:
      - Financing outflow (financing_activity < 0) — company is paying down debt/equity
      - AND Net Debt is declining YoY (net_debt < prev_net_debt)
    """
    if np.isnan(financing_activity) or np.isnan(net_debt) or np.isnan(prev_net_debt):
        return 0
    return int(financing_activity < 0 and net_debt < prev_net_debt)


def compute_cfo_quality(cfo: float, net_profit: float) -> float:
    """CFO / Net Profit. Already stored in DB; recompute for transparency."""
    if np.isnan(net_profit) or net_profit == 0:
        return np.nan
    return round(cfo / net_profit, 3)


def compute_capex_intensity(capex: float, sales: float) -> float:
    """|CapEx| / Sales."""
    if np.isnan(sales) or sales == 0:
        return np.nan
    return round(abs(capex) / sales, 3)


def compute_fcf_conversion(fcf: float, net_profit: float) -> float:
    """FCF / Net Profit."""
    if np.isnan(net_profit) or net_profit == 0:
        return np.nan
    return round(fcf / net_profit, 3)


# ─── Main Engine ──────────────────────────────────────────────────────────────
def build_intelligence(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all KPIs on the joined DataFrame."""
    # Sort for lag calculations
    df = df.sort_values(["company_id", "year"]).reset_index(drop=True)

    records = []
    for company_id, grp in df.groupby("company_id"):
        grp = grp.reset_index(drop=True)
        for i, row in grp.iterrows():
            cfo = _safe(row["cfo"])
            capex = _safe(row["capex"])
            fcf = _safe(row["fcf"])
            net_profit = _safe(row["net_profit"])
            sales = _safe(row["sales"])
            fin_act = _safe(row["financing_activity"])
            net_debt = _safe(row["net_debt"])

            # Previous year net_debt for deleveraging calc
            prev_net_debt = _safe(grp.iloc[i - 1]["net_debt"]) if i > 0 else np.nan

            # KPIs
            cfo_quality = compute_cfo_quality(cfo, net_profit)
            capex_int = compute_capex_intensity(capex, sales)
            fcf_conv = compute_fcf_conversion(fcf, net_profit)
            distress = compute_distress_signal(cfo, net_profit)
            deleveraging = compute_deleveraging_flag(fin_act, net_debt, prev_net_debt)

            # Capital allocation pattern (already in DB, reuse or recompute)
            cap_pattern = row.get("capital_allocation_pattern") or _classify_capital(cfo, capex, fcf, fin_act)

            records.append({
                "company_id": company_id,
                "year": row["year"],
                "broad_sector": row.get("broad_sector"),
                "cfo_cr": round(cfo, 2) if not np.isnan(cfo) else None,
                "capex_cr": round(capex, 2) if not np.isnan(capex) else None,
                "fcf_cr": round(fcf, 2) if not np.isnan(fcf) else None,
                "net_profit_cr": round(net_profit, 2) if not np.isnan(net_profit) else None,
                "sales_cr": round(sales, 2) if not np.isnan(sales) else None,
                "financing_activity_cr": round(fin_act, 2) if not np.isnan(fin_act) else None,
                "net_debt_cr": round(net_debt, 2) if not np.isnan(net_debt) else None,
                "cfo_quality_score": cfo_quality,
                "capex_intensity": capex_int,
                "fcf_conversion": fcf_conv,
                "distress_signal": distress,
                "deleveraging_flag": deleveraging,
                "capital_allocation_pattern": cap_pattern,
            })

    return pd.DataFrame(records)


def _classify_capital(cfo, capex, fcf, financing_activity) -> str:
    """Fallback capital allocation classification."""
    if np.isnan(cfo) or cfo < 0:
        return "Cash Burn"
    if not np.isnan(capex) and abs(capex) > cfo:
        return "Aggressive Expansion"
    if not np.isnan(fcf) and fcf > 0 and not np.isnan(financing_activity) and financing_activity < 0:
        return "Cash Cow / Returner"
    return "Stable / Moderate Reinvestment"


# ─── Distress Alerts ──────────────────────────────────────────────────────────
def build_distress_alerts(intel_df: pd.DataFrame) -> pd.DataFrame:
    """
    Distress alerts for companies where distress_signal = 1 in the latest year.
    Columns: company_id, year, broad_sector, cfo_cr, net_profit_cr,
             fcf_cr, distress_signal, capital_allocation_pattern, alert_reason
    """
    latest = (
        intel_df.dropna(subset=["year"])
        .sort_values("year", ascending=False)
        .groupby("company_id")
        .first()
        .reset_index()
    )

    distressed = latest[latest["distress_signal"] == 1].copy()
    distressed["alert_reason"] = "CFO < 0 and Net Profit < 0 in most recent year"

    cols = [
        "company_id", "year", "broad_sector",
        "cfo_cr", "net_profit_cr", "fcf_cr",
        "distress_signal", "capital_allocation_pattern", "alert_reason",
    ]
    return distressed[[c for c in cols if c in distressed.columns]].reset_index(drop=True)


# ─── Runner ───────────────────────────────────────────────────────────────────
def run_cashflow_intelligence():
    logger.info("Starting Cash Flow Intelligence Engine (Day 31)")

    conn = sqlite3.connect(DB_PATH)
    raw_df = fetch_data(conn)
    conn.close()

    logger.info(f"Fetched {len(raw_df)} company-year rows from database")

    intel_df = build_intelligence(raw_df)
    logger.info(f"Computed intelligence for {len(intel_df)} company-year records")

    distress_df = build_distress_alerts(intel_df)
    logger.info(f"Distress alerts: {len(distress_df)} companies flagged")

    # ── Write Excel (multi-sheet) ─────────────────────────────────────────────
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        # Sheet 1: Full intelligence table
        intel_df.to_excel(writer, sheet_name="Cashflow_Intelligence", index=False)

        # Sheet 2: Latest year snapshot
        latest_snap = (
            intel_df.dropna(subset=["year"])
            .sort_values("year", ascending=False)
            .groupby("company_id")
            .first()
            .reset_index()
        )
        latest_snap.to_excel(writer, sheet_name="Latest_Snapshot", index=False)

        # Sheet 3: Distress alerts
        distress_df.to_excel(writer, sheet_name="Distress_Alerts", index=False)

        # Sheet 4: Deleveraging companies (latest year)
        deleveraging = latest_snap[latest_snap["deleveraging_flag"] == 1]
        deleveraging.to_excel(writer, sheet_name="Deleveraging", index=False)

    logger.info(f"Saved: {EXCEL_PATH}")

    # ── Write distress CSV ────────────────────────────────────────────────────
    distress_df.to_csv(DISTRESS_CSV, index=False)
    logger.info(f"Saved: {DISTRESS_CSV}")

    # Summary stats
    latest = latest_snap
    logger.info(f"Summary (latest year per company):")
    logger.info(f"  Avg CFO Quality Score: {latest['cfo_quality_score'].mean():.2f}")
    logger.info(f"  Avg CapEx Intensity: {latest['capex_intensity'].mean():.2f}")
    logger.info(f"  Distressed companies: {latest['distress_signal'].sum()}")
    logger.info(f"  Deleveraging companies: {latest['deleveraging_flag'].sum()}")

    patterns = latest["capital_allocation_pattern"].value_counts()
    logger.info(f"  Capital allocation distribution:\n{patterns.to_string()}")

    return intel_df, distress_df


if __name__ == "__main__":
    run_cashflow_intelligence()
