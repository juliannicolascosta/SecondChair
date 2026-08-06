import socket
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.domain.candidates import LearningCandidate, LearningResult
from src.domain.learner import DomainLearner, HIGH_CONFIDENCE
from src.memory.working_memory import WorkingMemory
from src.models.event import Event
from src.models.work_session import WorkSession


BASE_TIME = datetime(2026, 8, 5, 9, 0, 0)


def event(
    application="Lex Doctor",
    offset=0,
    duration=60,
    case=None,
    client=None,
    document=None,
):
    start = BASE_TIME + timedelta(seconds=offset)
    return Event(
        application=application,
        title=f"{application} synthetic window",
        start_time=start,
        end_time=start + timedelta(seconds=duration),
        duration=duration,
        case=case,
        client=client,
        document=document,
    )


def clear_session(session_id=1, counterparty="Bank S.A.", with_document=False):
    caption = f"Client Alpha C/ {counterparty}"
    first = event(case=caption, client="Client Alpha")
    session = WorkSession.from_event(session_id, first)

    if with_document:
        session.add_event(event(
            application="PDF",
            offset=60,
            duration=30,
            document="Synthetic filing.pdf",
        ))

    return session


class LearningCandidateTests(unittest.TestCase):

    def test_candidate_validates_confidence_and_type(self):
        candidate = LearningCandidate(
            entity_type="case",
            canonical_name="Case Alpha",
            source="parser",
            confidence=0.75,
            requires_confirmation=True,
            reason="Synthetic ambiguous case",
        )
        self.assertEqual(candidate.confidence, 0.75)

        with self.assertRaises(ValueError):
            LearningCandidate("case", "Case", "parser", 1.1)
        with self.assertRaises(ValueError):
            LearningCandidate("person", "Person", "parser", 0.5)


class DomainLearnerTests(unittest.TestCase):

    def test_learns_unambiguous_case_and_client(self):
        learner = DomainLearner()

        result = learner.learn_from_session(clear_session())

        self.assertEqual(len(result.created_cases), 1)
        self.assertEqual(len(result.created_clients), 1)
        case = result.created_cases[0]
        client = result.created_clients[0]
        self.assertIs(case.client, client)
        self.assertEqual(client.cases, [case])

    def test_learns_organization_and_bidirectional_relation(self):
        learner = DomainLearner()

        result = learner.learn_from_session(clear_session())

        organization = result.created_organizations[0]
        case = result.created_cases[0]
        self.assertEqual(case.organizations, [organization])
        self.assertEqual(organization.cases, [case])

    def test_learns_document_and_relates_it_only_to_clear_case(self):
        learner = DomainLearner()

        result = learner.learn_from_session(clear_session(with_document=True))

        document = result.created_documents[0]
        case = result.created_cases[0]
        self.assertEqual(case.documents, [document])
        self.assertEqual(document.cases, [case])
        self.assertEqual(
            len({entity.id for entity in result.updated_entities}),
            len(result.updated_entities),
        )

    def test_ambiguous_counterparty_remains_pending(self):
        learner = DomainLearner()

        result = learner.learn_from_session(
            clear_session(counterparty="Natural Person")
        )

        self.assertEqual(result.created_organizations, [])
        candidate = next(
            item for item in result.pending_candidates
            if item.entity_type == "organization"
        )
        self.assertEqual(candidate.source, "lex_doctor_title")
        self.assertLess(candidate.confidence, HIGH_CONFIDENCE)
        self.assertTrue(candidate.requires_confirmation)
        self.assertTrue(candidate.reason)

    def test_same_session_is_not_learned_twice(self):
        learner = DomainLearner()
        session = clear_session()

        first = learner.learn_from_session(session)
        second = learner.learn_from_session(session)

        self.assertEqual(first.created_count, 3)
        self.assertEqual(second.created_count, 0)
        self.assertEqual(len(second.warnings), 1)
        self.assertEqual(len(learner.workspace.cases), 1)

    def test_different_sessions_reuse_same_domain_entities(self):
        learner = DomainLearner()

        learner.learn_from_session(clear_session(session_id=1))
        result = learner.learn_from_session(clear_session(session_id=2))

        self.assertEqual(result.created_count, 0)
        self.assertEqual(len(learner.workspace.clients), 1)
        self.assertEqual(len(learner.workspace.cases), 1)
        self.assertEqual(len(learner.workspace.organizations), 1)

    def test_learning_result_exposes_every_audit_collection(self):
        result = LearningResult()

        self.assertEqual(result.created_clients, [])
        self.assertEqual(result.created_cases, [])
        self.assertEqual(result.created_organizations, [])
        self.assertEqual(result.created_documents, [])
        self.assertEqual(result.updated_entities, [])
        self.assertEqual(result.pending_candidates, [])
        self.assertEqual(result.accepted_candidates, [])
        self.assertEqual(result.warnings, [])

    def test_learning_is_fully_offline(self):
        learner = DomainLearner()

        with patch.object(socket, "socket", side_effect=AssertionError("network used")):
            result = learner.learn_from_session(clear_session())

        self.assertEqual(len(result.created_cases), 1)


class WorkingMemoryLearningTests(unittest.TestCase):

    def test_workspace_updates_when_session_closes(self):
        memory = WorkingMemory()
        memory.register(event(
            case="Client Alpha C/ Bank S.A.",
            client="Client Alpha",
        ))

        memory.finish()

        self.assertEqual(len(memory.sessions), 1)
        self.assertEqual(len(memory.learning_results), 1)
        self.assertEqual(len(memory.workspace.cases), 1)
        self.assertEqual(len(memory.workspace.clients), 1)


if __name__ == "__main__":
    unittest.main()
