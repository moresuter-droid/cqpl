from flask import Flask, render_template, request, redirect, session
import sqlite3
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'cqpl_secret_key_2025'

def get_db():
    conn = sqlite3.connect('league.db')
    conn.row_factory = sqlite3.Row
    return conn

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

# ==================== ОБЩИЕ СТРАНИЦЫ ====================

@app.route('/')
def index():
    db = get_db()
    teams = db.execute('SELECT * FROM teams ORDER BY points DESC, wins DESC, goals_for DESC').fetchall()
    # Последние новости
    latest_news = db.execute('SELECT * FROM news ORDER BY created_date DESC LIMIT 3').fetchall()
    db.close()
    return render_template('index.html', teams=teams, news=latest_news)

@app.route('/news')
def news_list():
    db = get_db()
    news = db.execute('SELECT * FROM news ORDER BY created_date DESC').fetchall()
    db.close()
    return render_template('news_list.html', news=news)

@app.route('/news/<int:id>')
def news_detail(id):
    db = get_db()
    article = db.execute('SELECT * FROM news WHERE id = ?', (id,)).fetchone()
    other_news = db.execute('SELECT * FROM news WHERE id != ? ORDER BY created_date DESC LIMIT 3', (id,)).fetchall()
    db.close()
    return render_template('news_detail.html', article=article, other_news=other_news)

@app.route('/calendar')
def calendar():
    db = get_db()
    rounds = db.execute('SELECT DISTINCT round FROM matches ORDER BY round').fetchall()
    calendar_data = {}
    for r in rounds:
        matches = db.execute('''
            SELECT m.*, t1.name as home_name, t2.name as away_name
            FROM matches m
            JOIN teams t1 ON m.home_team_id = t1.id
            JOIN teams t2 ON m.away_team_id = t2.id
            WHERE m.round = ?
            ORDER BY m.match_date, m.id
        ''', (r['round'],)).fetchall()
        calendar_data[r['round']] = matches
    db.close()
    return render_template('calendar.html', calendar=calendar_data)

@app.route('/team/<int:id>')
def team(id):
    db = get_db()
    team_data = db.execute('SELECT * FROM teams WHERE id = ?', (id,)).fetchone()
    
    players = db.execute(
        'SELECT * FROM players WHERE team_id = ? ORDER BY goals DESC, number ASC', (id,)
    ).fetchall()
    
    # Все матчи команды
    all_matches = db.execute('''
        SELECT m.*, t1.name as home_name, t2.name as away_name
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
        WHERE (m.home_team_id = ? OR m.away_team_id = ?) AND m.status = 'finished'
        ORDER BY m.match_date DESC
    ''', (id, id)).fetchall()
    
    # Форма
    form = []
    for match in all_matches[:5]:
        is_home = match['home_team_id'] == id
        if is_home:
            if match['home_score'] > match['away_score']: form.append('W')
            elif match['home_score'] < match['away_score']: form.append('L')
            else: form.append('D')
        else:
            if match['away_score'] > match['home_score']: form.append('W')
            elif match['away_score'] < match['home_score']: form.append('L')
            else: form.append('D')
    
    db.close()
    return render_template('team.html', team=team_data, players=players, matches=all_matches, form=form)

@app.route('/player/<int:id>')
def player(id):
    db = get_db()
    player_data = db.execute('SELECT * FROM players WHERE id = ?', (id,)).fetchone()
    team_data = db.execute('SELECT * FROM teams WHERE id = ?', (player_data['team_id'],)).fetchone()
    
    # Матчи игрока с событиями
    player_events = db.execute('''
        SELECT e.*, m.match_date, m.round,
               t1.name as home_name, t2.name as away_name,
               m.home_score, m.away_score, m.home_team_id
        FROM events e
        JOIN matches m ON e.match_id = m.id
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
        WHERE e.player_id = ?
        ORDER BY m.match_date DESC
    ''', (id,)).fetchall()
    
    db.close()
    return render_template('player.html', player=player_data, team=team_data, events=player_events)

@app.route('/compare', methods=['GET'])
def compare():
    db = get_db()
    teams = db.execute('SELECT * FROM teams ORDER BY name').fetchall()
    t1 = t2 = None
    team1_id = request.args.get('team1')
    team2_id = request.args.get('team2')
    if team1_id and team2_id:
        t1 = db.execute('SELECT * FROM teams WHERE id=?', (team1_id,)).fetchone()
        t2 = db.execute('SELECT * FROM teams WHERE id=?', (team2_id,)).fetchone()
    db.close()
    return render_template('compare.html', teams=teams, t1=t1, t2=t2)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/scorers')
def scorers():
    db = get_db()
    top_scorers = db.execute('''
        SELECT p.*, t.name as team_name
        FROM players p JOIN teams t ON p.team_id = t.id
        ORDER BY p.goals DESC, p.assists DESC
    ''').fetchall()
    db.close()
    return render_template('scorers.html', scorers=top_scorers)

@app.route('/assists')
def assists():
    db = get_db()
    players = db.execute('''
        SELECT p.*, t.name as team_name FROM players p
        JOIN teams t ON p.team_id = t.id
        ORDER BY p.assists DESC
    ''').fetchall()
    db.close()
    return render_template('assists.html', players=players)

@app.route('/cards')
def cards():
    db = get_db()
    players = db.execute('''
        SELECT p.*, t.name as team_name FROM players p
        JOIN teams t ON p.team_id = t.id
        ORDER BY p.red_cards DESC, p.yellow_cards DESC
    ''').fetchall()
    db.close()
    return render_template('cards.html', players=players)

# ==================== АДМИН ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        admin = db.execute('SELECT * FROM admin WHERE username = ? AND password = ?', (username, password)).fetchone()
        db.close()
        if admin:
            session['admin'] = username
            return redirect('/admin')
        else:
            error = 'Неверный логин или пароль'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

@app.route('/admin')
@admin_required
def admin():
    db = get_db()
    matches = db.execute('''
        SELECT m.*, t1.name as home_name, t2.name as away_name
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
        ORDER BY m.match_date, m.round, m.id
    ''').fetchall()
    news = db.execute('SELECT * FROM news ORDER BY created_date DESC').fetchall()
    db.close()
    return render_template('admin.html', matches=matches, news=news)

@app.route('/match/<int:id>', methods=['GET', 'POST'])
@admin_required
def match(id):
    db = get_db()
    match_data = db.execute('''
        SELECT m.*, t1.name as home_name, t2.name as away_name
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
        WHERE m.id = ?
    ''', (id,)).fetchone()
    
    home_players = db.execute('SELECT * FROM players WHERE team_id = ?', (match_data['home_team_id'],)).fetchall()
    away_players = db.execute('SELECT * FROM players WHERE team_id = ?', (match_data['away_team_id'],)).fetchall()
    
    # Существующие события
    existing_events = db.execute('''
        SELECT e.*, p.name as player_name, p.number as player_number
        FROM events e
        JOIN players p ON e.player_id = p.id
        WHERE e.match_id = ?
        ORDER BY e.minute
    ''', (id,)).fetchall()
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'update_score':
            home_score = int(request.form['home_score'])
            away_score = int(request.form['away_score'])
            
            # Откат старой статистики
            if match_data['status'] == 'finished':
                old_home = match_data['home_score']
                old_away = match_data['away_score']
                for team_id, gf, ga in [(match_data['home_team_id'], old_home, old_away), (match_data['away_team_id'], old_away, old_home)]:
                    db.execute('UPDATE teams SET games = games - 1, goals_for = goals_for - ?, goals_against = goals_against - ? WHERE id = ?', (gf, ga, team_id))
                if old_home > old_away:
                    db.execute('UPDATE teams SET wins = wins - 1, points = points - 3 WHERE id = ?', (match_data['home_team_id'],))
                    db.execute('UPDATE teams SET losses = losses - 1 WHERE id = ?', (match_data['away_team_id'],))
                elif old_away > old_home:
                    db.execute('UPDATE teams SET wins = wins - 1, points = points - 3 WHERE id = ?', (match_data['away_team_id'],))
                    db.execute('UPDATE teams SET losses = losses - 1 WHERE id = ?', (match_data['home_team_id'],))
                else:
                    db.execute('UPDATE teams SET draws = draws - 1, points = points - 1 WHERE id IN (?, ?)', (match_data['home_team_id'], match_data['away_team_id']))
                
                # Удалить голы (события типа goal)
                db.execute('DELETE FROM events WHERE match_id = ? AND event_type = "goal"', (id,))
            
            # Новый счёт
            db.execute('UPDATE matches SET home_score = ?, away_score = ?, status = ? WHERE id = ?', (home_score, away_score, 'finished', id))
            
            for team_id, gf, ga in [(match_data['home_team_id'], home_score, away_score), (match_data['away_team_id'], away_score, home_score)]:
                db.execute('UPDATE teams SET games = games + 1, goals_for = goals_for + ?, goals_against = goals_against + ? WHERE id = ?', (gf, ga, team_id))
            
            if home_score > away_score:
                db.execute('UPDATE teams SET wins = wins + 1, points = points + 3 WHERE id = ?', (match_data['home_team_id'],))
                db.execute('UPDATE teams SET losses = losses + 1 WHERE id = ?', (match_data['away_team_id'],))
            elif away_score > home_score:
                db.execute('UPDATE teams SET wins = wins + 1, points = points + 3 WHERE id = ?', (match_data['away_team_id'],))
                db.execute('UPDATE teams SET losses = losses + 1 WHERE id = ?', (match_data['home_team_id'],))
            else:
                db.execute('UPDATE teams SET draws = draws + 1, points = points + 1 WHERE id IN (?, ?)', (match_data['home_team_id'], match_data['away_team_id']))
        
        elif action == 'add_event':
            player_id = int(request.form['player_id'])
            team_id = int(request.form['team_id'])
            event_type = request.form['event_type']
            minute = int(request.form['minute'])
            assist_id = request.form.get('assist_id', '')
            assist_id = int(assist_id) if assist_id else None
            
            db.execute('INSERT INTO events (match_id, player_id, team_id, event_type, minute, assist_player_id) VALUES (?, ?, ?, ?, ?, ?)',
                       (id, player_id, team_id, event_type, minute, assist_id))
            
            if event_type == 'goal':
                db.execute('UPDATE players SET goals = goals + 1 WHERE id = ?', (player_id,))
                if assist_id:
                    db.execute('UPDATE players SET assists = assists + 1 WHERE id = ?', (assist_id,))
            elif event_type == 'yellow':
                db.execute('UPDATE players SET yellow_cards = yellow_cards + 1 WHERE id = ?', (player_id,))
            elif event_type == 'red':
                db.execute('UPDATE players SET red_cards = red_cards + 1 WHERE id = ?', (player_id,))
        
        elif action == 'delete_event':
            event_id = int(request.form['event_id'])
            event = db.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
            if event:
                if event['event_type'] == 'goal':
                    db.execute('UPDATE players SET goals = goals - 1 WHERE id = ?', (event['player_id'],))
                    if event['assist_player_id']:
                        db.execute('UPDATE players SET assists = assists - 1 WHERE id = ?', (event['assist_player_id'],))
                elif event['event_type'] == 'yellow':
                    db.execute('UPDATE players SET yellow_cards = yellow_cards - 1 WHERE id = ?', (event['player_id'],))
                elif event['event_type'] == 'red':
                    db.execute('UPDATE players SET red_cards = red_cards - 1 WHERE id = ?', (event['player_id'],))
                db.execute('DELETE FROM events WHERE id = ?', (event_id,))
        
        db.commit()
        db.close()
        return redirect(f'/match/{id}')
    
    db.close()
    return render_template('match.html', match=match_data,
                           home_players=home_players, away_players=away_players,
                           events=existing_events)

# ==================== НОВОСТИ (админ) ====================

@app.route('/admin/news/add', methods=['GET', 'POST'])
@admin_required
def add_news():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        image = request.form.get('image', '')
        created_date = datetime.now().strftime('%Y-%m-%d')
        db = get_db()
        db.execute('INSERT INTO news (title, content, image, created_date, category) VALUES (?, ?, ?, ?, ?)',
                   (title, content, image, created_date, category))
        db.commit()
        db.close()
        return redirect('/admin')
    return render_template('add_news.html')

@app.route('/admin/news/delete/<int:id>')
@admin_required
def delete_news(id):
    db = get_db()
    db.execute('DELETE FROM news WHERE id = ?', (id,))
    db.commit()
    db.close()
    return redirect('/admin')

# ==================== КОМАНДА ТУРА ====================

@app.route('/team-of-week')
def team_of_week():
    db = get_db()
    # Получаем последний тур с матчами
    last_round = db.execute('SELECT MAX(round) FROM matches WHERE status = "finished"').fetchone()[0]
    
    totw = []
    if last_round:
        totw = db.execute('''
            SELECT tow.*, p.name as player_name, p.number, t.name as team_name, t.id as team_id
            FROM team_of_week tow
            JOIN players p ON tow.player_id = p.id
            JOIN teams t ON p.team_id = t.id
            WHERE tow.round = ?
            ORDER BY tow.id
        ''', (last_round,)).fetchall()
    
    # Все туры для навигации
    rounds = db.execute('SELECT DISTINCT round FROM team_of_week ORDER BY round DESC').fetchall()
    db.close()
    return render_template('team_of_week.html', totw=totw, rounds=rounds, selected_round=last_round)

@app.route('/team-of-week/<int:round_num>')
def team_of_week_round(round_num):
    db = get_db()
    totw = db.execute('''
        SELECT tow.*, p.name as player_name, p.number, t.name as team_name, t.id as team_id
        FROM team_of_week tow
        JOIN players p ON tow.player_id = p.id
        JOIN teams t ON p.team_id = t.id
        WHERE tow.round = ?
        ORDER BY tow.id
    ''', (round_num,)).fetchall()
    rounds = db.execute('SELECT DISTINCT round FROM team_of_week ORDER BY round DESC').fetchall()
    db.close()
    return render_template('team_of_week.html', totw=totw, rounds=rounds, selected_round=round_num)

# Админ: управление командой тура
@app.route('/admin/totw', methods=['GET', 'POST'])
@admin_required
def admin_totw():
    db = get_db()
    
    if request.method == 'POST':
        round_num = int(request.form['round'])
        # Удалить старую команду этого тура
        db.execute('DELETE FROM team_of_week WHERE round = ?', (round_num,))
        
        # Игроки по позициям
        for pos_key in ['gk', 'df1', 'df2', 'df3', 'df4', 'mf1', 'mf2', 'mf3', 'fw1', 'fw2', 'fw3']:
            player_id = request.form.get(pos_key)
            if player_id:
                if pos_key == 'gk':
                    position = 'Вратарь'
                elif pos_key.startswith('df'):
                    position = 'Защитник'
                elif pos_key.startswith('mf'):
                    position = 'Полузащитник'
                else:
                    position = 'Нападающий'
                db.execute('INSERT INTO team_of_week (round, player_id, position) VALUES (?, ?, ?)',
                          (round_num, player_id, position))
        
        db.commit()
        db.close()
        return redirect('/admin/totw')
    
    # Все игроки для выбора
    players = db.execute('''
        SELECT p.*, t.name as team_name
        FROM players p JOIN teams t ON p.team_id = t.id
        ORDER BY t.name, p.number
    ''').fetchall()
    
    # Существующие команды тура
    existing_rounds = db.execute('SELECT DISTINCT round FROM team_of_week ORDER BY round DESC').fetchall()
    
    db.close()
    return render_template('admin_totw.html', players=players, existing_rounds=existing_rounds)

if __name__ == '__main__':
    app.run()