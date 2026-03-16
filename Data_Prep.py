import pandas as pd
import numpy as np

df = pd.read_csv('data/raw/production_data.csv')

oee_by_line = (df.groupby('line_id')['oee'].mean() * 100).rename('OEE')
describe_by_line = df.groupby('line_id')['oee'].describe()

oeemean = df['oee'].mean()*(100)
print('Average OEE per line:')
print(oee_by_line.map('{:.2f}%'.format))
print('OEE statistics per line:')
print(describe_by_line.map('{:.2f}'.format))
print(f'General average OEE is: {oeemean:.2f}%')

oee_by_shift = (df.groupby('shift')['oee'].mean() * 100).rename('OEE')
print("OEE per shift:")
print(oee_by_shift.map('{:.2f}%'.format))