import unittest
from datetime import datetime, timedelta

from src.memory.reports import sessions_summary
from src.memory.session_builder import SessionBuilder
from src.memory.working_memory import WorkingMemory
from src.models.event import Event


BASE_TIME = datetime(2026, 8, 5, 9, 0, 0)


def completed_event(
    application="Lex Doctor",
    start_offset=0,
    duration=60,
    client=None,
    case=None,
    project=None,
):
    start = BASE_TIME + timedelta(seconds=start_offset)
    return Event(
        application=application,
        title=f"{application} test window",
        start_time=start,
        end_time=start + timedelta(seconds=duration),
        duration=duration,
        client=client,
        case=case,
        project=project,
    )


class SessionBuilderTests(unittest.TestCase):

    def test_creates_session_and_counts_events(self):
        builder = SessionBuilder()

        closed = builder.add_event(
            completed_event(client="Client A", case="Case A")
        )
        builder.add_event(
            completed_event(
                application="Word",
                start_offset=60,
                duration=120,
            )
        )

        self.assertIsNone(closed)
        self.assertEqual(builder.current_session.id, 1)
        self.assertEqual(builder.current_session.events_count, 2)
        self.assertEqual(
            builder.current_session.applications_used,
            ["Lex Doctor", "Word"],
        )
        self.assertEqual(builder.current_session.primary_application, "Word")

    def test_closes_session_when_case_changes(self):
        builder = SessionBuilder()
        builder.add_event(completed_event(case="Case A"))

        closed = builder.add_event(
            completed_event(start_offset=60, case="Case B")
        )

        self.assertEqual(closed.case, "Case A")
        self.assertEqual(closed.events_count, 1)
        self.assertEqual(builder.current_session.case, "Case B")
        self.assertEqual(builder.current_session.id, 2)

    def test_closes_session_after_more_than_ten_minutes_inactivity(self):
        builder = SessionBuilder()
        builder.add_event(completed_event(duration=60, case="Case A"))

        closed = builder.add_event(
            completed_event(start_offset=661, case="Case A")
        )

        self.assertIsNotNone(closed)
        self.assertEqual(builder.current_session.id, 2)

    def test_exactly_ten_minutes_does_not_close_session(self):
        builder = SessionBuilder()
        builder.add_event(completed_event(duration=60, case="Case A"))

        closed = builder.add_event(
            completed_event(start_offset=660, case="Case A")
        )

        self.assertIsNone(closed)
        self.assertEqual(builder.current_session.events_count, 2)

    def test_duration_spans_first_start_to_last_end(self):
        builder = SessionBuilder()
        builder.add_event(completed_event(duration=60, case="Case A"))
        builder.add_event(
            completed_event(
                application="PDF",
                start_offset=120,
                duration=30,
            )
        )

        self.assertEqual(builder.current_session.duration, 150)
        self.assertEqual(builder.current_session.context_switches, 1)

    def test_completely_different_explicit_context_closes_session(self):
        builder = SessionBuilder()
        builder.add_event(completed_event(project="Project A"))

        closed = builder.add_event(
            completed_event(start_offset=60, client="Client B")
        )

        self.assertIsNotNone(closed)
        self.assertEqual(builder.current_session.client, "Client B")


class WorkingMemorySessionTests(unittest.TestCase):

    def test_finish_moves_current_session_to_daily_history_once(self):
        memory = WorkingMemory()
        memory.register(completed_event(case="Case A"))

        memory.finish()
        memory.finish()

        self.assertIsNone(memory.current_session)
        self.assertEqual(len(memory.sessions), 1)
        self.assertEqual(memory.sessions[0].events_count, 1)

    def test_sessions_report_contains_session_details(self):
        memory = WorkingMemory()
        memory.register(completed_event(case="Case A"))
        memory.finish()
        rendered = []

        sessions_summary(memory.sessions, rendered.append)

        text = "\n".join(rendered)
        self.assertIn("RESUMEN DE SESIONES", text)
        self.assertIn("Sesión 1", text)
        self.assertIn("Case A", text)
        self.assertIn("1m", text)
        self.assertIn("1 eventos", text)


if __name__ == "__main__":
    unittest.main()
