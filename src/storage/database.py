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


# Additive tables remain compatible with the existing v1 event schema.
SCHEMA_VERSION = 1

INTERACTION_COLUMNS = (
    "interaction_count",
    "mouse_clicks",
    "keyboard_actions",
    "scroll_actions",
    "text_fields_used",
    "buttons_used",
    "combo_boxes_used",
    "menus_used",
    "window_switches",
)

CONTEXT_COLUMNS = {
    "process_name": "TEXT",
    "section": "TEXT",
    "client": "TEXT",
    "case_name": "TEXT",
    "project": "TEXT",
    "document": "TEXT",
    "activity_type": "TEXT",
    "context_source": "TEXT",
    "context_confidence": "REAL",
    "context_confirmed": "INTEGER NOT NULL DEFAULT 0",
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

                , activity_type TEXT

                , context_source TEXT

                , context_confidence REAL

                , context_confirmed INTEGER NOT NULL DEFAULT 0

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_session_interactions (
                session_key TEXT PRIMARY KEY,
                session_id INTEGER,
                day TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration INTEGER NOT NULL,
                label TEXT,
                interaction_count INTEGER NOT NULL DEFAULT 0,
                mouse_clicks INTEGER NOT NULL DEFAULT 0,
                keyboard_actions INTEGER NOT NULL DEFAULT 0,
                scroll_actions INTEGER NOT NULL DEFAULT 0,
                text_fields_used INTEGER NOT NULL DEFAULT 0,
                buttons_used INTEGER NOT NULL DEFAULT 0,
                combo_boxes_used INTEGER NOT NULL DEFAULT 0,
                menus_used INTEGER NOT NULL DEFAULT 0,
                window_switches INTEGER NOT NULL DEFAULT 0
            )
        """)

        interaction_columns = {
            row[1]
            for row in cursor.execute("PRAGMA table_info(work_session_interactions)")
        }
        if "control_metrics_status" not in interaction_columns:
            cursor.execute(
                "ALTER TABLE work_session_interactions "
                "ADD COLUMN control_metrics_status TEXT NOT NULL DEFAULT 'unavailable'"
            )
        if "control_metrics_reason" not in interaction_columns:
            cursor.execute(
                "ALTER TABLE work_session_interactions ADD COLUMN control_metrics_reason TEXT"
            )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_idle_metrics (
                day TEXT PRIMARY KEY,
                observed_seconds INTEGER NOT NULL DEFAULT 0,
                active_seconds INTEGER NOT NULL DEFAULT 0,
                inactive_seconds INTEGER NOT NULL DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_traces (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                status TEXT NOT NULL CHECK(status IN ('running','completed','cancelled')),
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS one_running_workflow_trace
            ON workflow_traces(status) WHERE status = 'running'
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_trace_sessions (
                trace_id TEXT NOT NULL REFERENCES workflow_traces(id) ON DELETE CASCADE,
                session_key TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration INTEGER NOT NULL,
                applications TEXT NOT NULL,
                processes TEXT NOT NULL,
                window_count INTEGER NOT NULL,
                context_switches INTEGER NOT NULL,
                interaction_count INTEGER NOT NULL,
                mouse_clicks INTEGER NOT NULL,
                keyboard_actions INTEGER NOT NULL,
                scroll_actions INTEGER NOT NULL,
                text_fields_used INTEGER NOT NULL,
                buttons_used INTEGER NOT NULL,
                combo_boxes_used INTEGER NOT NULL,
                menus_used INTEGER NOT NULL,
                window_switches INTEGER NOT NULL,
                control_metrics_status TEXT NOT NULL,
                PRIMARY KEY(trace_id, session_key)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_trace_intervals (
                trace_id TEXT PRIMARY KEY REFERENCES workflow_traces(id) ON DELETE CASCADE,
                applications TEXT NOT NULL,
                processes TEXT NOT NULL,
                interaction_count INTEGER NOT NULL,
                mouse_clicks INTEGER NOT NULL,
                keyboard_actions INTEGER NOT NULL,
                scroll_actions INTEGER NOT NULL,
                text_fields_used INTEGER NOT NULL,
                buttons_used INTEGER NOT NULL,
                combo_boxes_used INTEGER NOT NULL,
                menus_used INTEGER NOT NULL,
                window_switches INTEGER NOT NULL,
                control_metrics_status TEXT NOT NULL,
                control_metrics_reason TEXT,
                finalized_at TEXT NOT NULL
            )
        """)

        cursor.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

        conn.commit()


def save_event(

    start_time,
    end_time,
    duration,
    application,
    title,
    process_name=None,
    section=None,
    client=None,
    case_name=None,
    project=None,
    document=None,
    activity_type=None,
    context_source=None,
    context_confidence=None,
    context_confirmed=False,
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
                process_name,
                section,
                client,
                case_name,
                project,
                document

                , activity_type
                , context_source
                , context_confidence
                , context_confirmed

            )

            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

            """,

            (

                start_time,
                end_time,
                duration,
                application,
                title,
                process_name,
                section,
                client,
                case_name,
                project,
                document

                , activity_type
                , context_source
                , context_confidence
                , int(bool(context_confirmed))

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
        event.process_name,
        event.section or context.get("section"),
        event.client or context.get("client"),
        event.case or context.get("case"),
        event.project or context.get("project"),
        event.document or context.get("document"),
        event.activity_type or context.get("activity_type"),
        event.context_source or context.get("context_source"),
        event.context_confidence,
        event.context_confirmed,
        database=database,
    )


def save_session_interactions(session, database=DATABASE):
    """Persist only aggregate interaction counters for a closed WorkSession."""

    label = (
        session.case
        or session.client
        or session.project
        or session.primary_application
        or "Sin contexto"
    )
    values = [getattr(session, name, 0) for name in INTERACTION_COLUMNS]
    with closing(connect(database)) as conn, conn:
        conn.execute(
            f"""
            INSERT INTO work_session_interactions (
                session_key, session_id, day, start_time, end_time,
                duration, label, {', '.join(INTERACTION_COLUMNS)}
                , control_metrics_status, control_metrics_reason
            ) VALUES ({', '.join('?' for _ in range(9 + len(INTERACTION_COLUMNS)))})
            ON CONFLICT(session_key) DO UPDATE SET
                {', '.join(f'{name}=excluded.{name}' for name in INTERACTION_COLUMNS)},
                control_metrics_status=excluded.control_metrics_status,
                control_metrics_reason=excluded.control_metrics_reason
            """,
            (
                session.learning_id,
                session.id,
                session.start_time.date().isoformat(),
                session.start_time.isoformat(),
                session.end_time.isoformat(),
                session.duration,
                label,
                *values,
                session.control_metrics_status,
                session.control_metrics_reason,
            ),
        )


def save_idle_metrics(day, tracker, database=DATABASE):
    """Add one runtime's aggregate active/inactive totals to a day."""

    with closing(connect(database)) as conn, conn:
        conn.execute(
            """
            INSERT INTO daily_idle_metrics(
                day, observed_seconds, active_seconds, inactive_seconds
            ) VALUES(?,?,?,?)
            ON CONFLICT(day) DO UPDATE SET
                observed_seconds=observed_seconds + excluded.observed_seconds,
                active_seconds=active_seconds + excluded.active_seconds,
                inactive_seconds=inactive_seconds + excluded.inactive_seconds
            """,
            (
                day.isoformat(),
                tracker.observed_seconds,
                tracker.active_seconds,
                tracker.inactive_seconds,
            ),
        )
