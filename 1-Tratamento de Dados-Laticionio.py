import pandas as pd
import numpy as np

df = pd.read_csv('data/raw/production_data.csv')
#verificando a tabela
#print(df.head())

oee_by_line = (df.groupby('line_id')['oee'].mean() * 100).rename('OEE')
describe_by_line = df.groupby('line_id')['oee'].describe()

# média geral de OEE
oeemean = df['oee'].mean()*(100)
print('A média de OEE por linha:')
print(oee_by_line.map('{:.2f}%'.format))
print(describe_by_line.map('{:.2f}'.format))
print(f'A média de OEE geral é: {oeemean:.2f}%')

#Qual turno tem o melhor OEE médio?
oee_by_shift = (df.groupby('shift')['oee'].mean() * 100).rename('OEE')
print("\n📊 OEE por Turno:")
print(oee_by_shift.map('{:.2f}%'.format))

#Filtre apenas turnos com OEE médio acima de 85%
high_oee_shifts = oee_by_shift [oee_by_shift > 77]
print("\n📈 Turnos com OEE médio acima de 77%:")
print(high_oee_shifts.map('{:.2f}'.format))

#Crie uma coluna 'status': 'Bom' se OEE > 80%, senão 'Precisa melhorar'
df['status'] = np.where(df['oee'] > 0.80, 'Bom', 'Precisa melhorar')
print("\nStatus de OEE para cada registro:")
print(df[['line_id', 'shift', 'oee', 'status']])

#Quantas linhas tem OEE 'Bom' vs 'Precisa melhorar'?
status_counts = df['status'].value_counts()
print("\nContagem de status de OEE:")
print(status_counts)

#Qual linha tem mais registros 'Bom'?
bom_counts = df[df['status'] == 'Bom']['line_id'].value_counts()
print("\nLinhas com mais registros 'Bom':")
print(bom_counts)

#Qual linha tem mais registros 'Precisa melhorar'?
precisa_melhorar_counts = df[df['status'] == 'Precisa melhorar']['line_id'].value_counts()
print("\nLinhas com mais registros 'Precisa melhorar':")
print(precisa_melhorar_counts)
