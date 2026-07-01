import sqlite3

conn = sqlite3.connect('league.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS odds (
        id INTEGER PRIMARY KEY,
        match_id INTEGER,
        home_win REAL DEFAULT 2.0,
        draw REAL DEFAULT 3.0,
        away_win REAL DEFAULT 2.0,
        FOREIGN KEY (match_id) REFERENCES matches(id)
    )
''')

conn.commit()
conn.close()
print('Таблица коэффициентов добавлена!')
