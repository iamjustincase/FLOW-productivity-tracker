# data_manager.py (v1.1 - Final V1)

# --- Imports ---
import sqlite3  # Reason: For creating and interacting with the SQL database file.
from datetime import datetime  # Reason: To create timestamps for each log entry.

# --- Constants ---
# Defines the database file name.
DB_FILE = "flow_data.db" 

# --- Utility Function ---
def init_database():
    """
    Utility: Creates the database file and the 'activity_log' table
    if they don't already exist.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        category TEXT NOT NULL,
        app_name TEXT
    )
    ''')

    conn.commit()
    conn.close()
    print(f"Database '{DB_FILE}' initialized.")

# --- Core Logic ---
def log_event(category, app_name):
    """
    Core Logic: Inserts one "event" (one row) into the activity_log table.
    This is called by the "slow" thread every 5 seconds.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    timestamp = datetime.now() 

    cursor.execute('''
    INSERT INTO activity_log (timestamp, category, app_name)
    VALUES (?, ?, ?)
    ''', (timestamp, category, app_name))

    conn.commit()
    conn.close()