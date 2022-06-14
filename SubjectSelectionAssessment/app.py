import uuid, os, hashlib, pymysql
from flask import Flask, request, render_template, redirect, url_for, session, abort, flash, jsonify
app = Flask(__name__)

# Register the setup page and import create_connection()
from utils import create_connection, setup
app.register_blueprint(setup)


@app.route('/')
def home():
    return render_template("index.html")

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# User Related App Routes
@app.route('/checkemail')
def check_email():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = 'SELECT * FROM assessment_users WHERE email = %s'
            values = (
                request.args['email']
            )
            cursor.execute(sql, values)
            result = cursor.fetchone()
            if result:
                return jsonify({ 'status': 'Taken' })
            else:
                return jsonify({ 'status': 'OK' }) 

# TODO: Add a '/register' (add_user) route that uses INSERT
@app.route('/register', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':

        password =  request.form['password']
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        avatar_filename = None    

        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """INSERT INTO assessment_users
                    (first_name, last_name, email, password, avatar)
                    VALUES (%s, %s, %s, %s, %s)
                """
                values = (
                    request.form['first_name'],
                    request.form['last_name'],
                    request.form['email'],
                    encrypted_password,
                    avatar_filename
                )
                try:
                    cursor.execute(sql, values)
                    connection.commit()
                except pymysql.err.IntegrityError:
                    flash('Email has already been taken')
                    return redirect(url_for('add_user'))
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = 'SELECT * FROM assessment_users WHERE email = %s AND password = %s'
                values = (
                    request.form['email'],
                    encrypted_password
                )
                cursor.execute(sql, values)
                result = cursor.fetchone()
                if result:
                    session['logged_in'] = True
                    session['first_name'] = result['first_name']
                    session['email'] = result['email']
                    session['role'] = result['role']
                    session['id'] = result['id']
                    return redirect(url_for('view_user', id=result['id']))
        return redirect(url_for('home'))
    return render_template('users_add.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        password = request.form['password']
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()
        # LOGIN
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = 'SELECT * FROM assessment_users WHERE email = %s AND password = %s'
                values = (
                    request.form['email'],
                    encrypted_password
                )
                cursor.execute(sql, values)
                result = cursor.fetchone()
        if result:
            session['logged_in'] = True
            session['first_name'] = result['first_name']
            session['email'] = result['email']
            session['role'] = result['role']
            session['id'] = result['id']
            return redirect(url_for('view_user', id=result['id']))
        else:
            return redirect('/login')
    else:
        return render_template('users_login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/profile')
def view_user():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = """SELECT * FROM assessment_users WHERE id=%s"""
            values = (
                request.args['id']
            )
            cursor.execute(sql, values)
            result = cursor.fetchall()
    return render_template('users_view.html', result=result)

@app.route('/edituser', methods=['GET', 'POST'])
def edit_user():

    if session['role'] != 'admin' or str(session['id']) != request.args['id']:
        return abort(404)
    if request.method == 'POST':

        if request.files['avatar'].filename:
            avatar_image = request.files["avatar"]
            ext = os.path.splitext(avatar_image.filename)[1]
            avatar_filename = str(uuid.uuid4())[:8] + ext
            avatar_image.save("static/images/" + avatar_filename)
            if request.form['old_avatar'] != 'None' and os.path.exists("static/images/" + request.request.form['old_avatar']):
                os.remove("static/images/" + request.form['old_avatar'])
        elif request.form['old_avatar'] != 'None':
            avatar_filename = request.form['old_avatar']
        else:
            avatar_filename = None

        with create_connection() as connection:    

            with connection.cursor() as cursor:
                sql = """UPDATE assessment_users SET
                        first_name = %s, last_name = %s,
                        email = %s, avatar = %s
                    WHERE id = %s
                """
                values = (
                    request.form['first_name'],
                    request.form['last_name'],
                    request.form['email'],
                    avatar_filename,
                    request.args['id']
                )
                cursor.execute(sql, values)
                connection.commit()
        return redirect(url_for('home'))
    return render_template('users_edit.html')

@app.route('/deleteuser')
def delete_user():

    if session['role'] != 'admin' and str(session['id']) != request.args['id']:
        return abort(404)
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "DELETE FROM assessment_users WHERE id = %s"
            values = (
                request.args['id']
            )
            cursor.execute(sql, values)
            connection.commit()
            # Log out if function
        
    if str(session['id']) == request.args['id']:
        return redirect(url_for('logout'))
    else:
        return redirect(url_for('list_users'))

# Dashboard lists all users, this is an admin page
@app.route('/dashboard')
def list_users():

    if session['role'] != 'admin':
        return abort(404)
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM assessment_users")
            result = cursor.fetchall()
    return render_template('users_list.html', result=result)

# Subject related app routes
@app.route('/addsubject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':

        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """INSERT INTO assessment_subjects
                    (title, subject, year, description, internal_credits, external_credits)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                values = (
                    request.form['title'],
                    request.form['subject'],
                    request.form['year'],
                    request.form['description'],
                    request.form['internal_credits'],
                    request.form['external_credits']
                )
                cursor.execute(sql, values)
                connection.commit()
        return redirect(url_for('home'))
    return render_template("subjects_add.html")

@app.route('/deletesubject')
def delete_subject():
    return render_template("index.html")

@app.route('/editsubject')
def edit_subject():

    if session['role'] != 'admin':
        return abort(404)
    
    if request.method == 'POST':

        with create_connection() as connection:    
            with connection.cursor() as cursor:
                sql = """UPDATE assessment_subjects SET
                        title = %s, subject = %s,
                        year = %s, description = %s,
                        internal_credits = %s, external_credits = %s
                    WHERE id = %s
                """
                values = (
                    request.form['title'],
                    request.form['subject'],
                    request.form['year'],
                    request.form['description'],
                    request.form['internal_credits'],
                    request.form['external_credits'],
                    request.args['id']
                )
                cursor.execute(sql, values)
                connection.commit()
        return redirect(url_for('home'))
    return render_template("subjects_edit.html")

@app.route('/subjects')
def list_subjects():
    if session['role'] != 'admin':
        return abort(404)
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM assessment_subjects")
            result = cursor.fetchall()
    return render_template('subjects_list.html', result=result)

# Student-User related app routes
@app.route('/subjectselection')
def view_user_subjects():
    return render_template("index.html")

@app.route('/selectsubject')
def user_select_subject():
    return render_template("index.html")

@app.route('/removesubjectselection')
def delete_user_subject():
    return render_template("index.html")


if __name__ == '__main__':
    import os

    # This is required to allow flashing messages
    app.secret_key = os.urandom(32)
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT, debug=True)

