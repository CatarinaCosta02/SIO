import os
from datetime import timedelta, datetime

from flask import Flask, render_template, redirect, url_for, request, current_app, send_file
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from classes import User
from db import ClinicDB
from utils import get_timeslots

app = Flask(__name__)

app.secret_key = b'secret_key'
app.config["MYSQL_USER"] = "admin"
app.config["MYSQL_PASSWORD"] = "admin"
app.config["MYSQL_DB"] = "clinic"
app.config['MYSQL_HOST'] = "clinic-db"
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

db = ClinicDB(MySQL(app))

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(_id):
    cur = db.conn.cursor()
    cur.execute('SELECT * FROM users WHERE id = ' + str(_id))
    user = cur.fetchone()
    return User(user)


@app.route('/')
def root():
    return redirect(url_for('home'))


@app.route('/reset-db')
def reset_db():
    db.init()
    return redirect(url_for('home'))


@app.route('/admin')
@login_required
def admin():
    if current_user.username != 'admin':
        return redirect(url_for('home'))
    cur = db.conn.cursor()
    cur.execute('SELECT * FROM appointments '
                'LEFT JOIN '
                '(SELECT id, first_name AS u_first_name, last_name AS u_last_name FROM users) AS users '
                'ON appointments.id_user = users.id '
                'LEFT JOIN '
                '(SELECT id, first_name AS d_first_name, last_name AS d_last_name FROM doctors) AS doctors '
                'ON appointments.id_doctor = doctors.id ')
    apps = cur.fetchall()
    cur.execute('SELECT * FROM contacts '
                'LEFT JOIN '
                '(SELECT id, first_name AS u_first_name, last_name AS u_last_name FROM users) AS users '
                'ON contacts.id_user = users.id')
    conts = cur.fetchall()
    cur.close()

    ctx = {'layout': db.get_layout_ctx(),
           'appointments': apps,
           'contacts': conts}
    return render_template('admin.html', **ctx)


@app.route('/home')
def home():
    ctx = {'layout': db.get_layout_ctx()}
    return render_template('home.html', **ctx)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Catch any errors
        cur = db.conn.cursor()
        try:
            cur.execute(
                'SELECT * FROM users WHERE username = \'' + username + '\' AND password = SHA2(\'' + password + '\', 512)')
            user = cur.fetchone()
            cur.close()
        except Exception as e:
            cur.close()
            ctx = {'layout': db.get_layout_ctx(),
                   'request': request,
                   'error': str(e)}
            return render_template('login.html', **ctx)

        # Check if user exists
        if user:
            login_user(User(user))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            ctx = {'layout': db.get_layout_ctx(),
                   'request': request,
                   'error': 'Invalid username or password.'}
            return render_template('login.html', **ctx)
    else:
        ctx = {'layout': db.get_layout_ctx()}
        return render_template('login.html', **ctx)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password1 = request.form['password1']
        password2 = request.form['password2']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        email = request.form['email']

        # Username must be unique
        cur = db.conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = \'' + username + '\'')
        user = cur.fetchone()
        cur.close()
        if user:
            ctx = {'layout': db.get_layout_ctx(),
                   'request': request,
                   'error': 'Username already exists.'}
            return render_template('signup.html', **ctx)

        # Passwords must match
        if password1 != password2:
            ctx = {'layout': db.get_layout_ctx(),
                   'request': request,
                   'error': 'Passwords do not match.'}
            return render_template('signup.html', **ctx)

        # Catch any errors
        cur = db.conn.cursor()
        try:
            cur.execute(
                'INSERT INTO users (username, password, first_name, last_name, phone, email) VALUES (\'' + username + '\', SHA2(\'' + password1 + '\', 512), \'' + first_name + '\', \'' + last_name + '\', \'' + phone + '\', \'' + email + '\')')
            db.conn.commit()
            cur.close()
        except Exception as e:
            cur.close()
            ctx = {'layout': db.get_layout_ctx(),
                   'request': request,
                   'error': str(e)}
            return render_template('signup.html', **ctx)

        # Login the user
        cur = db.conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = \'' + username + '\'')
        user = cur.fetchone()
        cur.close()
        login_user(User(user))
        next_page = request.args.get('next')
        return redirect(next_page or url_for('home'))
    else:
        ctx = {'layout': db.get_layout_ctx()}
        return render_template('signup.html', **ctx)


@app.route('/departments')
def departments():
    cur = db.conn.cursor()
    cur.execute('SELECT * FROM departments')
    deps = cur.fetchall()
    cur.close()
    ctx = {'layout': db.get_layout_ctx(),
           'departments': deps}
    return render_template('departments.html', **ctx)


@app.route('/departments/<int:_id>')
def departments_single(_id):
    cur = db.conn.cursor()
    cur.execute('SELECT * FROM departments WHERE id = ' + str(_id))
    dep = cur.fetchone()
    cur.close()
    ctx = {'layout': db.get_layout_ctx(),
           'department': dep}
    return render_template('departments_single.html', **ctx)


@app.route('/doctors')
def doctors():
    cur = db.conn.cursor()
    cur.execute('SELECT * FROM doctors '
                'LEFT JOIN '
                '(SELECT id, name AS d_name FROM departments) AS departments '
                'ON doctors.id_department = departments.id')
    docs = cur.fetchall()
    cur.execute('SELECT * FROM departments')
    deps = cur.fetchall()
    cur.close()
    ctx = {'layout': db.get_layout_ctx(),
           'doctors': docs,
           'departments': deps}
    return render_template('doctors.html', **ctx)


@app.route('/doctors/<int:_id>')
def doctors_single(_id):
    cur = db.conn.cursor()
    cur.execute('SELECT * FROM doctors '
                'LEFT JOIN '
                '(SELECT id, name AS d_name FROM departments) AS departments '
                'ON doctors.id_department = departments.id '
                'WHERE doctors.id = ' + str(_id))
    doc = cur.fetchone()
    cur.close()
    ctx = {'layout': db.get_layout_ctx(),
           'doctor': doc}
    return render_template('doctors_single.html', **ctx)


@app.route('/appointment', methods=['GET', 'POST'])
@login_required
def appointment():
    if request.method == 'POST':
        message = request.form['message']
        start_date = request.form['start_date']
        end_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=1)
        id_doctor = request.form['id_doctor']
        id_user = current_user.id

        # Catch any errors
        cur = db.conn.cursor()
        try:
            cur.execute(
                'INSERT INTO appointments (message, start_date, end_date, id_doctor, id_user) '
                'VALUES (\'' + message + '\', \'' + str(start_date) + '\', \'' + str(
                    end_date) + '\', ' + str(id_doctor) + ', ' + str(id_user) + ')')
            db.conn.commit()
            cur.close()
        except Exception as e:
            cur.close()
            ctx = {'layout': db.get_layout_ctx(),
                   'request': request,
                   'error': str(e)}
            return render_template('appointment.html', **ctx)

        ctx = {'layout': db.get_layout_ctx(),
               'type': 'appointment'}
        return render_template('confirmation.html', **ctx)
    else:
        cur = db.conn.cursor()
        cur.execute('SELECT * FROM departments')
        deps = cur.fetchall()
        cur.execute('SELECT * FROM doctors')
        docs = cur.fetchall()
        cur.execute('SELECT * FROM schedules')
        scheds = cur.fetchall()
        cur.execute('SELECT * FROM appointments')
        appoints = cur.fetchall()
        cur.close()

        timeslots = get_timeslots(docs, scheds, appoints)

        ctx = {'layout': db.get_layout_ctx(),
               'departments': deps,
               'doctors': docs,
               'timeslots': timeslots}
        return render_template('appointment.html', **ctx)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        subject = request.form['subject']
        message = request.form['message']
        id_user = request.form['id_user']

        # Catch any errors
        cur = db.conn.cursor()
        try:
            cur.execute(
                'INSERT INTO contacts (subject, message, id_user) '
                'VALUES (\'' + subject + '\', \'' + message + '\', ' + str(id_user) + ')')
            db.conn.commit()
            cur.close()
        except Exception as e:
            cur.close()
            ctx = {'layout': db.get_layout_ctx(),
                   'request': request,
                   'error': str(e)}
            return render_template('contact.html', **ctx)

        ctx = {'layout': db.get_layout_ctx(),
               'type': 'contact'}
        return render_template('confirmation.html', **ctx)
    else:
        ctx = {'layout': db.get_layout_ctx()}
        return render_template('contact.html', **ctx)


@app.route('/prescription', methods=['GET', 'POST'])
def prescription():
    if request.method == 'POST':
        # Download the file
        if 'file' in request.form:
            file = request.form['file']
            path = os.path.join(current_app.root_path, 'exams', file)
            return send_file(path, as_attachment=True)

        # Check for file in database
        code = request.form['code']

        # Catch any errors
        cur = db.conn.cursor()
        try:
            cur.execute('SELECT url_exam FROM exams WHERE id = \'' + code + '\'')
            exam = cur.fetchone()
            cur.close()
        except Exception as e:
            cur.close()
            ctx = {'layout': db.get_layout_ctx(),
                   'request': request,
                   'error': str(e)}
            return render_template('prescription.html', **ctx)

        if exam:
            return redirect('?file=' + exam['url_exam'])
        else:
            ctx = {'layout': db.get_layout_ctx(),
                   'error': 'Result not found.'}
            return render_template('prescription.html', **ctx)
    else:
        ctx = {'layout': db.get_layout_ctx()}
        return render_template('prescription.html', **ctx)


if __name__ == '__main__':
    app.run()
