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
    ('LINE_A', 'Natural Yogurt', 5000, 'Natural Yogurt Line 5000L/h'),
    ('LINE_B', 'Greek Yogurt', 4000, 'Greek Yogurt Line 4000L/h'),
    ('LINE_C', 'Fermented Milk', 3500, 'Fermented Milk Line 3500L/h')
]
cursor.executemany('INSERT INTO lines VALUES (?,?,?,?)', lines_data)

df = pd.read_csv('data/raw/production_data.csv')

df.drop(columns=['downtime_reasons']).to_sql('production', conn, if_exists='append', index=False)

cursor.execute("SELECT production_id, date, line_id, shift FROM production")
id_map = {(date, line, shift): prod_id for prod_id, date, line, shift in cursor.fetchall()}


downtime_translation = {
    'Manutenção Preventiva': 'Preventive Maintenance',
    'Falta de Insumos': 'Lack of Materials',
    'Limpeza CIP': 'CIP Cleaning',
    'Troca de Turno': 'Shift Change',
    'Quebra de Máquina': 'Machine Breakdown',
    'Ajuste de Processo': 'Process Adjustment'
}

contador = 0
for _, row in df.iterrows():
    prod_id = id_map.get((row['date'], row['line_id'], row['shift']))
    if not prod_id or pd.isna(row['downtime_reasons']) or row['downtime_reasons'] == '[]':
        continue
    
    try:
        for parada in ast.literal_eval(row['downtime_reasons']):
            original_reason = parada.get('reason', 'Unknown')
            # Translate if the reason is in our dictionary, otherwise use the original or 'Unknown'
            translated_reason = downtime_translation.get(original_reason, original_reason)
            if translated_reason == 'Desconhecido': translated_reason = 'Unknown'

            cursor.execute('INSERT INTO downtime_events VALUES (NULL,?,?,?)', 
                         (prod_id, translated_reason, parada.get('duration', 0)))
            contador += 1
    except:
        continue

daily = df.groupby(['date','line_id']).agg({'oee':'mean','units_produced':'sum','downtime_min':'sum'}).reset_index()

for _, row in daily.iterrows():
    cursor.execute('INSERT INTO daily_metrics VALUES (?,?,?,?,?)',
                  (row['date'], row['line_id'], round(row['oee'], 4), 
                   int(row['units_produced']), int(row['downtime_min'])))

conn.commit()
conn.close()
print(f"Database updated successfully! {contador} downtime events inserted.")