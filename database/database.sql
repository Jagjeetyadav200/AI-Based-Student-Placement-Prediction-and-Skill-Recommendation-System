-- Placement System Database Schema
-- Run this after creating the 'placement_system' database

USE placement_system;

-- Table 1: Users (authentication)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'admin') NOT NULL DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Student Profiles (academic + skill data)
CREATE TABLE student_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    cgpa DECIMAL(4,2) NOT NULL,
    tenth_percentage DECIMAL(5,2) NOT NULL,
    twelfth_percentage DECIMAL(5,2) NOT NULL,
    backlogs INT NOT NULL DEFAULT 0,
    projects INT NOT NULL DEFAULT 0,
    internships INT NOT NULL DEFAULT 0,
    certifications INT NOT NULL DEFAULT 0,
    communication_level INT NOT NULL,       -- scale 1-10
    aptitude_score DECIMAL(5,2) NOT NULL,   -- percentage 0-100
    dsa_level INT NOT NULL,                 -- scale 1-10
    python_level INT NOT NULL,              -- scale 1-10
    sql_level INT NOT NULL,                 -- scale 1-10
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table 3: Predictions (history)
CREATE TABLE predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    probability DECIMAL(5,2) NOT NULL,   -- e.g. 82.50
    category ENUM('HIGH', 'MEDIUM', 'LOW') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);