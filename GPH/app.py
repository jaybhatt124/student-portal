from flask import Flask, render_template, request, redirect, send_from_directory, flash, session, url_for
from werkzeug.utils import secure_filename
import mysql.connector
import csv, os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
UPLOAD_FOLDER = 'uploads'
MATERIAL_FOLDER = 'materials'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MATERIAL_FOLDER'] = MATERIAL_FOLDER

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
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/attendance')
@login_required
def attendance():
    return render_template('attendance.html')

@app.route('/upload_csv', methods=['POST'])
@login_required
def upload_csv():
    semester = request.form['semester']
    subject = request.form['subject']
    file = request.files['csv_file']
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                enroll, name = row[1], row[2]
                cursor.execute("INSERT INTO students (enrollment_no, name, semester) VALUES (%s, %s, %s)", (enroll, name, semester))
        conn.commit()
        flash('CSV uploaded and students saved.')
    return redirect(url_for('attendance'))

@app.route('/mark_attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    semester = request.args.get('semester')
    subject = request.args.get('subject')
    if request.method == 'POST':
        attendance = request.form.getlist('attendance')
        today = datetime.now().date()
        for student in attendance:
            enrollment_no, name = student.split('|')
            cursor.execute("INSERT INTO attendance (enrollment_no, name, semester, subject, date, status) VALUES (%s, %s, %s, %s, %s, %s)",
                           (enrollment_no, name, semester, subject, today, 'Present'))
        conn.commit()
        flash('Attendance marked successfully.')
        return redirect(url_for('attendance'))
    else:
        cursor.execute("SELECT enrollment_no, name FROM students WHERE semester=%s", (semester,))
        students = cursor.fetchall()
        return render_template('mark_attendance.html', students=students, semester=semester, subject=subject)


@app.route('/materials')
def materials():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('materials.html')


# ─────── Route: Semester Page with Subjects ───────
# ─────── Route: List Subjects for a Semester ───────
@app.route('/materials/sem/<int:sem>')
def semester_subjects(sem):
    if 'user_id' not in session:
        return redirect('/login')
    role = session.get('role')
    subjects = ["Mathematics", "Physics", "Chemistry", "Biology", "English", "Computer"]
    return render_template("semester_subjects.html", sem=sem, subjects=subjects, role=role)


from datetime import datetime
# ─────── Route: Upload/View Materials by Subject ───────
import json
from datetime import datetime

@app.route('/materials/sem/<int:sem>/subject/<subject>', methods=['GET', 'POST'])
def subject_materials(sem, subject):
    if 'user_id' not in session:
        return redirect('/login')

    role = session.get('role')
    safe_subject = secure_filename(subject)
    subject_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'sem{sem}', safe_subject)
    os.makedirs(subject_folder, exist_ok=True)

    # Metadata file path
    meta_file_path = os.path.join(subject_folder, 'upload_info.json')

    # Load existing metadata
    if os.path.exists(meta_file_path):
        with open(meta_file_path, 'r') as f:
            upload_info = json.load(f)
    else:
        upload_info = {}

    # Handle material upload
    if request.method == 'POST' and role in ['admin', 'teacher']:
        file = request.files['material']
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(subject_folder, filename)
            file.save(filepath)

            # Save metadata
            upload_info[filename] = {
                "uploaded_by": session.get("username", "Unknown"),
                "uploaded_on": datetime.now().strftime('%Y-%m-%d %H:%M'),
                "size": round(os.path.getsize(filepath) / 1024, 2)  # Size in KB
            }
            with open(meta_file_path, 'w') as f:
                json.dump(upload_info, f)

            flash('Material uploaded successfully!', 'success')
        return redirect(url_for('subject_materials', sem=sem, subject=subject))

    # Get all files except metadata
    files = [f for f in os.listdir(subject_folder) if f != 'upload_info.json']

    # Load custom template if needed
    subject_lower = subject.lower()
    if subject_lower == "mathematics":
        template = "math_materials.html"
    elif subject_lower == "physics":
        template = "physics_materials.html"
    else:
        template = "subject_materials.html"

    return render_template(template, sem=sem, subject=subject, files=files, role=role, upload_info=upload_info)





@app.route('/materials/sem/<int:sem>/subject/<subject>/delete/<filename>', methods=['POST'])
def delete_material(sem, subject, filename):
    if 'user_id' not in session or session.get('role') not in ['admin', 'teacher']:
        return redirect('/login')

    subject_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'sem{sem}', secure_filename(subject))
    file_path = os.path.join(subject_folder, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        flash('Material deleted successfully!', 'success')
    else:
        flash('File not found!', 'danger')

    return redirect(url_for('subject_materials', sem=sem, subject=subject))








@app.route('/upload_material', methods=['POST'])
@login_required
def upload_material():
    semester = request.form['semester']
    subject = request.form['subject']
    file = request.files['material_file']
    if file:
        filename = secure_filename(file.filename)
        folder = os.path.join(app.config['MATERIAL_FOLDER'], f"sem_{semester}", subject)
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))
        flash('Material uploaded successfully.')
    return redirect(url_for('attendance'))

@app.route('/view_materials')
@login_required
def view_materials():
    semester = request.args.get('semester')
    subject = request.args.get('subject')
    folder = os.path.join(app.config['MATERIAL_FOLDER'], f"sem_{semester}", subject)
    if os.path.exists(folder):
        files = os.listdir(folder)
    else:
        files = []
    return render_template('view_materials.html', files=files, semester=semester, subject=subject)

@app.route('/download/<semester>/<subject>/<filename>')
@login_required
def download_material(semester, subject, filename):
    folder = os.path.join(app.config['MATERIAL_FOLDER'], f"sem_{semester}", subject)
    return send_from_directory(folder, filename)

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT id FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user[0]
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
        
        cursor.execute(
            "INSERT INTO users (name, email, username, password) VALUES (%s, %s, %s, %s)",
            (name, email, username, password)
        )
        conn.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/download/<int:sem>/<subject>/<filename>')
def download_file(sem, subject, filename):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], f'sem{sem}', secure_filename(subject))
    return send_from_directory(folder, filename)



if __name__ == '__main__':
    app.run(debug=True)
