"""
create_admin.py
One-time script to create the admin user correctly.
Run once, then this file can be deleted or kept for reference
(it safely does nothing if the admin already exists).
"""

from werkzeug.security import generate_password_hash
from db import get_db_connection

ADMIN_NAME = "Admin"
ADMIN_EMAIL = "admin@placement.com"
ADMIN_PASSWORD = "YourAdminPassword123"  # change this before running

conn = get_db_connection()
try:
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM users WHERE email = %s", (ADMIN_EMAIL,))
        if cursor.fetchone():
            print("⚠️  Admin already exists. No action taken.")
        else:
            password_hash = generate_password_hash(ADMIN_PASSWORD)
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                (ADMIN_NAME, ADMIN_EMAIL, password_hash, "admin")
            )
            conn.commit()
            print("✅ Admin created successfully.")
            print(f"Email: {ADMIN_EMAIL}")
            print(f"Password: {ADMIN_PASSWORD}")
finally:
    conn.close()