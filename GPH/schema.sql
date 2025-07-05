-- Create the database
CREATE DATABASE IF NOT EXISTS student_portal;
USE student_portal;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    standard INT CHECK (standard BETWEEN 1 AND 12),
    role ENUM('admin', 'teacher', 'student') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attendance table
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    date DATE,
    status ENUM('present', 'absent') NOT NULL,
    standard INT,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Materials table
CREATE TABLE materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    filename VARCHAR(255),
    standard INT,
    uploaded_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Assignments table
CREATE TABLE assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    filename VARCHAR(255),
    standard INT,
    uploaded_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    uploaded_by ENUM('admin', 'teacher')
);

-- Announcements
CREATE TABLE announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Gallery
CREATE TABLE gallery (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image_path VARCHAR(255),
    uploaded_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages
CREATE TABLE counselor_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    message TEXT,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Users table (already exists, only if missing add these fields)
-- role: ENUM('admin', 'teacher', 'student')
-- standard: INT (for class year)

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    roll_no VARCHAR(50),
    department VARCHAR(100),
    year INT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    department VARCHAR(100),
    year INT,
    faculty_id INT,
    FOREIGN KEY (faculty_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    subject_id INT,
    date DATE,
    status ENUM('present', 'absent'),
    marked_by INT,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (marked_by) REFERENCES users(id),
    UNIQUE (student_id, subject_id, date)
);
DROP TABLE attendance;

CREATE TABLE students (
  id INT AUTO_INCREMENT PRIMARY KEY,
  enrollment_no VARCHAR(20),
  name VARCHAR(100),
  semester INT
);

CREATE TABLE attendance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  enrollment_no VARCHAR(20),
  name VARCHAR(100),
  semester INT,
  subject VARCHAR(50),
  date DATE,
  status VARCHAR(10)
);

ALTER TABLE users MODIFY name VARCHAR(255) NULL;


