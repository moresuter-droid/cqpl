import sqlite3
import os
import random
from datetime import date, timedelta

if os.path.exists('league.db'):
    os.remove('league.db')

conn = sqlite3.connect('league.db')
cursor = conn.cursor()

# Админ
cursor.execute('CREATE TABLE admin (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')
cursor.execute("INSERT INTO admin (username, password) VALUES ('admin', 'cqpl2025')")

# Команды
cursor.execute('''
    CREATE TABLE teams (
        id INTEGER PRIMARY KEY, name TEXT, logo TEXT DEFAULT '',
        games INTEGER DEFAULT 0, wins INTEGER DEFAULT 0, draws INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0, goals_for INTEGER DEFAULT 0, goals_against INTEGER DEFAULT 0,
        points INTEGER DEFAULT 0
    )
''')

# Игроки
cursor.execute('''
    CREATE TABLE players (
        id INTEGER PRIMARY KEY, name TEXT, number INTEGER, position TEXT,
        team_id INTEGER, goals INTEGER DEFAULT 0, assists INTEGER DEFAULT 0,
        yellow_cards INTEGER DEFAULT 0, red_cards INTEGER DEFAULT 0,
        FOREIGN KEY (team_id) REFERENCES teams(id)
    )
''')

# Матчи
cursor.execute('''
    CREATE TABLE matches (
        id INTEGER PRIMARY KEY, round INTEGER, home_team_id INTEGER, away_team_id INTEGER,
        home_score INTEGER DEFAULT 0, away_score INTEGER DEFAULT 0,
        match_date TEXT, status TEXT DEFAULT 'scheduled',
        FOREIGN KEY (home_team_id) REFERENCES teams(id),
        FOREIGN KEY (away_team_id) REFERENCES teams(id)
    )
''')

# События матча (голы, ассисты, карточки)
cursor.execute('''
    CREATE TABLE events (
        id INTEGER PRIMARY KEY, match_id INTEGER, player_id INTEGER, team_id INTEGER,
        event_type TEXT, minute INTEGER, assist_player_id INTEGER DEFAULT NULL,
        FOREIGN KEY (match_id) REFERENCES matches(id),
        FOREIGN KEY (player_id) REFERENCES players(id)
    )
''')

# Новости
cursor.execute('''
    CREATE TABLE news (
        id INTEGER PRIMARY KEY, title TEXT, content TEXT, image TEXT DEFAULT '',
        created_date TEXT, category TEXT DEFAULT 'general'
    )
''')

# 10 команд
teams = ['Құлағер', 'Бәйтерек', 'Алматы Сити', 'Техас', 'Бейбарыс',
         'Намыс', 'Қансонар', 'Қыран', 'Ақтөбе', 'Номад']
for name in teams:
    cursor.execute('INSERT INTO teams (name) VALUES (?)', (name,))

# Игроки
positions = ['Вратарь', 'Защитник', 'Защитник', 'Защитник', 'Защитник',
             'Полузащитник', 'Полузащитник', 'Полузащитник', 'Нападающий', 'Нападающий', 'Нападающий']
names_pool = [
    'Аслан', 'Ерлан', 'Нұрлан', 'Бауыржан', 'Данияр', 'Әлішер', 'Руслан', 'Арман',
    'Тимур', 'Айдос', 'Марат', 'Қайрат', 'Азамат', 'Дәурен', 'Ержан', 'Нұржан',
    'Әділет', 'Бекзат', 'Сұлтан', 'Али', 'Мейрам', 'Жандос', 'Рамазан', 'Нұрдәулет',
    'Мақсат', 'Абылай', 'Ерболат', 'Сәбит', 'Темірлан', 'Дидар'
]
random.seed(2025)
for team_id in range(1, 11):
    used_names = random.sample(names_pool, 11)
    for num in range(1, 12):
        cursor.execute('INSERT INTO players (name, number, position, team_id) VALUES (?, ?, ?, ?)',
                       (used_names[num-1], num, positions[num-1], team_id))

# Календарь
base_date = date(2025, 7, 1)
for round_num in range(1, 10):
    round_date = base_date + timedelta(days=(round_num-1) * 7)
    arr = list(range(1, 11))
    random.shuffle(arr)
    for i in range(0, 10, 2):
        cursor.execute('INSERT INTO matches (round, home_team_id, away_team_id, match_date, status) VALUES (?, ?, ?, ?, ?)',
                       (round_num, arr[i], arr[i+1], round_date.strftime('%Y-%m-%d'), 'scheduled'))

# Тестовые новости
news_data = [
    ('CQPL маусымы басталды!', 'Cyber Qazaqstan Premier League жаңа маусымы ресми түрде басталды. 10 команда чемпиондық үшін күреседі.', '2025-07-01', 'league'),
    ('Құлағер командасы жаңа ойыншылармен келісімшартқа отырды', 'Құлағер клубы 3 жаңа ойыншымен күшейтілді. Алдағы турларда команда мықты өнер көрсетеді деп күтілуде.', '2025-07-03', 'transfer'),
    ('1-турдың үздік ойыншысы анықталды', 'Алматы Сити командасының шабуылшысы 1-турдың үздік ойыншысы атанды.', '2025-07-05', 'players'),
    ('CQPL турнир кестесіндегі өзгерістер', '3-турдан кейін турнир кестесінде елеулі өзгерістер болды. Бәйтерек көшбасшылыққа шықты.', '2025-07-15', 'league'),
]
for title, content, cdate, cat in news_data:
    cursor.execute('INSERT INTO news (title, content, created_date, category) VALUES (?, ?, ?, ?)',
                   (title, content, cdate, cat))

conn.commit()
conn.close()
print('База CQPL толық жаңартылды!')
print('Логин: admin | Пароль: cqpl2025')
