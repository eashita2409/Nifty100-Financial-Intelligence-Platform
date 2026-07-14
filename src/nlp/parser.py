"""
Day 29 — NLP Analysis Parser
Parses the `analysis` table (originally sourced from analysis.xlsx) using regex.
Extracts compounded_sales_growth, compounded_profit_growth, stock_price_cagr, and roe
into structured rows and cross-validates parsed CAGRs against the Ratio Engine.

Output:
  output/analysis_parsed.csv
  output/parse_failures.csv
"""

import re
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

PARSED_CSV = OUTPUT_DIR / "analysis_parsed.csv"
FAILURES_CSV = OUTPUT_DIR / "parse_failures.csv"

# Logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("NLPParser")

# ─── Regex ────────────────────────────────────────────────────────────────────
# Matches patterns like:
#   "10 Years: 21%"   "5 Years:       22%"   "3 Years:  9%"   "TTM:  5%"   "Last Year: 17%"
#   "1 Year: 13%"
PERIOD_MAP = {
    "10": 10, "5": 5, "3": 3, "1": 1,
    "ttm": 0, "last year": 1,
}

PATTERN = re.compile(
    r"""
    (?P<period>\d+\s*Years?|TTM|Last\s+Year|1\s+Year)   # period label
    \s*:?\s*                                               # separator
    (?P<value>[\d.]+)\s*%                                  # value %
    """,
    re.IGNORECASE | re.VERBOSE,
)

METRIC_COLUMNS = {
    "compounded_sales_growth": "compounded_sales_growth",
    "compounded_profit_growth": "compounded_profit_growth",
    "stock_price_cagr": "stock_price_cagr",
    "roe": "roe",
}


def _normalise_period(period_str: str) -> int:
    """Convert period label to integer years."""
    p = period_str.strip().lower()
    if p == "ttm":
        return 0
    if "last year" in p or p == "1 year":
        return 1
    m = re.search(r"(\d+)", p)
    return int(m.group(1)) if m else -1


def parse_cell(company_id: str, metric_type: str, raw_text: str):
    """Parse a single analysis cell into structured records."""
    records = []
    failures = []

    if not isinstance(raw_text, str) or raw_text.strip() == "":
        failures.append({
            "company_id": company_id,
            "metric_type": metric_type,
            "raw_text": raw_text,
            "reason": "empty or non-string",
        })
        return records, failures

    match = PATTERN.search(raw_text)
    if match:
        period_years = _normalise_period(match.group("period"))
        try:
            value_pct = float(match.group("value"))
        except ValueError:
            failures.append({
                "company_id": company_id,
                "metric_type": metric_type,
                "raw_text": raw_text,
                "reason": "could not parse value as float",
            })
            return records, failures

        records.append({
            "company_id": company_id,
            "metric_type": metric_type,
            "period_years": period_years,
            "value_pct": value_pct,
        })
    else:
        failures.append({
            "company_id": company_id,
            "metric_type": metric_type,
            "raw_text": raw_text,
            "reason": "no regex match",
        })

    return records, failures


def parse_analysis_table(conn: sqlite3.Connection):
    """Parse all rows in the analysis table."""
    df = pd.read_sql_query("SELECT * FROM analysis", conn)
    logger.info(f"Read {len(df)} rows from analysis table ({df['company_id'].nunique()} companies)")

    all_records = []
    all_failures = []

    for _, row in df.iterrows():
        company_id = row["company_id"]
        for col_name in METRIC_COLUMNS:
            raw = row.get(col_name, "")
            recs, fails = parse_cell(company_id, col_name, raw)
            all_records.extend(recs)
            all_failures.extend(fails)

    parsed_df = pd.DataFrame(all_records, columns=["company_id", "metric_type", "period_years", "value_pct"])
    failures_df = pd.DataFrame(all_failures, columns=["company_id", "metric_type", "raw_text", "reason"])
    return parsed_df, failures_df


def cross_validate(parsed_df: pd.DataFrame, conn: sqlite3.Connection,
                   divergence_threshold: float = 5.0):
    """
    Cross-validate parsed CAGR values against the Ratio Engine columns in financial_ratios.
    Flag rows where divergence > divergence_threshold %.
    """
    # Only revenue and profit CAGR can be cross-validated from financial_ratios
    CAGR_MAP = {
        "compounded_sales_growth": {5: "revenue_cagr_5yr", 3: "revenue_cagr_3yr", 10: "revenue_cagr_10yr"},
        "compounded_profit_growth": {5: "pat_cagr_5yr", 3: "pat_cagr_3yr", 10: "pat_cagr_10yr"},
    }

    ratios_df = pd.read_sql_query(
        """
        SELECT company_id, year, revenue_cagr_3yr, revenue_cagr_5yr, revenue_cagr_10yr,
               pat_cagr_3yr, pat_cagr_5yr, pat_cagr_10yr
        FROM financial_ratios
        """,
        conn
    )
    latest = (
        ratios_df.dropna(subset=["year"])
        .sort_values("year", ascending=False)
        .groupby("company_id")
        .first()
        .reset_index()
    )

    divergent_rows = []
    for _, row in parsed_df.iterrows():
        metric = row["metric_type"]
        period = int(row["period_years"])
        if metric not in CAGR_MAP or period not in CAGR_MAP[metric]:
            continue

        col = CAGR_MAP[metric][period]
        company_match = latest[latest["company_id"] == row["company_id"]]
        if company_match.empty:
            continue
        ratio_val = company_match.iloc[0][col]
        if pd.isna(ratio_val):
            continue

        parsed_val = row["value_pct"]
        divergence = abs(parsed_val - ratio_val)
        if divergence > divergence_threshold:
            divergent_rows.append({
                "company_id": row["company_id"],
                "metric_type": metric,
                "period_years": period,
                "parsed_value_pct": parsed_val,
                "ratio_engine_value_pct": round(ratio_val, 2),
                "divergence_pct": round(divergence, 2),
            })

    if divergent_rows:
        logger.warning(f"Cross-validation: {len(divergent_rows)} rows flagged with divergence > {divergence_threshold}%")
        for r in divergent_rows:
            logger.warning(f"  {r['company_id']} | {r['metric_type']} ({r['period_years']}y): "
                           f"parsed={r['parsed_value_pct']}, ratio={r['ratio_engine_value_pct']}, "
                           f"divergence={r['divergence_pct']}%")
    else:
        logger.info("Cross-validation: No divergence > 5% detected.")

    return divergent_rows


def run_parser():
    logger.info("Starting NLP Analysis Parser (Day 29)")
    conn = sqlite3.connect(DB_PATH)

    parsed_df, failures_df = parse_analysis_table(conn)

    # Cross-validate
    cross_validate(parsed_df, conn)
    conn.close()

    # Save outputs
    parsed_df.to_csv(PARSED_CSV, index=False)
    failures_df.to_csv(FAILURES_CSV, index=False)

    logger.info(f"Parsed records: {len(parsed_df)} | Failures: {len(failures_df)}")
    logger.info(f"Saved: {PARSED_CSV}")
    logger.info(f"Saved: {FAILURES_CSV}")

    return parsed_df, failures_df


if __name__ == "__main__":
    run_parser()
