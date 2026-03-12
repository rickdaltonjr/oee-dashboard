import sqlite3
import pandas as pd
import ast

conn = sqlite3.connect('database/oee_database.db')
cursor = conn.cursor()

cursor.execute("DELETE FROM daily_metrics")
cursor.execute("DELETE FROM downtime_events")
cursor.execute("DELETE FROM production")
cursor.execute("DELETE FROM lines")
conn.commit()

lines_data = [
    ('LINHA_A', 'Iogurte Natural', 5000, 'Linha de iogurte natural 5000L/h'),
    ('LINHA_B', 'Iogurte Grego', 4000, 'Linha de iogurte grego 4000L/h'),
    ('LINHA_C', 'Leite Fermentado', 3500, 'Linha de leite fermentado 3500L/h')
]
cursor.executemany('INSERT INTO lines VALUES (?,?,?,?)', lines_data)

df = pd.read_csv('data/raw/production_data.csv')
df.drop(columns=['downtime_reasons']).to_sql('production', conn, if_exists='append', index=False)

cursor.execute("SELECT production_id, date, line_id, shift FROM production")
id_map = {(date, line, shift): prod_id for prod_id, date, line, shift in cursor.fetchall()}

contador = 0
for _, row in df.iterrows():
    prod_id = id_map.get((row['date'], row['line_id'], row['shift']))
    if not prod_id or pd.isna(row['downtime_reasons']) or row['downtime_reasons'] == '[]':
        continue
    
    try:
        for parada in ast.literal_eval(row['downtime_reasons']):
            cursor.execute('INSERT INTO downtime_events VALUES (NULL,?,?,?)', 
                         (prod_id, parada.get('reason','Desconhecido'), parada.get('duration',0)))
            contador += 1
    except:
        continue


daily = df.groupby(['date','line_id']).agg({'oee':'mean','units_produced':'sum','downtime_min':'sum'}).reset_index()

for _, row in daily.iterrows():
    cursor.execute('INSERT INTO daily_metrics VALUES (?,?,?,?,?)',
                  (row['date'], row['line_id'], round(row['oee'],4), 
                   int(row['units_produced']), int(row['downtime_min'])))

conn.commit()

# Verificação
print("RESULTADO:")
for tabela in ['lines','production','downtime_events','daily_metrics']:
    cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
    print(f"   {tabela}: {cursor.fetchone()[0]}")

conn.close()