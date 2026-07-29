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

DATABASE = "secondchair.db"


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

            title TEXT NOT NULL

        )
    """)

    conn.commit()
    conn.close()


def save_event(timestamp, application, title):

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO events
        (timestamp, application, title)
        VALUES (?, ?, ?)
    """, (timestamp, application, title))

    conn.commit()
    conn.close()