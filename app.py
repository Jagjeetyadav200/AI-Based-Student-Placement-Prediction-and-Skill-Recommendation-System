"""
app.py
Main Flask application: authentication, profile, prediction,
history, and admin routes.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import joblib
import numpy as np
import os
from dotenv import load_dotenv
from db import get_db_connection

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ---- Load ML model once at startup ----
MODEL_PATH = "model/placement_model.pkl"
model = None
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    print("⚠️  WARNING: Model file not found. Run train_model.py first.")

# Feature order MUST match train_model.py exactly
FEATURES = [
    "cgpa", "tenth_percentage", "twelfth_percentage", "backlogs",
    "projects", "internships", "certifications", "communication_level",
    "aptitude_score", "dsa_level", "python_level", "sql_level"
]

# Thresholds for placement category (clearly defined, used consistently everywhere)
HIGH_THRESHOLD = 70.0    # >= 70% probability => HIGH
MEDIUM_THRESHOLD = 40.0  # 40-69.99% => MEDIUM, below 40% => LOW

def get_category(probability):
    if probability >= HIGH_THRESHOLD:
        return "HIGH"
    elif probability >= MEDIUM_THRESHOLD:
        return "MEDIUM"
    else:
        return "LOW"
# Rule-based skill recommendation and strength/weakness analysis.
# NOTE: This is transparent if/else logic — NOT deep learning or AI-based
# recommendation. Documented honestly as required.
SKILL_THRESHOLD = 6   # out of 10
APTITUDE_THRESHOLD = 60  # out of 100

def analyze_profile(profile_data):
    strengths = []
    weaknesses = []
    recommended_skills = []

    skill_checks = [
        ("DSA", profile_data["dsa_level"], "dsa"),
        ("Python", profile_data["python_level"], "python"),
        ("SQL", profile_data["sql_level"], "sql"),
        ("Communication", profile_data["communication_level"], "communication"),
    ]
    for label, value, _ in skill_checks:
        if value >= SKILL_THRESHOLD + 1:
            strengths.append(f"Strong {label} skills ({value}/10)")
        elif value < SKILL_THRESHOLD:
            weaknesses.append(f"{label} needs improvement ({value}/10)")
            recommended_skills.append(label)

    aptitude = float(profile_data["aptitude_score"])
    if aptitude >= 75:
        strengths.append(f"Strong aptitude score ({aptitude}%)")
    elif aptitude < APTITUDE_THRESHOLD:
        weaknesses.append(f"Aptitude score is below average ({aptitude}%)")
        recommended_skills.append("Aptitude")

    if int(profile_data["projects"]) >= 3:
        strengths.append(f"Good project experience ({profile_data['projects']} projects)")
    elif int(profile_data["projects"]) < 2:
        weaknesses.append("Limited number of projects")
        recommended_skills.append("Building Projects")

    if int(profile_data["internships"]) >= 1:
        strengths.append("Has internship experience")
    else:
        weaknesses.append("No internship experience yet")

    if int(profile_data["certifications"]) < 1:
        weaknesses.append("No certifications listed")
        recommended_skills.append("Relevant Certifications")

    if int(profile_data["backlogs"]) > 0:
        weaknesses.append(f"{profile_data['backlogs']} active backlog(s)")

    return strengths, weaknesses, recommended_skills
# ---- Decorators for access control ----
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # ---- Validation ----
        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("register"))

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash("Email already registered.", "error")
                    return redirect(url_for("register"))

                password_hash = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                    (name, email, password_hash, "student")
                )
                conn.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Database error: {str(e)}", "error")
            return redirect(url_for("register"))
        finally:
            conn.close()

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("login"))

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()

            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["name"] = user["name"]
                session["role"] = user["role"]
                flash(f"Welcome back, {user['name']}!", "success")
                if user["role"] == "admin":
                    return redirect(url_for("admin_dashboard"))
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid email or password.", "error")
                return redirect(url_for("login"))
        except Exception as e:
            flash(f"Database error: {str(e)}", "error")
            return redirect(url_for("login"))
        finally:
            conn.close()

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM student_profiles WHERE user_id = %s", (session["user_id"],))
            profile = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM predictions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                (session["user_id"],)
            )
            latest_prediction = cursor.fetchone()
    finally:
        conn.close()

    return render_template(
        "dashboard.html",
        profile=profile,
        latest_prediction=latest_prediction
    )

# ---------------- PROFILE (create/update) ----------------
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    conn = get_db_connection()
    try:
        if request.method == "POST":
            data = {
                "cgpa": request.form.get("cgpa"),
                "tenth_percentage": request.form.get("tenth_percentage"),
                "twelfth_percentage": request.form.get("twelfth_percentage"),
                "backlogs": request.form.get("backlogs"),
                "projects": request.form.get("projects"),
                "internships": request.form.get("internships"),
                "certifications": request.form.get("certifications"),
                "communication_level": request.form.get("communication_level"),
                "aptitude_score": request.form.get("aptitude_score"),
                "dsa_level": request.form.get("dsa_level"),
                "python_level": request.form.get("python_level"),
                "sql_level": request.form.get("sql_level"),
            }

            # ---- Validation ----
            try:
                cgpa = float(data["cgpa"])
                tenth = float(data["tenth_percentage"])
                twelfth = float(data["twelfth_percentage"])
                backlogs = int(data["backlogs"])
                projects = int(data["projects"])
                internships = int(data["internships"])
                certifications = int(data["certifications"])
                communication = int(data["communication_level"])
                aptitude = float(data["aptitude_score"])
                dsa = int(data["dsa_level"])
                python_skill = int(data["python_level"])
                sql_skill = int(data["sql_level"])
            except (ValueError, TypeError):
                flash("All fields must be valid numbers.", "error")
                return redirect(url_for("profile"))

            errors = []
            if not (0 <= cgpa <= 10):
                errors.append("CGPA must be between 0 and 10.")
            if not (0 <= tenth <= 100) or not (0 <= twelfth <= 100):
                errors.append("Percentages must be between 0 and 100.")
            if not (0 <= aptitude <= 100):
                errors.append("Aptitude score must be between 0 and 100.")
            if backlogs < 0 or projects < 0 or internships < 0 or certifications < 0:
                errors.append("Counts cannot be negative.")
            for level, label in [(communication, "Communication"), (dsa, "DSA"),
                                  (python_skill, "Python"), (sql_skill, "SQL")]:
                if not (1 <= level <= 10):
                    errors.append(f"{label} level must be between 1 and 10.")

            if errors:
                for e in errors:
                    flash(e, "error")
                return redirect(url_for("profile"))

            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM student_profiles WHERE user_id = %s", (session["user_id"],))
                existing = cursor.fetchone()

                if existing:
                    cursor.execute("""
                        UPDATE student_profiles SET
                            cgpa=%s, tenth_percentage=%s, twelfth_percentage=%s, backlogs=%s,
                            projects=%s, internships=%s, certifications=%s, communication_level=%s,
                            aptitude_score=%s, dsa_level=%s, python_level=%s, sql_level=%s
                        WHERE user_id=%s
                    """, (cgpa, tenth, twelfth, backlogs, projects, internships, certifications,
                          communication, aptitude, dsa, python_skill, sql_skill, session["user_id"]))
                else:
                    cursor.execute("""
                        INSERT INTO student_profiles
                        (user_id, cgpa, tenth_percentage, twelfth_percentage, backlogs,
                         projects, internships, certifications, communication_level,
                         aptitude_score, dsa_level, python_level, sql_level)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (session["user_id"], cgpa, tenth, twelfth, backlogs, projects,
                          internships, certifications, communication, aptitude,
                          dsa, python_skill, sql_skill))
                conn.commit()

            flash("Profile saved successfully.", "success")
            return redirect(url_for("dashboard"))

        # GET request — load existing profile if present
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM student_profiles WHERE user_id = %s", (session["user_id"],))
            profile_data = cursor.fetchone()
        return render_template("profile.html", profile=profile_data)
    finally:
        conn.close()

# ---------------- PREDICTION ----------------
@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    if model is None:
        flash("Prediction model is not available. Please contact admin.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM student_profiles WHERE user_id = %s", (session["user_id"],))
            profile_data = cursor.fetchone()

        if not profile_data:
            flash("Please complete your profile before predicting.", "error")
            return redirect(url_for("profile"))

        if request.method == "POST":
            # Build feature vector in the EXACT order used during training
            input_values = [[
                float(profile_data["cgpa"]),
                float(profile_data["tenth_percentage"]),
                float(profile_data["twelfth_percentage"]),
                int(profile_data["backlogs"]),
                int(profile_data["projects"]),
                int(profile_data["internships"]),
                int(profile_data["certifications"]),
                int(profile_data["communication_level"]),
                float(profile_data["aptitude_score"]),
                int(profile_data["dsa_level"]),
                int(profile_data["python_level"]),
                int(profile_data["sql_level"]),
            ]]

            input_array = np.array(input_values)
            probability = model.predict_proba(input_array)[0][1] * 100  # class 1 = placed
            probability = round(probability, 2)
            category = get_category(probability)

            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO predictions (user_id, probability, category) VALUES (%s, %s, %s)",
                    (session["user_id"], probability, category)
                )
                new_prediction_id = cursor.lastrowid
                conn.commit()

            return redirect(url_for("result", prediction_id=new_prediction_id))

        return render_template("prediction.html", profile=profile_data)
    finally:
        conn.close()

# ---------------- RESULT ----------------
@app.route("/result/<int:prediction_id>")
@login_required
def result(prediction_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Ownership check: a student can only ever view THEIR OWN prediction.
            # Without the user_id filter, a student could view another
            # student's result just by guessing/incrementing the ID in the URL.
            cursor.execute(
                "SELECT * FROM predictions WHERE id = %s AND user_id = %s",
                (prediction_id, session["user_id"])
            )
            prediction = cursor.fetchone()

            if not prediction:
                flash("Prediction not found.", "error")
                return redirect(url_for("dashboard"))

            cursor.execute("SELECT * FROM student_profiles WHERE user_id = %s", (session["user_id"],))
            profile_data = cursor.fetchone()
    finally:
        conn.close()

    strengths, weaknesses, recommended_skills = analyze_profile(profile_data)

    return render_template(
        "result.html",
        probability=prediction["probability"],
        category=prediction["category"],
        profile=profile_data,
        strengths=strengths,
        weaknesses=weaknesses,
        recommended_skills=recommended_skills
    )
# ---------------- HISTORY ----------------
@app.route("/history")
@login_required
def history():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM predictions WHERE user_id = %s ORDER BY created_at DESC",
                (session["user_id"],)
            )
            records = cursor.fetchall()
    finally:
        conn.close()

    return render_template("history.html", records=records)

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role = 'student'")
            total_students = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM predictions")
            total_predictions = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM predictions WHERE category = 'HIGH'")
            high_count = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM predictions WHERE category = 'MEDIUM'")
            medium_count = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM predictions WHERE category = 'LOW'")
            low_count = cursor.fetchone()["total"]

            cursor.execute("SELECT id, name, email, created_at FROM users WHERE role = 'student'")
            students = cursor.fetchall()
    finally:
        conn.close()

    return render_template(
        "admin.html",
        total_students=total_students,
        total_predictions=total_predictions,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        students=students
    )

# ---------------- ADMIN STUDENT DETAILS ----------------
@app.route("/admin/student/<int:student_id>")
@login_required
@admin_required
def admin_student_details(student_id):
    """Show complete details of one registered student to an admin."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    u.id, u.name, u.email, u.created_at,
                    sp.cgpa, sp.tenth_percentage, sp.twelfth_percentage,
                    sp.backlogs, sp.projects, sp.internships, sp.certifications,
                    sp.communication_level, sp.aptitude_score,
                    sp.dsa_level, sp.python_level, sp.sql_level,
                    sp.updated_at
                FROM users u
                LEFT JOIN student_profiles sp ON sp.user_id = u.id
                WHERE u.id = %s AND u.role = 'student'
                """,
                (student_id,)
            )
            student = cursor.fetchone()

            if not student:
                flash("Student not found.", "error")
                return redirect(url_for("admin_dashboard"))

            cursor.execute(
                """
                SELECT id, probability, category, created_at
                FROM predictions
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (student_id,)
            )
            predictions = cursor.fetchall()
    finally:
        conn.close()

    return render_template(
        "admin_student.html",
        student=student,
        predictions=predictions
    )

# ---------------- ERROR HANDLERS ----------------
@app.errorhandler(404)
def not_found(e):
    return render_template(
        "error.html", code=404,
        title="Page Not Found",
        message="The page you're looking for doesn't exist or may have moved."
    ), 404

@app.errorhandler(500)
def server_error(e):
    return render_template(
        "error.html", code=500,
        title="Something Went Wrong",
        message="An unexpected error occurred on our end. Please try again in a moment."
    ), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template(
        "error.html", code=403,
        title="Access Denied",
        message="You don't have permission to view this page."
    ), 403
if __name__ == "__main__":
    app.run(debug=True)