"""Read-only queries used by the Analytics layer."""

import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from src.storage.database import DATABASE


EVENT_COLUMNS = (
    "start_time",
    "end_time",
    "duration",
    "application",
    "title",
    "section",
    "client",
    "case_name",
    "project",
    "document",
    "activity_type",
    "context_source",
    "context_confidence",
    "context_confirmed",
)


def events_for_date(day=None, database=DATABASE):
    """Return the day's completed events in chronological order."""

    selected_day = day or date.today()
    database = Path(database)

    with closing(sqlite3.connect(database)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT {', '.join(EVENT_COLUMNS)}
            FROM events
            WHERE date(start_time) = date(?)
            ORDER BY start_time, id
            """,
            (selected_day.isoformat(),),
        ).fetchall()

    return [dict(row) for row in rows]


def events_today(database=DATABASE):
    """Backward-compatible alias for callers that need today's events."""

    return events_for_date(database=database)


def interaction_sessions_for_date(day=None, database=DATABASE):
    """Return aggregate facts only; detailed interactions are intentionally absent."""

    selected_day = day or date.today()
    database = Path(database)
    with closing(sqlite3.connect(database)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT * FROM work_session_interactions
            WHERE day = ?
            ORDER BY start_time, session_id
            """,
            (selected_day.isoformat(),),
        ).fetchall()
    return [dict(row) for row in rows]


def idle_metrics_for_date(day=None, database=DATABASE):
    selected_day = day or date.today()
    database = Path(database)
    with closing(sqlite3.connect(database)) as conn:
        row = conn.execute(
            """
            SELECT observed_seconds, active_seconds, inactive_seconds
            FROM daily_idle_metrics WHERE day = ?
            """,
            (selected_day.isoformat(),),
        ).fetchone()
    if row is None:
        return {"observed_seconds": 0, "active_seconds": 0, "inactive_seconds": 0}
    return dict(zip(("observed_seconds", "active_seconds", "inactive_seconds"), row))
