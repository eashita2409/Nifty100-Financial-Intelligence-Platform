import pandas as pd
from src.analytics.kpi_engine import KPIEngine
engine = KPIEngine('data/db/nifty100.db', 'output/kpi_summary.csv')
engine.connect()
df = engine.calculate_kpis()
print(df[df['company_id'] == 'INFY'][['company_id', 'roe', 'roce']])
engine.close()
