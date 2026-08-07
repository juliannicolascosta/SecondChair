import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

from src.models.event import Event
from src.models.work_session import WorkSession
from src.telemetry.interaction.collector import InteractionCollector
from src.telemetry.interaction.models import InteractionType
from src.workflows.repository import WorkflowTraceRepository
from src.workflows.reports import anonymous_trace, compare_traces, render_trace


START = datetime(2026, 8, 7, 10, 0, 0)


class Clock:
    def __init__(self):
        self.now = START

    def __call__(self):
        value = self.now
        self.now += timedelta(minutes=5)
        return value


def session(status="available", clicks=3):
    event = Event(
        application="Word", title="sensitive title", process_name="WINWORD.EXE",
        start_time=START, end_time=START + timedelta(seconds=60), duration=60,
    )
    result = WorkSession.from_event(1, event)
    result.interaction_count = clicks + 2
    result.mouse_clicks = clicks
    result.keyboard_actions = 2
    result.text_fields_used = 1
    result.buttons_used = 1
    result.window_switches = 2
    result.control_metrics_status = status
    return result


class WorkflowTraceTests(unittest.TestCase):
    def repository(self, directory, clock=None):
        return WorkflowTraceRepository(Path(directory) / "trace.db", clock or Clock())

    def test_manual_trace_persists_only_aggregate_session_facts(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.repository(directory)
            started = repository.start("Generar factura")
            self.assertTrue(repository.attach_session(session()))
            trace = repository.finish()
            self.assertEqual(trace.id, started.id)
            self.assertEqual(trace.status, "completed")
            self.assertEqual(trace.applications_used, ("Word",))
            self.assertEqual(trace.processes_used, ("WINWORD.EXE",))
            self.assertEqual(trace.mouse_clicks, 3)
            self.assertEqual(trace.text_fields_used, 1)
            with closing(sqlite3.connect(repository.database)) as conn:
                columns = {r[1] for r in conn.execute("PRAGMA table_info(workflow_trace_sessions)")}
                stored = str(conn.execute("SELECT * FROM workflow_trace_sessions").fetchone())
            self.assertNotIn("title", columns)
            self.assertNotIn("sensitive title", stored)

    def test_only_one_trace_can_run_and_cancel_is_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.repository(directory)
            repository.start("A")
            with self.assertRaises(RuntimeError):
                repository.start("B")
            self.assertEqual(repository.finish(cancelled=True).status, "cancelled")
            with self.assertRaises(RuntimeError):
                repository.finish()

    def test_unavailable_controls_are_not_reported_as_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.repository(directory)
            repository.start("A")
            repository.attach_session(session(status="unavailable"))
            trace = repository.finish()
            self.assertIsNone(trace.text_fields_used)
            output = []
            render_trace(trace, output.append)
            self.assertIn("Controles UI: no disponibles", output)

    def test_anonymous_export_removes_label_processes_and_session_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.repository(directory)
            repository.start("Sensitive label")
            repository.attach_session(session())
            exported = anonymous_trace(repository.finish())
            rendered = str(exported)
            self.assertNotIn("Sensitive label", rendered)
            self.assertNotIn("WINWORD", rendered)
            self.assertNotIn("session_ids", rendered)

    def test_comparison_is_descriptive_and_requires_matching_label(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.repository(directory)
            repository.start("Factura")
            repository.attach_session(session(clicks=4))
            first = repository.finish()
            repository.start("Factura")
            repository.attach_session(session(clicks=2))
            second = repository.finish()
            comparison = compare_traces(first, second)
            self.assertEqual(comparison["mouse_clicks"]["delta"], -2)
            repository.start("Otro")
            other = repository.finish()
            with self.assertRaises(ValueError):
                compare_traces(first, other)

    def test_completed_trace_uses_exact_interaction_time_slice(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = Clock()
            repository = self.repository(directory, clock)
            repository.start("Factura")  # 10:00 to 10:05
            collector = InteractionCollector()
            collector.running = True
            collector.record(InteractionType.MOUSE_CLICK, timestamp=START - timedelta(seconds=1))
            collector.record(
                InteractionType.KEYBOARD_ACTIVITY,
                timestamp=START + timedelta(minutes=1),
                window={"application": "Word", "process_name": "WINWORD.EXE", "title": "private"},
            )
            repository.finish()
            collector.record(InteractionType.SCROLL, timestamp=START + timedelta(minutes=6))

            self.assertEqual(repository.finalize_pending(collector), 1)
            trace = repository.list("Factura")[0]
            self.assertEqual(trace.interaction_count, 1)
            self.assertEqual(trace.keyboard_actions, 1)
            self.assertEqual(trace.mouse_clicks, 0)
            self.assertEqual(trace.scroll_actions, 0)
            self.assertEqual(trace.applications_used, ("Word",))
            self.assertEqual(trace.interaction_metrics_status, "exact")
            self.assertEqual(repository.finalize_pending(collector), 0)

    def test_session_aggregation_does_not_consume_events_needed_by_trace(self):
        collector = InteractionCollector()
        collector.running = True
        collector.record(InteractionType.KEYBOARD_ACTIVITY, timestamp=START + timedelta(seconds=1))
        collector.attach_to_session(session())
        result = collector.aggregate_between(START, START + timedelta(seconds=2))
        self.assertEqual(result["counters"].keyboard_actions, 1)


if __name__ == "__main__":
    unittest.main()
