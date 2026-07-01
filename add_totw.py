import sqlite3

conn = sqlite3.connect('league.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS team_of_week (
        id INTEGER PRIMARY KEY,
        round INTEGER,
        player_id INTEGER,
        position TEXT,
        FOREIGN KEY (player_id) REFERENCES players(id)
    )
''')

conn.commit()
conn.close()
print('Таблица team_of_week добавлена!')
