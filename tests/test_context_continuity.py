import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from src.analytics.queries import events_for_date
from src.context.continuity import ContextContinuity, classify_communication
from src.domain.learner import DomainLearner
from src.models.event import Event
from src.models.work_session import WorkSession
from src.storage.database import initialize, save_event_model


NOW = datetime(2026, 8, 7, 16, 0, 0)


class MutableClock:
    def __init__(self, value=NOW):
        self.value = value

    def __call__(self):
        return self.value


class ContextContinuityTests(unittest.TestCase):
    def test_recent_lex_case_is_associated_without_confirmation(self):
        clock = MutableClock()
        continuity = ContextContinuity(clock=clock)
        continuity.apply(Event(
            application="Lex Doctor", title="Procesos",
            client="Cliente A", case="Cliente A C/ Empresa S.A.",
        ))
        clock.value += timedelta(seconds=20)

        communication = continuity.apply(Event(
            application="Outlook", title="Nuevo mensaje",
        ))

        self.assertEqual(communication.case, "Cliente A C/ Empresa S.A.")
        self.assertEqual(communication.activity_type, "email_compose")
        self.assertEqual(communication.context_source, "recent_lex_context")
        self.assertEqual(communication.context_confidence, 0.60)
        self.assertFalse(communication.context_confirmed)

    def test_context_expires_without_interrupting_or_guessing(self):
        clock = MutableClock()
        continuity = ContextContinuity(timeout_seconds=300, clock=clock)
        continuity.apply(Event(
            application="Lex Doctor", title="Procesos", case="Case A",
        ))
        clock.value += timedelta(seconds=301)

        communication = continuity.apply(Event(
            application="WhatsApp Business", title="WhatsApp Business",
        ))

        self.assertEqual(communication.activity_type, "messaging_window")
        self.assertIsNone(communication.case)
        self.assertIsNone(communication.context_source)

    def test_outlook_classification_does_not_claim_a_send(self):
        self.assertEqual(classify_communication("Outlook", "RE: Consulta"), "email_reply")
        self.assertEqual(classify_communication("Outlook", "Bandeja de entrada"), "email_window")
        self.assertNotEqual(classify_communication("Outlook", "Nuevo mensaje"), "email_sent")

    def test_inferred_only_context_is_not_auto_promoted(self):
        event = Event(
            application="Outlook", title="Nuevo mensaje",
            start_time=NOW, end_time=NOW + timedelta(seconds=30), duration=30,
            client="Cliente A", case="Cliente A C/ Empresa S.A.",
            activity_type="email_compose", context_source="recent_lex_context",
            context_confidence=0.60, context_confirmed=False,
        )
        result = DomainLearner().learn_from_session(WorkSession.from_event(1, event))
        self.assertEqual(result.created_cases, [])
        self.assertEqual(result.created_clients, [])
        self.assertGreaterEqual(len(result.pending_candidates), 2)

    def test_provenance_round_trips_through_sqlite(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "continuity.db"
            initialize(database)
            event = Event(
                application="Outlook", title="Nuevo mensaje",
                start_time=NOW, end_time=NOW + timedelta(seconds=30), duration=30,
                client="Cliente A", case="Case A", activity_type="email_compose",
                context_source="recent_lex_context", context_confidence=0.60,
                context_confirmed=False,
            )
            save_event_model(event, database)
            row = events_for_date(NOW.date(), database)[0]
        self.assertEqual(row["activity_type"], "email_compose")
        self.assertEqual(row["context_source"], "recent_lex_context")
        self.assertEqual(row["context_confidence"], 0.60)
        self.assertEqual(row["context_confirmed"], 0)


if __name__ == "__main__":
    unittest.main()
