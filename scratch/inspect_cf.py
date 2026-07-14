import sqlite3, pandas as pd
conn = sqlite3.connect('data/db/nifty100.db')
df = pd.read_sql_query("""
    SELECT fr.company_id, fr.year, fr.cash_from_operations_cr, fr.capex_cr,
           fr.free_cash_flow_cr, fr.total_debt_cr, fr.net_debt_cr,
           fr.cfo_quality_score, fr.capex_intensity, fr.fcf_conversion,
           fr.capital_allocation_pattern,
           cf.financing_activity, p.net_profit, p.sales
    FROM financial_ratios fr
    LEFT JOIN cashflow cf ON fr.company_id=cf.company_id AND fr.year=cf.year
    LEFT JOIN profitandloss p ON fr.company_id=p.company_id AND fr.year=p.year
    WHERE fr.company_id IN ('TCS','HDFCBANK','RELIANCE')
    ORDER BY fr.company_id, fr.year DESC LIMIT 12
""", conn)
print(df.to_string())
conn.close()
