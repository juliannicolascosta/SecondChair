"""
Second Chair

Módulo:
Storage

Archivo:
database.py

Responsabilidad:
Administrar la base de datos SQLite.
"""

import sqlite3
from pathlib import Path


DATA_FOLDER = Path("data")
DATABASE = DATA_FOLDER / "secondchair.db"


def connect():
    DATA_FOLDER.mkdir(exist_ok=True)
    return sqlite3.connect(DATABASE)


def initialize():
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                end_time TEXT,
                duration INTEGER,
                application TEXT,
                title TEXT
            )
        """)
        conn.commit()


def save_event(start_time, end_time, duration, application, title):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO events (
                start_time,
                end_time,
                duration,
                application,
                title
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (start_time, end_time, duration, application, title)
        )
        conn.commit()