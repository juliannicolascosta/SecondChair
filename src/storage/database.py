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
from contextlib import closing
from pathlib import Path

from src.models.event import Event


DATA_FOLDER = Path("data")
DATABASE = DATA_FOLDER / "secondchair.db"


SCHEMA_VERSION = 1

CONTEXT_COLUMNS = {
    "section": "TEXT",
    "client": "TEXT",
    "case_name": "TEXT",
    "project": "TEXT",
    "document": "TEXT",
}


def connect(database=DATABASE):
    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(database)


def initialize(database=DATABASE):

    with closing(connect(database)) as conn, conn:

        cursor = conn.cursor()

        cursor.execute("""

            CREATE TABLE IF NOT EXISTS events (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                start_time TEXT,

                end_time TEXT,

                duration INTEGER,

                application TEXT,

                title TEXT,

                section TEXT,

                client TEXT,

                case_name TEXT,

                project TEXT,

                document TEXT

            )

        """)

        existing_columns = {
            row[1]
            for row in cursor.execute("PRAGMA table_info(events)")
        }

        for column, column_type in CONTEXT_COLUMNS.items():
            if column not in existing_columns:
                cursor.execute(
                    f"ALTER TABLE events ADD COLUMN {column} {column_type}"
                )

        cursor.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

        conn.commit()


def save_event(

    start_time,
    end_time,
    duration,
    application,
    title,
    section=None,
    client=None,
    case_name=None,
    project=None,
    document=None,
    database=DATABASE

):

    with closing(connect(database)) as conn, conn:

        cursor = conn.cursor()

        cursor.execute(

            """

            INSERT INTO events(

                start_time,
                end_time,
                duration,
                application,
                title,
                section,
                client,
                case_name,
                project,
                document

            )

            VALUES(?,?,?,?,?,?,?,?,?,?)

            """,

            (

                start_time,
                end_time,
                duration,
                application,
                title,
                section,
                client,
                case_name,
                project,
                document

            )

        )

        conn.commit()


def save_event_model(event: Event, database=DATABASE):
    """Persist a completed Event using its typed fields."""

    context = event.context or {}

    save_event(
        event.start_time.strftime("%Y-%m-%d %H:%M:%S"),
        event.end_time.strftime("%Y-%m-%d %H:%M:%S"),
        event.duration,
        event.application,
        event.title,
        event.section or context.get("section"),
        event.client or context.get("client"),
        event.case or context.get("case"),
        event.project or context.get("project"),
        event.document or context.get("document"),
        database=database,
    )
