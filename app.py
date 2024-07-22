from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'elly'
app.config['MYSQL_PASSWORD'] = 'elly'
app.config['MYSQL_DB'] = 'linker'

mysql = MySQL(app)

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
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[0], password):
            return redirect(url_for('index'))
        return "Invalid credentials!"
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
