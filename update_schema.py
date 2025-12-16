import sqlite3
import os

DB_NAME = "dashboard.db"

def add_columns():
    if not os.path.exists(DB_NAME):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE issues ADD COLUMN labels TEXT")
        print("Added column: labels")
    except sqlite3.OperationalError:
        print("Column 'labels' likely already exists.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns()
