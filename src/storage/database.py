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

DATABASE = Path("data") / "secondchair.db"


def connect():
    return sqlite3.connect(DATABASE)


def initialize():

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp TEXT NOT NULL,

            application TEXT NOT NULL,

            title TEXT NOT NULL,

            duration INTEGER DEFAULT 0

        )
    """)

    conn.commit()
    conn.close()


def save_event(timestamp, application, title, duration=0):

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO events
        (timestamp, application, title, duration)
        VALUES (?, ?, ?, ?)
    """, (
        timestamp,
        application,
        title,
        duration
    ))

    conn.commit()
    conn.close()