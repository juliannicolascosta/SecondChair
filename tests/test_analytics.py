import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.analytics.queries import events_for_date
from src.analytics.reports import (
    build_daily_summary,
    daily_summary,
    seconds_to_text,
    today_summary,
)
from src.storage.database import initialize, save_event


class AnalyticsTests(unittest.TestCase):

    def test_seconds_to_text_keeps_sub_minute_precision(self):
        self.assertEqual(seconds_to_text(0), "0s")
        self.assertEqual(seconds_to_text(59), "59s")
        self.assertEqual(seconds_to_text(60), "1m")
        self.assertEqual(seconds_to_text(3660), "1h 1m")

    def test_summary_aggregates_all_required_dimensions(self):
        rows = [
            {
                "duration": 30,
                "application": "Lex Doctor",
                "client": "Cliente A",
                "case_name": "Expediente 1",
                "section": "Procesos",
                "project": None,
                "document": None,
            },
            {
                "duration": 45,
                "application": "Lex Doctor",
                "client": "Cliente A",
                "case_name": "Expediente 1",
                "section": "Movimientos",
                "project": None,
                "document": None,
            },
            {
                "duration": 90,
                "application": "VS Code",
                "client": None,
                "case_name": None,
                "section": None,
                "project": "SecondChair",
                "document": None,
            },
        ]

        summary = build_daily_summary(rows, date(2026, 8, 5))

        self.assertEqual(summary.total_seconds, 165)
        self.assertEqual(summary.by_application["Lex Doctor"], 75)
        self.assertEqual(summary.by_case["Expediente 1"], 75)
        self.assertEqual(summary.by_client["Cliente A"], 75)
        self.assertEqual(summary.context_changes, 2)

    def test_daily_query_filters_date_and_report_is_renderable(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "analytics.db"
            initialize(database)
            save_event(
                "2026-08-05 09:00:00",
                "2026-08-05 09:00:42",
                42,
                "Outlook",
                "Inbox",
                client="Cliente sintético",
                case_name="Expediente sintético",
                database=database,
            )
            save_event(
                "2026-08-04 09:00:00",
                "2026-08-04 09:01:00",
                60,
                "Outlook",
                "Previous day",
                database=database,
            )

            rows = events_for_date(date(2026, 8, 5), database)
            summary = daily_summary(date(2026, 8, 5), database)

            self.assertEqual(len(rows), 1)
            self.assertEqual(summary.total_seconds, 42)

            rendered = []
            today_summary(database, rendered.append)
            self.assertTrue(any("Tiempo total" in line for line in rendered))


if __name__ == "__main__":
    unittest.main()
