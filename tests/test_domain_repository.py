import socket
import sqlite3
import tempfile
import unittest
from contextlib import closing
from contextlib import redirect_stdout
from contextlib import redirect_stderr
from io import StringIO
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from src.domain.candidates import LearningCandidate, LearningResult
from src.domain.learner import DomainLearner
from src.domain.registry import DomainRegistry
from src.domain.relations import (
    relate_case_document,
    relate_case_organization,
    relate_case_person,
)
from src.domain.repository import DOMAIN_SCHEMA_VERSION, DomainRepository
from src.domain.resolver import DomainResolver
from src.domain.workspace import create_workspace
from src.memory.working_memory import WorkingMemory
from src.models.event import Event


BASE_TIME = datetime(2026, 8, 5, 9, 0, 0)


def completed_lex_event():
    return Event(
        application="Lex Doctor",
        title="Synthetic Lex Doctor window",
        start_time=BASE_TIME,
        end_time=BASE_TIME + timedelta(seconds=90),
        duration=90,
        client="Synthetic Client",
        case="Synthetic Client C/ Synthetic Bank S.A.",
    )


class DomainRepositoryTests(unittest.TestCase):

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary.name) / "secondchair.db"
        self.repository = DomainRepository(self.database)
        self.repository.initialize()

    def tearDown(self):
        self.temporary.cleanup()

    def test_creates_versioned_schema_with_foreign_keys(self):
        self.assertEqual(self.repository.schema_version(), DOMAIN_SCHEMA_VERSION)
        with closing(self.repository.connect()) as conn:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            foreign_keys = conn.execute("PRAGMA foreign_keys").fetchone()[0]

        self.assertTrue({
            "domain_meta",
            "domain_clients",
            "domain_cases",
            "domain_organizations",
            "domain_persons",
            "domain_documents",
            "domain_case_clients",
            "domain_case_organizations",
            "domain_case_persons",
            "domain_case_documents",
            "domain_learning_candidates",
            "domain_learned_sessions",
        }.issubset(tables))
        self.assertEqual(foreign_keys, 1)

    def test_round_trip_preserves_entities_uuid_and_relations(self):
        registry = DomainRegistry()
        client = registry.obtener_o_crear_cliente("Synthetic Client")
        case = registry.obtener_o_crear_expediente("Synthetic Case", client)
        organization = registry.obtener_o_crear_empresa("Synthetic Organization S.A.")
        person = registry.obtener_o_crear_persona("Synthetic Person")
        document = registry.obtener_o_crear_documento(
            "Synthetic Document.pdf", "synthetic/path.pdf"
        )
        relate_case_organization(case, organization)
        relate_case_person(case, person)
        relate_case_document(case, document)

        self.repository.save_workspace(registry.workspace)
        loaded = self.repository.load_workspace()

        self.assertEqual(loaded.clients[0].id, client.id)
        self.assertEqual(loaded.cases[0].id, case.id)
        self.assertEqual(loaded.organizations[0].id, organization.id)
        self.assertEqual(loaded.persons[0].id, person.id)
        self.assertEqual(loaded.documents[0].id, document.id)
        loaded_case = loaded.cases[0]
        self.assertIs(loaded_case.client, loaded.clients[0])
        self.assertEqual(loaded_case.organizations, loaded.organizations)
        self.assertEqual(loaded_case.persons, loaded.persons)
        self.assertEqual(loaded_case.documents, loaded.documents)
        self.assertEqual(loaded.documents[0].cases, [loaded_case])

    def test_registry_reuses_loaded_entity(self):
        registry = DomainRegistry()
        original = registry.obtener_o_crear_cliente("Synthetic Client")
        self.repository.save_workspace(registry.workspace)

        restarted = DomainRegistry(self.repository.load_workspace())
        reused = restarted.obtener_o_crear_cliente(" synthetic   CLIENT ")

        self.assertEqual(reused.id, original.id)
        self.assertEqual(len(restarted.workspace.clients), 1)

    def test_persists_all_candidate_statuses(self):
        for status in ("pending", "accepted", "rejected"):
            self.repository.save_candidate(LearningCandidate(
                entity_type="case",
                canonical_name=f"Synthetic {status}",
                source="parser",
                confidence=0.5,
                reason="Synthetic fixture",
                status=status,
            ))

        self.assertEqual(
            {candidate.status for candidate in self.repository.load_candidates()},
            {"pending", "accepted", "rejected"},
        )
        self.assertEqual(len(self.repository.load_candidates("pending")), 1)

    def test_transaction_rolls_back_on_canonical_collision(self):
        from src.domain.entities import Client, Workspace

        invalid = Workspace(clients=[
            Client("Synthetic Duplicate"),
            Client(" synthetic  duplicate "),
        ])

        with self.assertRaises(sqlite3.IntegrityError):
            self.repository.save_workspace(invalid)

        self.assertEqual(self.repository.load_workspace().clients, [])

    def test_migration_preserves_existing_tables_and_rows(self):
        other_database = Path(self.temporary.name) / "legacy.db"
        with closing(sqlite3.connect(other_database)) as conn, conn:
            conn.execute("CREATE TABLE legacy_domain_sentinel(value TEXT)")
            conn.execute("INSERT INTO legacy_domain_sentinel VALUES('preserve')")
            conn.execute("CREATE TABLE events(id INTEGER PRIMARY KEY, title TEXT)")
            conn.execute("INSERT INTO events(title) VALUES('synthetic')")

        repository = DomainRepository(other_database)
        repository.initialize()

        with closing(repository.connect()) as conn:
            sentinel = conn.execute(
                "SELECT value FROM legacy_domain_sentinel"
            ).fetchone()[0]
            event_count = conn.execute("SELECT count(*) FROM events").fetchone()[0]
        self.assertEqual(sentinel, "preserve")
        self.assertEqual(event_count, 1)

    def test_repository_operates_offline(self):
        with patch.object(socket, "socket", side_effect=AssertionError("network used")):
            self.repository.save_workspace(create_workspace())
            self.repository.load_workspace()


class DomainRestartTests(unittest.TestCase):

    def test_distinct_sessions_accumulate_count_and_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = DomainRepository(Path(directory) / "secondchair.db")
            repository.initialize()
            memory = WorkingMemory(
                domain_learner=DomainLearner(),
                domain_repository=repository,
            )
            first = completed_lex_event()
            second = completed_lex_event()
            second.start_time += timedelta(hours=1)
            second.end_time += timedelta(hours=1)

            memory.register(first)
            memory.register(second)
            memory.finish()

            loaded_case = repository.load_workspace().cases[0]
            self.assertEqual(loaded_case.total_sessions, 2)
            self.assertEqual(loaded_case.total_time, 180)

    def test_persistence_failure_keeps_result_for_retry(self):
        class FailingRepository:
            def save_learning_result(self, result, workspace, session):
                raise sqlite3.OperationalError("synthetic failure")

        memory = WorkingMemory(
            domain_learner=DomainLearner(),
            domain_repository=FailingRepository(),
        )
        memory.register(completed_lex_event())

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            memory.finish()

        self.assertEqual(len(memory.learning_results), 1)
        self.assertEqual(len(memory.pending_persistence), 1)
        self.assertTrue(memory.learning_results[0].warnings)

    def test_restart_preserves_identity_relations_and_prevents_relearning(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = DomainRepository(Path(directory) / "secondchair.db")
            repository.initialize()

            first_learner = DomainLearner()
            first_memory = WorkingMemory(
                domain_learner=first_learner,
                domain_repository=repository,
            )
            first_memory.register(completed_lex_event())
            first_memory.finish()

            first_workspace = repository.load_workspace()
            first_case_id = first_workspace.cases[0].id
            first_client_id = first_workspace.clients[0].id
            self.assertEqual(first_workspace.cases[0].total_sessions, 1)
            self.assertEqual(first_workspace.cases[0].total_time, 90)
            accepted = repository.load_candidates("accepted")
            self.assertTrue(accepted)
            self.assertTrue(all(
                candidate.metadata.get("entity_id")
                for candidate in accepted
            ))

            loaded_workspace = repository.load_workspace()
            registry = DomainRegistry(loaded_workspace)
            second_learner = DomainLearner(
                loaded_workspace,
                registry,
                DomainResolver(registry),
            )
            second_learner.learned_session_ids.update(
                repository.load_learned_session_ids()
            )
            second_memory = WorkingMemory(
                domain_learner=second_learner,
                domain_repository=repository,
            )
            second_memory.register(completed_lex_event())
            second_memory.finish()

            final_workspace = repository.load_workspace()
            self.assertEqual(final_workspace.cases[0].id, first_case_id)
            self.assertEqual(final_workspace.clients[0].id, first_client_id)
            self.assertIs(
                final_workspace.cases[0].client,
                final_workspace.clients[0],
            )
            self.assertEqual(final_workspace.cases[0].total_sessions, 1)
            self.assertEqual(final_workspace.cases[0].total_time, 90)
            self.assertTrue(second_memory.learning_results[0].warnings)

    def test_pending_candidate_survives_restart_without_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = DomainRepository(Path(directory) / "secondchair.db")
            repository.initialize()
            learner = DomainLearner()
            memory = WorkingMemory( domain_learner=learner, domain_repository=repository)
            ambiguous = completed_lex_event()
            ambiguous.case = "Synthetic Client C/ Synthetic Natural Person"
            memory.register(ambiguous)
            memory.finish()

            candidates = repository.load_candidates("pending")
            workspace = repository.load_workspace()
            self.assertTrue(candidates)
            self.assertEqual(workspace.organizations, [])


if __name__ == "__main__":
    unittest.main()
