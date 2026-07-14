import pandas as pd
df = pd.read_excel('output/valuation_summary.xlsx')
print('Total rows:', len(df))
print('Columns:', df.columns.tolist())
print()
print('Flag distribution:')
print(df['flag'].value_counts())
print()
# Spot check specific tickers requested in spec
for ticker in ['TCS', 'INFY', 'RELIANCE', 'HDFCBANK', 'ITC', 'BEL', 'HAL', 'NTPC', 'SUNPHARMA', 'ASIANPAINT']:
    row = df[df['company_id'] == ticker]
    if not row.empty:
        r = row.iloc[0]
        pe = r['PE']
        flag = r['flag']
        fcf = r['FCF_yield_pct']
        print(f"{ticker}: PE={pe}, Flag={flag}, FCF_yield={fcf:.2f}%")
    else:
        print(f"{ticker}: NOT FOUND")

flags_df = pd.read_csv('output/valuation_flags.csv')
print()
print('valuation_flags.csv rows:', len(flags_df))
print('Flags breakdown:', flags_df['flag'].value_counts().to_dict())
