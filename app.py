from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from flask import session
import datetime
import os

import os

current_image_index = 0
profile_images = [f"profile{i}.png" for i in range(1, len(os.listdir('static/profile_pics')) + 1)]
profile_images.sort()


app = Flask(__name__)

app.secret_key = 'HETI'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'elly'
app.config['MYSQL_PASSWORD'] = 'elly'
app.config['MYSQL_DB'] = 'linker'

mysql = MySQL(app)

current_user_id = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user_type = request.form['user_type']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password, user_type) VALUES (%s, %s, %s)", (username, password, user_type))
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
        cur.execute("SELECT user_id, password, user_type FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[1], password):
            current_user_id = user[0]
            user_type = user[2]
            if user_type in ['recruiter', 'recruiter_premium']:
                return redirect(url_for('recruiter_profile'))
            else:
                return redirect(url_for('recruitee_profile'))
        return "Invalid credentials!"
    return render_template('login.html')

@app.route('/recruiter_profile', methods=['GET', 'POST'])
def recruiter_profile():
    global current_user_id
    if current_user_id is None:
        return redirect(url_for('login'))

    if request.method == 'POST':
        job_title = request.form['job_title']
        job_description = request.form['job_description']
        compensation = request.form['compensation']
        job_location = request.form['job_location']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Jobs (user_id, job_title, job_description, compensation, job_location) VALUES (%s, %s, %s, %s, %s)",
                    (current_user_id, job_title, job_description, compensation, job_location))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('recruiter_profile'))
    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Location")
        locations = cur.fetchall()
        cur.close()
        return render_template('recruiter_profile.html', locations=locations)

@app.route('/recruitee_profile', methods=['GET', 'POST'])
def recruitee_profile():
    global current_user_id
    if current_user_id is None:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    if request.method == 'POST':
        bio = request.form['bio']
        selected_skills = request.form.getlist('skills')
        
        # Update bio
        cur.execute("UPDATE Recruitee SET bio = %s WHERE user_id = %s", (bio, current_user_id))
        
        # Clear current skills
        cur.execute("DELETE FROM UserSkills WHERE user_id = %s", [current_user_id])
        
        # Insert new skills
        for skill_id in selected_skills:
            cur.execute("INSERT INTO UserSkills (user_id, skill_id) VALUES (%s, %s)", (current_user_id, skill_id))
        
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('swipe_recruitee'))
    else:
        # Fetch current bio
        cur.execute("SELECT bio FROM Recruitee WHERE user_id = %s", [current_user_id])
        bio = cur.fetchone()[0]
        
        # Fetch all skills and mark the ones the user already has
        cur.execute("""
            SELECT s.skill_id, s.skill_name, 
            CASE WHEN us.user_id IS NOT NULL THEN 1 ELSE 0 END AS has_skill
            FROM Skills s
            LEFT JOIN UserSkills us ON s.skill_id = us.skill_id AND us.user_id = %s
        """, [current_user_id])
        skills = cur.fetchall()
        cur.close()
        return render_template('recruitee_profile.html', bio=bio, skills=skills)


def get_remaining_swipes(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_type FROM Users WHERE user_id = %s", [user_id])
    user_type = cur.fetchone()[0]
    if user_type in ['recruiter_premium', 'recruitee_premium']:
        return float('inf')  # Infinite swipes for premium users

    # For regular users, calculate remaining swipes
    today = date.today()
    cur.execute("SELECT swipe_count FROM DailySwipes WHERE user_id = %s AND swipe_date = %s", (user_id, today))
    result = cur.fetchone()
    cur.close()
    if result:
        return 10 - result[0]
    else:
        return 10

@app.route('/swipe_action', methods=['POST'])
def swipe_action():
    global current_user_id, current_image_index, profile_images
    if current_user_id is None:
        return redirect(url_for('login'))
    
    action = request.form['action']
    swipee_id = request.form.get('user_id') or request.form.get('job_id')  # Handle both user and job IDs
    
    if not swipee_id:
        return jsonify({'error': 'Missing user_id or job_id'}), 400

    cur = mysql.connection.cursor()
    match_found = False

    # Determine if the current user is a recruiter or recruitee
    cur.execute("SELECT user_type FROM Users WHERE user_id = %s", [current_user_id])
    user_type = cur.fetchone()[0]

    # Check if the current user is swiping on a user (for recruiters) or a job (for recruitees)
    if user_type in ['recruiter', 'recruiter_premium']:
        # Recruiter is swiping on a recruitee
        cur.execute("INSERT INTO UserSwipes (swiper_id, swipee_id, swipe_type) VALUES (%s, %s, %s)", (current_user_id, swipee_id, action))
        
        # Check for a mutual like (recruitee liked the recruiter back)
        cur.execute("""
        SELECT COUNT(*) FROM UserSwipes
        WHERE swiper_id = %s AND swipee_id = %s AND swipe_type = 'like'
        """, (swipee_id, current_user_id))
    else:
        # Recruitee is swiping on a job (recruiter)
        cur.execute("INSERT INTO UserSwipes (swiper_id, swipee_id, swipe_type) VALUES (%s, %s, %s)", (swipee_id, current_user_id, action))
        
        # Check for a mutual like (recruiter liked the recruitee back)
        cur.execute("""
        SELECT COUNT(*) FROM UserSwipes
        WHERE swiper_id = %s AND swipee_id = %s AND swipe_type = 'like'
        """, (current_user_id, swipee_id))

    match_count = cur.fetchone()[0]
    if match_count > 0:
        match_found = True
        cur.execute("INSERT INTO Matches (user1_id, user2_id) VALUES (LEAST(%s, %s), GREATEST(%s, %s))", (current_user_id, swipee_id, current_user_id, swipee_id))

    # Delete from the PotentialUsers or PotentialJobs table
    if request.form.get('user_id'):
        cur.execute("DELETE FROM PotentialUsers WHERE user_id = %s AND filterer_id = %s", [swipee_id, current_user_id])
    elif request.form.get('job_id'):
        cur.execute("DELETE FROM PotentialJobs WHERE job_id = %s AND filterer_id = %s", [swipee_id, current_user_id])
        
    mysql.connection.commit()
    cur.close()

    # Cycle to the next image
    current_image_index = (current_image_index + 1) % len(profile_images)
    
    return jsonify({'match': match_found})

@app.route('/swipe_recruiter', methods=['GET', 'POST'])
def swipe_recruiter():
    global current_user_id, current_image_index, profile_images
    
    if current_user_id is None:
        return redirect(url_for('login'))

    if request.method == 'POST':
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
        return redirect(url_for('swipe_recruiter'))

    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Skills")
        skills = cur.fetchall()
        
        # Fetch one potential user to display
        cur.execute("SELECT u.user_id, u.username, r.bio FROM PotentialUsers p JOIN Users u ON p.user_id = u.user_id LEFT JOIN Recruitee r ON u.user_id = r.user_id WHERE p.filterer_id = %s LIMIT 1", [current_user_id])
        potential_user = cur.fetchone()
        
        user_skills = []
        if potential_user:
            cur.execute("SELECT s.skill_name FROM UserSkills us JOIN Skills s ON us.skill_id = s.skill_id WHERE us.user_id = %s", [potential_user[0]])
            user_skills = [row[0] for row in cur.fetchall()]

        cur.close()

        profile_image = profile_images[current_image_index]

        return render_template('swipe_recruiter.html', skills=skills, user=potential_user, user_skills=user_skills, profile_image=profile_image, remaining_swipes=get_remaining_swipes(current_user_id))

@app.route('/swipe_recruitee', methods=['GET', 'POST'])
def swipe_recruitee():
    global current_user_id, current_image_index, profile_images
    
    if current_user_id is None:
        return redirect(url_for('login'))

    if request.method == 'POST':
        acceptable_cities = request.form.getlist('acceptable_cities')
        min_compensation = request.form['min_compensation']
        cur = mysql.connection.cursor()

        # Clear previous potential jobs for this filterer
        cur.execute("DELETE FROM PotentialJobs WHERE filterer_id = %s", [current_user_id])

        # Create a query with placeholders
        city_placeholders = ','.join(['%s'] * len(acceptable_cities))
        
        # Insert new potential jobs
        insert_query = f"""
        INSERT INTO PotentialJobs (job_id, filterer_id)
        SELECT DISTINCT j.job_id, %s
        FROM Jobs j
        JOIN Location l ON j.job_location = l.location_id
        WHERE l.location_id IN ({city_placeholders})
        AND j.compensation >= %s
        """
        cur.execute(insert_query, [current_user_id] + acceptable_cities + [min_compensation])

        mysql.connection.commit()
        cur.close()
        return redirect(url_for('swipe_recruitee'))

    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Location")
        locations = cur.fetchall()
        
        # Fetch one potential job to display
        cur.execute("SELECT j.job_id, j.job_title, j.job_description, j.compensation, l.location_name FROM PotentialJobs p JOIN Jobs j ON p.job_id = j.job_id JOIN Location l ON j.job_location = l.location_id WHERE p.filterer_id = %s LIMIT 1", [current_user_id])
        potential_job = cur.fetchone()
        cur.close()

        profile_image = profile_images[current_image_index]

        return render_template('swipe_recruitee.html', locations=locations, job=potential_job, profile_image=profile_image, remaining_swipes=get_remaining_swipes(current_user_id))




@app.route('/match_popup')
def match_popup():
    return render_template('match_popup.html')

@app.route('/matches')
def matches():
    global current_user_id
    if current_user_id is None:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("""
    SELECT u.user_id, u.username
    FROM Matches m
    JOIN Users u ON (u.user_id = m.user1_id OR u.user_id = m.user2_id)
    WHERE (m.user1_id = %s OR m.user2_id = %s) AND u.user_id != %s
    """, (current_user_id, current_user_id, current_user_id))
    matches = cur.fetchall()
    cur.close()
    return render_template('matches.html', matches=matches)
@app.route('/upgrade_premium', methods=['POST'])
def upgrade_premium():
    global current_user_id
    if current_user_id is None:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT user_type FROM Users WHERE user_id = %s", [current_user_id])
    user_type = cur.fetchone()[0]

    if user_type == 'recruiter':
        new_user_type = 'recruiter_premium'
    elif user_type == 'recruitee':
        new_user_type = 'recruitee_premium'
    else:
        new_user_type = user_type

    cur.execute("UPDATE Users SET user_type = %s WHERE user_id = %s", (new_user_type, current_user_id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('index'))
@app.route('/enter_chat', methods=['POST'])
def enter_chat():
    global current_user_id
    if current_user_id is None:
        return redirect(url_for('login'))

    match_id = request.form['match_id']
    session['chat_with_user_id'] = match_id
    return redirect(url_for('chat'))
@app.context_processor
def inject_user():
    global current_user_id
    if current_user_id is None:
        return dict(user_type=None, is_premium=False)

    cur = mysql.connection.cursor()
    cur.execute("SELECT user_type FROM Users WHERE user_id = %s", [current_user_id])
    user_type = cur.fetchone()[0]
    is_premium = user_type in ['recruiter_premium', 'recruitee_premium']
    cur.close()
    return dict(user_type=user_type, is_premium=is_premium)


@app.route('/logout')
def logout():
    global current_user_id
    current_user_id = None
    return redirect(url_for('login'))
@app.route('/admin')
def admin():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM Users 
        WHERE user_type = 'recruiter_premium' OR user_type = 'recruitee_premium'
    """)
    premium_user_count = cur.fetchone()[0]
    sub_cost = 100
    total_revenue = premium_user_count * sub_cost
    cur.close()
    return render_template('admin.html', premium_user_count=premium_user_count, total_revenue=total_revenue, sub_cost=sub_cost)
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    global current_user_id
    if current_user_id is None:
        return redirect(url_for('login'))

    chat_with_user_id = session.get('chat_with_user_id')
    if chat_with_user_id is None:
        return redirect(url_for('matches'))

    cur = mysql.connection.cursor()
    if request.method == 'POST':
        message_text = request.form['message_text']
        timestamp = datetime.datetime.now()
        cur.execute("INSERT INTO Messages (sender_id, receiver_id, message_text, timestamp) VALUES (%s, %s, %s, %s)", 
                    (current_user_id, chat_with_user_id, message_text, timestamp))
        mysql.connection.commit()

    cur.execute("""
        SELECT m.message_text, u.username, m.timestamp
        FROM Messages m
        JOIN Users u ON m.sender_id = u.user_id
        WHERE (m.sender_id = %s AND m.receiver_id = %s)
        OR (m.sender_id = %s AND m.receiver_id = %s)
        ORDER BY m.timestamp
    """, (current_user_id, chat_with_user_id, chat_with_user_id, current_user_id))
    messages = cur.fetchall()
    cur.close()
    return render_template('chat.html', messages=messages, chat_with_user_id=chat_with_user_id)
if __name__ == '__main__':
    app.run(debug=True)
