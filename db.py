"""
db.py
Centralized database connection helper using PyMySQL.
"""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    connection = pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor  # rows returned as dicts
    )
    return connection