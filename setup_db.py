import sqlite3

conn = sqlite3.connect('league.db')
cursor = conn.cursor()

# Таблица команд
cursor.execute('''
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY,
        name TEXT,
        logo TEXT DEFAULT '',
        games INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        draws INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        goals_for INTEGER DEFAULT 0,
        goals_against INTEGER DEFAULT 0,
        points INTEGER DEFAULT 0
    )
''')

# Таблица игроков
cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY,
        name TEXT,
        number INTEGER,
        position TEXT,
        team_id INTEGER,
        goals INTEGER DEFAULT 0,
        assists INTEGER DEFAULT 0
    )
''')

# 10 команд
teams = [
    'Спартак', 'Динамо', 'Локомотив', 'Зенит', 'ЦСКА',
    'Краснодар', 'Ростов', 'Рубин', 'Ахмат', 'Урал'
]

for name in teams:
    cursor.execute('INSERT INTO teams (name) VALUES (?)', (name,))

# Игроки для каждой команды
positions = ['Вратарь', 'Защитник', 'Защитник', 'Защитник', 'Защитник',
             'Полузащитник', 'Полузащитник', 'Полузащитник', 'Нападающий', 'Нападающий', 'Нападающий']

for team_id in range(1, 11):
    for num in range(1, 12):
        pos = positions[num-1]
        name = f'Игрок {num} ({pos})'
        cursor.execute(
            'INSERT INTO players (name, number, position, team_id) VALUES (?, ?, ?, ?)',
            (name, num, pos, team_id)
        )

conn.commit()
conn.close()
print('База готова! 10 команд и 110 игроков добавлены.')
