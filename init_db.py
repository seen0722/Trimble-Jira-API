import sqlite3
import os

DB_NAME = "dashboard.db"

def init_db():
    if os.path.exists(DB_NAME):
        print(f"Database {DB_NAME} already exists.")
        # Optional: could check for schema migration here
    else:
        print(f"Creating new database: {DB_NAME}")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Table: Snapshots
    # Records when a data collection run happened
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS snapshots (
            snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_issues INTEGER,
            note TEXT
        )
    ''')

    # Table: Issues
    # Stores the state of each issue at the time of the snapshot
    # We store denormalized data for easier trending (e.g., historical status)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER,
            key TEXT,
            summary TEXT,
            status TEXT,
            priority TEXT,
            assignee TEXT,
            created_date DATETIME,
            resolution_date DATETIME,
            type TEXT,
            component TEXT,
            reporter TEXT,
            updated_date DATETIME,
            labels TEXT,
            latest_comment TEXT,
            llm_summary TEXT,
            FOREIGN KEY(snapshot_id) REFERENCES snapshots(snapshot_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
