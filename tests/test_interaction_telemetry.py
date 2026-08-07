import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import date, datetime, timedelta
from pathlib import Path

from src.analytics.reports import daily_friction_summary, friction_report
from src.memory.working_memory import WorkingMemory
from src.models.event import Event
from src.storage.database import initialize, save_session_interactions
from src.telemetry.interaction.collector import InteractionCollector
from src.telemetry.interaction.counters import InteractionCounters
from src.telemetry.interaction.models import InteractionEvent, InteractionType
from src.telemetry.interaction.ui_automation import UIAutomationInspector


NOW = datetime(2026, 8, 7, 10, 0, 0)


class FakeSource:
    def __init__(self):
        self.callback = None
        self.starts = 0
        self.stops = 0

    def start(self, callback):
        self.callback = callback
        self.starts += 1

    def stop(self):
        self.stops += 1


class FailingAutomation:
    def ControlFromCursor(self):
        raise OSError("UIA unavailable")


class ButtonAutomation:
    def ControlFromCursor(self):
        return type("Control", (), {"ControlTypeName": "ButtonControl"})()


def completed_event(start=NOW, seconds=60):
    return Event(
        application="Word",
        title="document",
        start_time=start,
        end_time=start + timedelta(seconds=seconds),
        duration=seconds,
    )


class InteractionTelemetryTests(unittest.TestCase):
    def test_counters(self):
        counters = InteractionCounters()
        for kind in (
            InteractionType.MOUSE_CLICK,
            InteractionType.KEYBOARD_ACTIVITY,
            InteractionType.SCROLL,
        ):
            counters.record(InteractionEvent(NOW, kind))
        self.assertEqual(counters.interaction_count, 3)
        self.assertEqual(counters.mouse_clicks, 1)
        self.assertEqual(counters.keyboard_actions, 1)
        self.assertEqual(counters.scroll_actions, 1)

    def test_control_click_is_deduplicated(self):
        collector = InteractionCollector(
            ui_inspector=UIAutomationInspector(ButtonAutomation()),
            clock=lambda: NOW,
        )
        collector.running = True
        event = collector.record(InteractionType.MOUSE_CLICK)
        self.assertEqual(event.interaction_type, InteractionType.BUTTON)
        self.assertEqual(collector.counters.interaction_count, 1)
        self.assertEqual(collector.counters.mouse_clicks, 1)
        self.assertEqual(collector.counters.buttons_used, 1)

    def test_event_model_cannot_store_content(self):
        with self.assertRaises(TypeError):
            InteractionEvent(NOW, InteractionType.KEYBOARD_ACTIVITY, text="secret")
        self.assertNotIn("key", InteractionEvent.__dataclass_fields__)
        self.assertNotIn("value", InteractionEvent.__dataclass_fields__)

    def test_ui_automation_failure_keeps_basic_click(self):
        collector = InteractionCollector(
            ui_inspector=UIAutomationInspector(FailingAutomation()),
            clock=lambda: NOW,
        )
        collector.running = True
        event = collector.record(InteractionType.MOUSE_CLICK)
        self.assertEqual(event.interaction_type, InteractionType.MOUSE_CLICK)
        self.assertIsNone(event.control_type)

    def test_start_and_stop_are_clean_and_idempotent(self):
        source = FakeSource()
        collector = InteractionCollector(event_source=source)
        collector.start()
        collector.start()
        collector.stop()
        collector.stop()
        self.assertEqual((source.starts, source.stops), (1, 1))

    def test_session_association_does_not_create_session(self):
        collector = InteractionCollector(clock=lambda: NOW + timedelta(seconds=1))
        collector.running = True
        collector.record(InteractionType.KEYBOARD_ACTIVITY)
        memory = WorkingMemory(interaction_collector=collector)
        self.assertIsNone(memory.current_session)
        memory.register(completed_event())
        session = memory.finish()
        self.assertEqual(session.keyboard_actions, 1)
        self.assertEqual(session.interaction_count, 1)

    def test_window_switch_count(self):
        collector = InteractionCollector(clock=lambda: NOW)
        collector.running = True
        collector.record(InteractionType.SCROLL, window={"title": "A", "process_name": "a"})
        collector.record(InteractionType.SCROLL, window={"title": "B", "process_name": "b"})
        self.assertEqual(collector.counters.window_switches, 1)

    def test_interaction_failure_does_not_stop_work_session(self):
        class FailingCollector:
            def attach_to_session(self, session):
                raise OSError("synthetic failure")

        memory = WorkingMemory(interaction_collector=FailingCollector())
        memory.register(completed_event())
        session = memory.finish()
        self.assertIn(session, memory.sessions)
        self.assertEqual(memory.interaction_errors, ["OSError"])

    def test_aggregate_persistence_and_daily_report(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "telemetry.db"
            initialize(database)
            collector = InteractionCollector(clock=lambda: NOW + timedelta(seconds=1))
            collector.running = True
            collector.record(InteractionType.MOUSE_CLICK)
            collector.record(InteractionType.KEYBOARD_ACTIVITY)
            memory = WorkingMemory(
                interaction_collector=collector,
                interaction_sink=lambda session: save_session_interactions(session, database),
            )
            memory.register(completed_event())
            memory.finish()

            summary = daily_friction_summary(date(2026, 8, 7), database)
            self.assertEqual(summary.totals["interaction_count"], 2)
            self.assertEqual(summary.totals["mouse_clicks"], 1)
            rendered = []
            friction_report(date(2026, 8, 7), database, rendered.append)
            self.assertIn("Interacciones totales: 2", rendered)

            with closing(sqlite3.connect(database)) as conn:
                tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master")}
                columns = {
                    row[1]
                    for row in conn.execute("PRAGMA table_info(work_session_interactions)")
                }
            self.assertIn("work_session_interactions", tables)
            self.assertNotIn("window_title", columns)
            self.assertNotIn("control_type", columns)
            self.assertNotIn("text", columns)


if __name__ == "__main__":
    unittest.main()
