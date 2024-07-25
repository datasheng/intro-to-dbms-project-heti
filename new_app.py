from flask import Flask, request, render_template, redirect, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Set a secret key for the session
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'elly'
app.config['MYSQL_PASSWORD'] = 'elly'
app.config['MYSQL_DB'] = 'linker'

mysql = MySQL(app)

# Global variable to hold the current user ID
current_user_id = None

@app.route('/')
def index():
    return "Welcome to the Job Search App!"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global current_user_id
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT user_id, password FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[1], password):
            current_user_id = user[0]
            return redirect(url_for('profile'))
        return "Invalid credentials!"
    return render_template('login.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    global current_user_id
    if current_user_id is None:
        return redirect(url_for('login'))

    if request.method == 'POST':
        selected_skills = request.form.getlist('skills')
        cur = mysql.connection.cursor()
        for skill_id in selected_skills:
            cur.execute("INSERT INTO UserSkills (user_id, skill_id) VALUES (%s, %s)", (current_user_id, skill_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('profile'))
    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Skills")
        skills = cur.fetchall()
        cur.close()
        return render_template('profile.html', skills=skills)

@app.route('/swipe', methods=['GET', 'POST'])
def swipe():
    global current_user_id
    if current_user_id is None:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Apply filters and insert potential users into PotentialUsers table
        selected_skills = request.form.getlist('skills')
        cur = mysql.connection.cursor()

        # Clear previous potential users for this filterer
        cur.execute("DELETE FROM PotentialUsers WHERE filterer_id = %s", [current_user_id])

        # Create a query with placeholders
        placeholders = ','.join(['%s'] * len(selected_skills))
        
        # Insert new potential users
        insert_query = f"""
        INSERT INTO PotentialUsers (user_id, filterer_id)
        SELECT DISTINCT u.user_id, %s
        FROM Users u
        JOIN UserSkills us ON u.user_id = us.user_id
        WHERE us.skill_id IN ({placeholders})
        AND u.user_id != %s
        """
        cur.execute(insert_query, [current_user_id] + selected_skills + [current_user_id])

        mysql.connection.commit()
        cur.close()
        return redirect(url_for('swipe'))

    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Skills")
        skills = cur.fetchall()
        
        # Fetch one potential user to display
        cur.execute("SELECT u.user_id, u.username FROM PotentialUsers p JOIN Users u ON p.user_id = u.user_id WHERE p.filterer_id = %s LIMIT 1", [current_user_id])
        potential_user = cur.fetchone()
        cur.close()
        return render_template('swipe.html', skills=skills, user=potential_user)

@app.route('/swipe_action', methods=['POST'])
def swipe_action():
    global current_user_id
    if current_user_id is None:
        return redirect(url_for('login'))
    
    swipee_id = request.form['user_id']
    action = request.form['action']
    
    cur = mysql.connection.cursor()
    if action == 'like':
        cur.execute("INSERT INTO UserSwipes (swiper_id, swipee_id, swipe_type) VALUES (%s, %s, 'like')", (current_user_id, swipee_id))
    
    # Delete from the PotentialUsers table
    cur.execute("DELETE FROM PotentialUsers WHERE user_id = %s AND filterer_id = %s", [swipee_id, current_user_id])
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('swipe'))

if __name__ == '__main__':
    app.run(debug=True)
