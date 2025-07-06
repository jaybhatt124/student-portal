from flask import Flask, render_template, request, redirect, session, flash, url_for, send_from_directory
from werkzeug.utils import secure_filename
from functools import wraps
import mysql.connector
import os
import csv
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ──────── DB Connection ────────
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='root',
    database='student_portal'
)
cursor = conn.cursor()

# ──────── Login Required Decorator ────────
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ──────── Routes ────────

#login----------
@app.route('/')
def index():
    return redirect(url_for('login'))

#home----
@app.route('/home')
@login_required
def home():
    return render_template('home.html')
#materials---
@app.route('/materials')
@login_required
def materials():
    return render_template('materials.html')

@app.route('/materials/sem/<int:sem>')
@login_required
def semester_subjects(sem):
    role = session.get('role')
    subjects = ["Mathematics", "Physics", "Chemistry", "Biology", "English", "Computer"]
    return render_template("semester_subjects.html", sem=sem, subjects=subjects, role=role)

@app.route('/materials/sem/<int:sem>/subject/<subject>', methods=['GET', 'POST'])
@login_required
def subject_materials(sem, subject):
    role = session.get('role')
    safe_subject = secure_filename(subject)
    subject_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'sem{sem}', safe_subject)
    os.makedirs(subject_folder, exist_ok=True)

    meta_file_path = os.path.join(subject_folder, 'upload_info.json')
    upload_info = {}
    if os.path.exists(meta_file_path):
        with open(meta_file_path, 'r') as f:
            upload_info = json.load(f)

    if request.method == 'POST' and role in ['admin', 'teacher']:
        file = request.files['material']
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(subject_folder, filename)
            file.save(filepath)

            upload_info[filename] = {
                "uploaded_by": session.get("username", "Unknown"),
                "uploaded_on": datetime.now().strftime('%Y-%m-%d %H:%M'),
                "size": round(os.path.getsize(filepath) / 1024, 2)
            }
            with open(meta_file_path, 'w') as f:
                json.dump(upload_info, f)
            flash('Material uploaded successfully!', 'success')
        return redirect(url_for('subject_materials', sem=sem, subject=subject))

    files = [f for f in os.listdir(subject_folder) if f != 'upload_info.json']
    return render_template("subject_materials.html", sem=sem, subject=subject, files=files, role=role, upload_info=upload_info)

@app.route('/materials/sem/<int:sem>/subject/<subject>/delete/<filename>', methods=['POST'])
@login_required
def delete_material(sem, subject, filename):
    if session.get('role') not in ['admin', 'teacher']:
        return redirect('/login')
    subject_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'sem{sem}', secure_filename(subject))
    file_path = os.path.join(subject_folder, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash('Material deleted successfully!', 'success')
    return redirect(url_for('subject_materials', sem=sem, subject=subject))

@app.route('/download/<int:sem>/<subject>/<filename>')
@login_required
def download_file(sem, subject, filename):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], f'sem{sem}', secure_filename(subject))
    return send_from_directory(folder, filename)

#attendance
@app.route('/attendance')
@login_required
def attendance_semester():
    return render_template('attendance_semesters.html', role=session.get('role'))

@app.route('/attendance/sem/<int:sem>')
@login_required
def attendance_subjects(sem):
    role = session.get('role')
    subjects = ["Mathematics", "Physics", "Chemistry", "Biology", "English", "Computer"]
    return render_template('attendance_subjects.html', sem=sem, subjects=subjects, role=role)

@app.route('/attendance')
@login_required
def view_attendance():
    return render_template('attendance_semesters.html', role=session.get('role'))



@app.route('/attendance/sem/<int:sem>/subject/<subject>', methods=['GET', 'POST'])
@login_required
def subject_attendance(sem, subject):
    role = session.get('role')
    folder = os.path.join('attendance_data', f'sem{sem}', secure_filename(subject))
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, 'students.csv')

    # Upload CSV or mark attendance
    if request.method == 'POST' and role in ['admin', 'teacher']:
        if 'csv_file' in request.files:
            csv_file = request.files['csv_file']
            csv_file.save(file_path)
            flash('Student list uploaded successfully.', 'success')
        elif 'attendance_submit' in request.form:
            for key in request.form:
                if key.startswith('status_'):
                    enr = key.split('_')[1]
                    status = request.form[key]
                    with open(os.path.join(folder, f"{enr}.txt"), 'a') as f:
                        f.write(f"{datetime.now().date()},{status}\n")
            flash('Attendance submitted.', 'success')
        return redirect(url_for('subject_attendance', sem=sem, subject=subject))

    # Read student list
    students = []
    if os.path.exists(file_path):
        with open(file_path, newline='', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            students = list(reader)

    return render_template('subject_attendance.html', sem=sem, subject=subject, students=students, role=role)


##assignmentsss

@app.route('/assignments')
@login_required
def assignments_semester():
    return render_template('assignment_semesters.html', role=session.get('role'))


@app.route('/assignments/sem/<int:sem>')
@login_required
def assignments_subjects(sem):
    role = session.get('role')
    subjects = ["Mathematics", "Physics", "Chemistry", "Biology", "English", "Computer"]
    return render_template('assignment_subjects.html', sem=sem, subjects=subjects, role=role)


@app.route('/assignments/sem/<int:sem>/subject/<subject>', methods=['GET', 'POST'])
@login_required
def subject_assignments(sem, subject):
    role = session.get('role')
    folder = os.path.join('assignment_data', f'sem{sem}', secure_filename(subject))
    os.makedirs(folder, exist_ok=True)

    if request.method == 'POST' and role in ['admin', 'teacher']:
        file = request.files['assignment']
        if file and file.filename:
            file.save(os.path.join(folder, secure_filename(file.filename)))
            flash('Assignment uploaded successfully.', 'success')
        return redirect(url_for('subject_assignments', sem=sem, subject=subject))

    files = os.listdir(folder) if os.path.exists(folder) else []
    return render_template('subject_assignments.html', sem=sem, subject=subject, files=files, role=role)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT id, role FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user[0]
            session['username'] = username
            session['role'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        cursor.execute("INSERT INTO users (name, email, username, password) VALUES (%s, %s, %s, %s)", (name, email, username, password))
        conn.commit()
        flash('Registration successful.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/gallery', methods=['GET', 'POST'])
@login_required
def gallery():
    role = session.get('role')
    gallery_folder = os.path.join('static', 'gallery')
    os.makedirs(gallery_folder, exist_ok=True)

    if request.method == 'POST' and role in ['admin', 'teacher']:
        file = request.files['image']
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(gallery_folder, filename))
            flash('Image uploaded!', 'success')
        return redirect(url_for('gallery'))

    images = os.listdir(gallery_folder)
    return render_template('gallery.html', images=images, role=role)

@app.route('/gallery/delete/<filename>', methods=['POST'])
@login_required
def delete_gallery_image(filename):
    if session.get('role') not in ['admin', 'teacher']:
        return redirect('/login')
    file_path = os.path.join('static', 'gallery', filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash('Image deleted.', 'success')
    return redirect(url_for('gallery'))
####announcements

@app.route('/announcements', methods=['GET', 'POST'])
@login_required
def announcements():
    role = session.get('role')
    username = session.get('username')

    if request.method == 'POST' and role in ['admin', 'teacher']:
        title = request.form['title']
        content = request.form['content']
        cursor.execute("INSERT INTO announcements (title, content, posted_by) VALUES (%s, %s, %s)",
                       (title, content, username))
        conn.commit()
        flash("Announcement posted!", "success")
        return redirect(url_for('announcements'))

    cursor.execute("SELECT * FROM announcements ORDER BY posted_on DESC")
    data = cursor.fetchall()
    return render_template("announcements.html", announcements=data, role=role)



if __name__ == '__main__':
    app.run(debug=True)
