import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from pathlib import Path

from src.models.event import Event
from src.storage.database import CONTEXT_COLUMNS, initialize, save_event_model


class DatabaseTests(unittest.TestCase):

    def test_initialize_migrates_legacy_database_without_losing_events(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "legacy.db"

            with closing(sqlite3.connect(database)) as conn, conn:
                conn.execute("""
                    CREATE TABLE events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        start_time TEXT,
                        end_time TEXT,
                        duration INTEGER,
                        application TEXT,
                        title TEXT
                    )
                """)
                conn.execute("""
                    INSERT INTO events(
                        start_time, end_time, duration, application, title
                    ) VALUES ('2026-01-01', '2026-01-01', 10, 'Test', 'Legacy')
                """)

            initialize(database)

            with closing(sqlite3.connect(database)) as conn:
                columns = {
                    row[1] for row in conn.execute("PRAGMA table_info(events)")
                }
                count = conn.execute("SELECT count(*) FROM events").fetchone()[0]
                version = conn.execute("PRAGMA user_version").fetchone()[0]

            self.assertTrue(set(CONTEXT_COLUMNS).issubset(columns))
            self.assertEqual(count, 1)
            self.assertEqual(version, 1)

    def test_save_event_model_persists_typed_context(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "events.db"
            initialize(database)
            event = Event(
                application="Lex Doctor",
                title="Procesos - Cliente C/ Demandado",
                start_time=datetime(2026, 1, 1, 10, 0, 0),
                end_time=datetime(2026, 1, 1, 10, 0, 5),
                duration=5,
                client="Cliente",
                case="Cliente C/ Demandado",
                section="Procesos",
            )

            save_event_model(event, database)

            with closing(sqlite3.connect(database)) as conn:
                row = conn.execute(
                    "SELECT duration, client, case_name, section FROM events"
                ).fetchone()

            self.assertEqual(row, (5, "Cliente", "Cliente C/ Demandado", "Procesos"))


if __name__ == "__main__":
    unittest.main()
