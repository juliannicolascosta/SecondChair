"""
Second Chair

Módulo:
Analytics

Archivo:
queries.py

Responsabilidad:
Consultas sobre la base de datos.
"""

import sqlite3
from pathlib import Path


DATABASE = Path("data") / "secondchair.db"


def connect():
    return sqlite3.connect(DATABASE)


def events_today():

    with connect() as conn:

        cursor = conn.cursor()

        cursor.execute(

            """

            SELECT

                application,
                title,
                duration,
                section,
                client,
                case_name,
                project,
                document

            FROM events

            WHERE date(start_time)=date('now','localtime')

            ORDER BY start_time

            """

        )

        return cursor.fetchall()