# Register the setup page and import create_connection()
from utils import create_connection, setup
import uuid
import os
import hashlib
import pymysql
from flask import Flask, request, render_template, redirect, url_for, session
from flask import abort, flash, jsonify
from datetime import datetime

app = Flask(__name__)
app.register_blueprint(setup)

# Miscellaneous App Routes


# Home page
@app.route('/')
def home():
    return render_template("index.html")


# 404 Page
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# User Related App Routes


# AJAX check whether email already exists while registering a user
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
                return jsonify({'status': 'Taken'})
            else:
                return jsonify({'status': 'OK'})


# Add a user to database
@app.route('/register', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':

        password = request.form['password']
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
                sql = '''SELECT * FROM assessment_users WHERE email = %s
                    AND password = %s'''
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


# Login user to session
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        password = request.form['password']
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()
        # LOGIN
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = '''SELECT * FROM assessment_users WHERE email = %s AND
                    password = %s'''
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


# Logout user from session
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# View profile of user
@app.route('/profile')
def view_user():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = """SELECT * FROM assessment_users WHERE id=%s"""
            values = (
                request.args['id']
            )
            cursor.execute(sql, values)
            result = cursor.fetchone()
    return render_template('users_view.html', result=result)


# Edit user information
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
            if request.form['old_avatar'] != 'None' and (
                os.path.exists("static/images/" +
                               request.request.form['old_avatar'])):
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


# Delete user from database
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
                    (title, subject, year, description, internal_credits,
                    external_credits, start_date, end_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    request.form['title'],
                    request.form['subject'],
                    request.form['year'],
                    request.form['description'],
                    request.form['internal_credits'],
                    request.form['external_credits'],
                    request.form['start_date'],
                    request.form['end_date']
                )
                try:
                    cursor.execute(sql, values)
                    connection.commit()
                except pymysql.err.IntegrityError:
                    flash('end_date should be greater than start_date')
                    return redirect(url_for('add_subject'))
        return redirect(url_for('list_subjects'))
    return render_template("subjects_add.html")


# Delete subject from database
@app.route('/deletesubject')
def delete_subject():
    if session['role'] != 'admin':
        return abort(404)
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "DELETE FROM assessment_subjects WHERE id = %s"
            values = (
                request.args['id']
            )
            cursor.execute(sql, values)
            connection.commit()
            return redirect(url_for('list_subjects'))


# Edit subject information
@app.route('/editsubject', methods=['GET', 'POST'])
def edit_subject():

    if session['role'] != 'admin':
        return abort(404)

    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM assessment_subjects WHERE id = %s"
            values = (
            request.args['id']
            )
            cursor.execute(sql, values)
            result = cursor.fetchone()


    if request.method == 'POST':

        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """UPDATE assessment_subjects SET
                        title = %s, subject = %s,
                        year = %s, description = %s,
                        internal_credits = %s, external_credits = %s,
                        start_date = %s, end_date = %s
                    WHERE id = %s
                """
                values = (
                    request.form['title'],
                    request.form['subject'],
                    request.form['year'],
                    request.form['description'],
                    request.form['internal_credits'],
                    request.form['external_credits'],
                    request.form['start_date'],
                    request.form['end_date'],
                    request.args['id']
                ) 
                cursor.execute(sql, values)
                connection.commit()
        return redirect(url_for('view_subjects'))
    return render_template("subjects_edit.html", subject_info=result)


# List all subjects, this is an admin page
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


# This page shows all of your subjects, and if you are able to add more
@app.route('/subjectselection')
def view_user_subjects():
    if session['role'] != 'admin' and str(session['id']) != request.args['id']:
        return abort(404)
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = """SELECT
                assessment_student_subject.id,
                assessment_student_subject.student_id,
                assessment_student_subject.subject_id,
                assessment_subjects.title,
                assessment_subjects.subject,
                assessment_subjects.year,
                assessment_subjects.description,
                assessment_subjects.internal_credits,
                assessment_subjects.external_credits,
                assessment_subjects.start_date
                FROM
                assessment_student_subject
                INNER JOIN
                assessment_subjects
                ON
                    assessment_student_subject.subject_id =
                    assessment_subjects.id
                WHERE
                assessment_student_subject.student_id = %s"""

            values = (
                request.args['id']
            )
            cursor.execute(sql, values)
            result = cursor.fetchall()

            sql = """SELECT COUNT(*) As count_s FROM
                     assessment_student_subject WHERE student_id = %s"""
            values = (
                session['id']
                )
            cursor.execute(sql, values)
            select_count = cursor.fetchone()
            selected = 5 - int(select_count['count_s'])

    return render_template('users_subject_view.html', result=result,
                           select_left=selected)


# This page shows all subjects, allowing you to choose one to add to your user
@app.route('/selectsubject')
def user_select_subject():
    with create_connection() as connection:
        with connection.cursor() as cursor:

            # Get current date and time
            date_time = datetime.now()

            date = date_time.date()

            # Convert date to string
            date_str = str(date)

            cursor.execute("""SELECT * FROM assessment_subjects WHERE
                              start_date <= %s AND %s <= end_date""",
                           (date_str, date_str))
            result = cursor.fetchall()

            # Make a count
            sql = """SELECT COUNT(*) As count_s FROM
                     assessment_student_subject WHERE student_id = %s"""
            values = (
                session['id']
                )
            cursor.execute(sql, values)
            select_count = cursor.fetchone()
            selected = 5-int(select_count['count_s'])

            sql = """SELECT subject_id FROM assessment_student_subject WHERE
                     student_id = %s"""
            values = (
                session['id']
                )
            cursor.execute(sql, values)
            already_selected = cursor.fetchall()
            new_selected = []
            for dict in already_selected:
                for value in dict.values():
                    new_selected.append(value)
            already_selected = new_selected
    if selected <= 0:
        flash('Already selected 5 subjects')
    return render_template("users_subject_selection.html", result=result,
                           select_left=selected,
                           already_selected=already_selected)


# Add a subject, allowing you to choose one to add to your user
@app.route('/addselectedsubject')
def user_add_subject():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = """SELECT * FROM assessment_student_subject
                     WHERE student_id = %s AND subject_id = %s
            """
            values = (
                str(request.args['student_id']),
                str(request.args['subject_id'])
            )
            cursor.execute(sql, values)
            result = cursor.fetchone()

            # check subjects already selected

            sql = """SELECT COUNT(*) As count_s FROM
                     assessment_student_subject WHERE student_id = %s"""
            values = (
                session['id']
                )
            cursor.execute(sql, values)
            select_count = cursor.fetchone()
            selected = 5 - int(select_count['count_s'])
            if selected <= 0:
                return redirect(url_for("view_user_subjects", id=session['id'],
                                        select_left=selected))

            # If the selection already exists, just return to selection page
            if result:
                return redirect(url_for("view_user_subjects",
                                id=session['id']))

            sql = """INSERT INTO assessment_student_subject
                (student_id, subject_id)
                VALUES (%s, %s)
            """
            values = (
                request.args['student_id'],
                request.args['subject_id']
            )
            cursor.execute(sql, values)
            connection.commit()
            return redirect(url_for("view_user_subjects", id=session['id']))


# Remove a subject that has been selected
@app.route('/removesubjectselection')
def delete_user_subject():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM assessment_student_subject WHERE id = %s"
            values = (
                request.args['id']
            )
            cursor.execute(sql, values)
            result = cursor.fetchone()
    if session['role'] != 'admin' and str(session['id']) != (
                                                    str(result['student_id'])):
        return abort(404)
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "DELETE FROM assessment_student_subject WHERE id = %s"
            values = (
                request.args['id']
            )
            cursor.execute(sql, values)
            connection.commit()
            return redirect(url_for('view_user_subjects', id=session['id']))


# View a subject's information
@app.route('/viewsubject')
def view_subject():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = """SELECT
                    assessment_student_subject.*,
                    assessment_users.first_name,
                    assessment_users.last_name,
                    assessment_users.email
                FROM
                    assessment_student_subject
                    INNER JOIN
                    assessment_users
                ON
                    assessment_student_subject.student_id = assessment_users.id
                WHERE
                     assessment_student_subject.subject_id = %s
            """
            values = (
                request.args['id']
            )
            cursor.execute(sql, values)
            students_selected = cursor.fetchall()

            sql = "SELECT * FROM assessment_subjects where id = %s"

            values = (
                request.args['id']
            )
            cursor.execute(sql, values)
            subject_information = cursor.fetchone()
    return render_template('subjects_view.html',
                           subject_info=subject_information,
                           students_selected=students_selected)


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
