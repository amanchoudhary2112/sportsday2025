from flask import Flask, session, render_template, request, redirect, url_for, flash, send_file
import os
from datetime import datetime
import mysql.connector
import tempfile
import openpyxl
from functools import wraps

app = Flask(__name__)
app.secret_key = 'aman_key'

# -------------------- DATABASE CONFIG -------------------- #
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'sportsday'
}

# Initialize tables if they don't exist
def init_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            sport_selected VARCHAR(255),
            mobile VARCHAR(20),
            role VARCHAR(50),
            course VARCHAR(255)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INT AUTO_INCREMENT PRIMARY KEY,
            team_name VARCHAR(255),
            sport VARCHAR(255),
            leader VARCHAR(255),
            roll_no VARCHAR(50),
            member1 VARCHAR(255),
            member2 VARCHAR(255),
            member3 VARCHAR(255),
            member4 VARCHAR(255),
            timestamp DATETIME
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

init_db()

# -------------------- HELPER FUNCTIONS & DECORATORS -------------------- #

def get_db_connection():
    """Establishes and returns a database connection."""
    return mysql.connector.connect(**DB_CONFIG)

def admin_required(f):
    """Decorator to check for an active admin session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def download_to_excel(query, query_params, filename, sheet_name="Data"):
    """Fetches data and creates a downloadable Excel file."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, query_params)
    data = cursor.fetchall()
    headers = [i[0] for i in cursor.description]
    cursor.close()
    conn.close()

    if not data:
        flash(f"No data found for {sheet_name}.", 'warning')
        return redirect(url_for('participants'))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(headers)
    for row in data:
        ws.append(row)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(temp_file.name)

    return send_file(temp_file.name, as_attachment=True, download_name=filename)

def delete_from_table(table_name, row_id):
    """Deletes a row from a specified table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (row_id,))
    conn.commit()
    cursor.close()
    conn.close()

# -------------------- ROUTES -------------------- #

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            return redirect(url_for('participants'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/')
def index():
    sports = {
        'Badminton': '/static/images/badminton.webp',
        'Carrom Board': '/static/images/carrom board.jpg',
        'Chess': '/static/images/chessnew.jpg',
        'Table Tennis': '/static/images/table tennis.jpg',
        'Tug Of War': '/static/images/tug of war1.jpg',
        'Lemon Spoon Race': '/static/images/lemonspoon1.webp'
    }
    return render_template('index.html', sports=sports)

@app.route('/register')
def register():
    return render_template('choose_registration.html')

@app.route('/register/individual', defaults={'sport': None}, methods=['GET', 'POST'])
@app.route('/register/individual/<sport>', methods=['GET', 'POST'])
def register_individual(sport):
    sports_list = ['Badminton', 'Carrom Board', 'Chess', 'Table Tennis', 'Tug Of War','Lemon Race']
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        sport_selected = request.form['sport']
        mobile = request.form.get('mobile', '')
        role = request.form.get('role', '')

        # Only keep course if Student
        if role == 'Student':
            course = request.form.get('course', '')
        else:
            course = ' '  # Prevents Faculty from having a course

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO participants (name, email, sport_selected, mobile, role, course)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, email, sport_selected, mobile, role, course))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('success', name=name, sport=sport_selected))

    return render_template('register.html', sports=sports_list, selected_sport=sport)

@app.route('/register/team', methods=['GET', 'POST'])
def register_team():
    sports = ['Badminton', 'Carrom Board', 'Chess', 'Table Tennis', 'Tug Of War', 'Lemon Spoon Race']
    if request.method == 'POST':
        team_name = request.form['team_name']
        sport = request.form['sport']
        leader = request.form['leader']
        roll_no = request.form['roll_no']
        members = [request.form.get(f'member{i}', '') for i in range(1, 5)]
        timestamp = datetime.now()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO teams (team_name, sport, leader, roll_no, member1, member2, member3, member4, timestamp)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (team_name, sport, leader, roll_no, *members, timestamp))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('success', name=leader, sport=sport))
    return render_template('create_team.html', sports=sports)

@app.route('/success')
def success():
    name = request.args.get('name')
    sport = request.args.get('sport')
    return render_template('success.html', name=name, sport=sport)

@app.route('/gallery')
def gallery():
    sports_images = [
        "https://source.unsplash.com/800x600/?sports-day,athlete",
        "https://source.unsplash.com/801x601/?relay-race",
        "https://source.unsplash.com/802x602/?school-sports,celebration",
        "https://source.unsplash.com/803x603/?tug-of-war",
        "https://source.unsplash.com/804x604/?running,track",
        "https://source.unsplash.com/805x605/?prize-distribution",
        "https://source.unsplash.com/806x606/?sports-team,celebration",
        "https://source.unsplash.com/807x607/?school-sports-day",
        "https://source.unsplash.com/808x608/?track-and-field",
    ]
    return render_template('gallery.html', images=sports_images)

@app.route('/participants')
@admin_required
def participants():
    search_query = request.args.get('search', '').lower()
    conn = get_db_connection()

    # Create search pattern once
    search_pattern = f"%{search_query}%"

    # List of columns for each table
    participant_columns = ["name", "email", "sport_selected", "mobile", "role", "course"]
    team_columns = ["team_name", "sport", "leader", "roll_no", "member1", "member2", "member3", "member4"]

    cursor_participants = conn.cursor()
    cursor_teams = conn.cursor()

    # Build participants query
    if search_query:
        where_clause = " OR ".join([f"LOWER({col}) LIKE %s" for col in participant_columns])
        sql = f"SELECT id, name, email, sport_selected, mobile, role, course FROM participants WHERE {where_clause}"
        cursor_participants.execute(sql, tuple([search_pattern] * len(participant_columns)))
    else:
        cursor_participants.execute("SELECT id, name, email, sport_selected, mobile, role, course FROM participants")

    participants_data = cursor_participants.fetchall()

    # Build teams query
    if search_query:
        where_clause = " OR ".join([f"LOWER({col}) LIKE %s" for col in team_columns])
        sql = f"""
            SELECT id, team_name, sport, leader, roll_no, member1, member2, member3, member4, timestamp 
            FROM teams 
            WHERE {where_clause}
        """
        cursor_teams.execute(sql, tuple([search_pattern] * len(team_columns)))
    else:
        cursor_teams.execute("SELECT id, team_name, sport, leader, roll_no, member1, member2, member3, member4, timestamp FROM teams")

    teams_data = cursor_teams.fetchall()

    cursor_participants.close()
    cursor_teams.close()
    conn.close()

    return render_template(
        'participants.html', 
        participants=participants_data, 
        teams=teams_data, 
        current_year=datetime.now().year, 
        search_query=search_query
    )


@app.route('/download_all')
@admin_required
def download_all():
    query = "SELECT * FROM participants"
    return download_to_excel(query, (), "all_participants.xlsx", "Individual Participants")

@app.route('/download_all_teams')
@admin_required
def download_all_teams():
    query = "SELECT * FROM teams"
    return download_to_excel(query, (), "all_teams.xlsx", "Team Registrations")

@app.route('/download_sport/<sport>')
@admin_required
def download_sport(sport):
    query = "SELECT * FROM participants WHERE LOWER(sport_selected) = %s"
    return download_to_excel(query, (sport.lower(),), f"{sport}_participants.xlsx", "Individual Participants")

@app.route('/download_team_sport/<sport>')
@admin_required
def download_team_sport(sport):
    query = "SELECT * FROM teams WHERE LOWER(sport) = %s"
    return download_to_excel(query, (sport.lower(),), f"{sport}_teams.xlsx", "Team Registrations")

@app.route('/delete/<int:row_id>', methods=['POST'])
@admin_required
def delete_participant(row_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM participants WHERE id = %s", (row_id,))
    deleted_participant = cursor.fetchone()
    if deleted_participant:
        session['last_deleted'] = deleted_participant
    cursor.close()
    conn.close()
    delete_from_table("participants", row_id)
    flash("Participant deleted. You can undo this action.", "info")
    return redirect(url_for('participants'))

@app.route('/delete_team/<int:row_id>', methods=['POST'])
@admin_required
def delete_team(row_id):
    delete_from_table("teams", row_id)
    flash("Team deleted.", "info")
    return redirect(url_for('participants'))

@app.route('/undo_delete')
@admin_required
def undo_delete():
    deleted_participant = session.get('last_deleted')
    if deleted_participant:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO participants (id, name, email, sport_selected, mobile, role, course)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, deleted_participant[0:7])
        conn.commit()
        cursor.close()
        conn.close()
        session.pop('last_deleted', None)
        flash('Undo successful: Participant restored.', 'success')
    else:
        flash('No participant to undo.', 'warning')
    return redirect(url_for('participants'))

@app.route('/delete_all', methods=['POST'])
@admin_required
def delete_all():
    delete_from_table("participants", None) # No specific ID, deletes all
    delete_from_table("teams", None)       # No specific ID, deletes all
    flash("All participants and teams deleted.", "info")
    return redirect(url_for('participants'))

@app.route('/edit/<int:row_id>', methods=['GET', 'POST'])
@admin_required
def edit_participant(row_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        updated = (
            request.form['name'], request.form['email'], request.form['sport'],
            request.form['mobile'], request.form['role'], request.form['course'], row_id
        )
        cursor.execute("""
            UPDATE participants
            SET name=%s, email=%s, sport_selected=%s, mobile=%s, role=%s, course=%s
            WHERE id=%s
        """, updated)
        conn.commit()
        cursor.close()
        conn.close()
        flash('Participant updated successfully.', 'success')
        return redirect(url_for('participants'))
    cursor.execute("SELECT * FROM participants WHERE id = %s", (row_id,))
    participant = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit.html', participant=participant, row_id=row_id)

@app.route('/edit_team/<int:row_id>', methods=['GET', 'POST'])
@admin_required
def edit_team(row_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        updated = (
            request.form['team_name'], request.form['sport'], request.form['leader'],
            request.form['roll_no'], request.form.get('member1', ''),
            request.form.get('member2', ''), request.form.get('member3', ''),
            request.form.get('member4', ''), row_id
        )
        cursor.execute("""
            UPDATE teams
            SET team_name=%s, sport=%s, leader=%s, roll_no=%s, member1=%s, member2=%s, member3=%s, member4=%s
            WHERE id=%s
        """, updated)
        conn.commit()
        cursor.close()
        conn.close()
        flash('Team updated successfully.', 'success')
        return redirect(url_for('participants'))
    cursor.execute("SELECT * FROM teams WHERE id = %s", (row_id,))
    team = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_team.html', team=team, row_id=row_id)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# -------------------- MAIN -------------------- #
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
