import sqlite3
import pandas as pd

conn = sqlite3.connect('database/oee_database.db')
cursor = conn.cursor()

print("DataBase Conected: database/oee_database.db")

cursor.execute('''
CREATE TABLE IF NOT EXISTS production (
    production_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    line_id TEXT NOT NULL,
    product TEXT NOT NULL,
    shift INTEGER NOT NULL,
    available_time_min INTEGER,
    production_time_min INTEGER,
    downtime_min INTEGER,
    units_produced INTEGER,
    defective_units INTEGER,
    good_units INTEGER,
    availability REAL,
    performance REAL,
    quality REAL,
    oee REAL
)
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS downtime_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    production_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    duration_min INTEGER NOT NULL,
    FOREIGN KEY (production_id) REFERENCES production(production_id)
)
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS lines (
        line_id VARCHAR(10) PRIMARY KEY,
        product VARCHAR(50) NOT NULL,
        capacity_per_hour INTEGER NOT NULL,
        description TEXT
    )
    ''')
    
cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_metrics (
        date DATE NOT NULL,
        line_id VARCHAR(10) NOT NULL,
        avg_oee DECIMAL(5,4),
        total_produced INTEGER,
        total_downtime INTEGER,
        PRIMARY KEY (date, line_id)
    )
    ''')
    
conn.commit()
print("Tables created successfully")
conn.close()