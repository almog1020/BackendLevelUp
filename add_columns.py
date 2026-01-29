"""Add missing columns to the users table."""
import os
from dotenv import load_dotenv
load_dotenv()

import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Connecting to database...")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

columns_to_add = [
    ("last_active", "TIMESTAMP"),
    ("favorite_genre", "VARCHAR(100)"),
    ("preferred_store", "VARCHAR(100)"),
]

for col_name, col_type in columns_to_add:
    try:
        cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};")
        print(f"Added column: {col_name}")
    except psycopg2.errors.DuplicateColumn:
        conn.rollback()
        print(f"Column already exists: {col_name}")

conn.commit()
cur.close()
conn.close()
print("Done!")
