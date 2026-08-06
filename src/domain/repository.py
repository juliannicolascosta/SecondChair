"""Transactional SQLite persistence for Domain state, separate from events."""

import sqlite3
from contextlib import closing
from pathlib import Path

from src.domain.entities import Case, Client, Document, Organization, Person, Workspace
from src.domain.registry import normalize_identity
from src.domain.relations import (
    relate_case_document,
    relate_case_organization,
    relate_case_person,
    relate_client_case,
)
from src.domain.serializer import (
    candidate_from_row,
    candidate_to_record,
    datetime_to_text,
    text_to_datetime,
)
from src.domain.workspace import create_workspace
from src.storage.database import DATABASE


DOMAIN_SCHEMA_VERSION = 1

ENTITY_TABLES = {
    Client: "domain_clients",
    Case: "domain_cases",
    Organization: "domain_organizations",
    Person: "domain_persons",
    Document: "domain_documents",
}


class DomainRepository:
    def __init__(self, database=DATABASE):
        self.database = Path(database)

    def connect(self):
        self.database.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self):
        with closing(self.connect()) as conn, conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS domain_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            row = conn.execute(
                "SELECT value FROM domain_meta WHERE key='schema_version'"
            ).fetchone()
            version = int(row["value"]) if row else 0

            if version > DOMAIN_SCHEMA_VERSION:
                raise RuntimeError(
                    f"Unsupported domain schema version: {version}"
                )

            migrations = {0: self._migrate_0_to_1}
            while version < DOMAIN_SCHEMA_VERSION:
                migration = migrations.get(version)
                if migration is None:
                    raise RuntimeError(
                        f"Missing domain migration from version {version}"
                    )
                migration(conn)
                version += 1
                conn.execute(
                    """
                    INSERT INTO domain_meta(key, value)
                    VALUES('schema_version', ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value
                    """,
                    (str(version),),
                )

    @staticmethod
    def _migrate_0_to_1(conn):
        metrics = """
            id TEXT PRIMARY KEY,
            canonical_key TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            first_seen TEXT,
            last_seen TEXT,
            total_sessions INTEGER NOT NULL DEFAULT 0 CHECK(total_sessions >= 0),
            total_time INTEGER NOT NULL DEFAULT 0 CHECK(total_time >= 0)
        """
        for table in (
            "domain_clients",
            "domain_cases",
            "domain_organizations",
            "domain_persons",
        ):
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({metrics})")

        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS domain_documents (
                {metrics},
                path TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS domain_case_clients (
                case_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES domain_cases(id) ON DELETE CASCADE,
                FOREIGN KEY(client_id) REFERENCES domain_clients(id) ON DELETE RESTRICT
            )
        """)
        for table, target in (
            ("domain_case_organizations", "domain_organizations"),
            ("domain_case_persons", "domain_persons"),
            ("domain_case_documents", "domain_documents"),
        ):
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    case_id TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    PRIMARY KEY(case_id, entity_id),
                    FOREIGN KEY(case_id) REFERENCES domain_cases(id) ON DELETE CASCADE,
                    FOREIGN KEY(entity_id) REFERENCES {target}(id) ON DELETE CASCADE
                )
            """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS domain_learning_candidates (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                canonical_name TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1),
                metadata TEXT NOT NULL,
                requires_confirmation INTEGER NOT NULL CHECK(requires_confirmation IN (0,1)),
                reason TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending','accepted','rejected')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS domain_learned_sessions (
                session_id TEXT PRIMARY KEY,
                learned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                duration INTEGER NOT NULL DEFAULT 0 CHECK(duration >= 0)
            )
        """)

    def schema_version(self):
        with closing(self.connect()) as conn:
            row = conn.execute(
                "SELECT value FROM domain_meta WHERE key='schema_version'"
            ).fetchone()
            return int(row["value"]) if row else 0

    def save_workspace(self, workspace):
        with closing(self.connect()) as conn, conn:
            self._save_workspace(conn, workspace)

    def _save_workspace(self, conn, workspace):
        for collection in (
            workspace.clients,
            workspace.cases,
            workspace.organizations,
            workspace.persons,
            workspace.documents,
        ):
            for entity in collection:
                self._upsert_entity(conn, entity)

        for case in workspace.cases:
            if case.client is not None:
                conn.execute("""
                    INSERT INTO domain_case_clients(case_id, client_id)
                    VALUES(?, ?)
                    ON CONFLICT(case_id) DO UPDATE SET client_id=excluded.client_id
                """, (case.id, case.client.id))
            self._save_many_relation(
                conn, "domain_case_organizations", case.id, case.organizations
            )
            self._save_many_relation(
                conn, "domain_case_persons", case.id, case.persons
            )
            self._save_many_relation(
                conn, "domain_case_documents", case.id, case.documents
            )

    @staticmethod
    def _save_many_relation(conn, table, case_id, entities):
        for entity in entities:
            conn.execute(
                f"INSERT OR IGNORE INTO {table}(case_id, entity_id) VALUES(?, ?)",
                (case_id, entity.id),
            )

    @staticmethod
    def _entity_record(entity):
        return (
            entity.id,
            normalize_identity(entity.name),
            entity.name,
            datetime_to_text(entity.created_at),
            datetime_to_text(entity.updated_at),
            datetime_to_text(entity.first_seen),
            datetime_to_text(entity.last_seen),
            entity.total_sessions,
            entity.total_time,
        )

    def _upsert_entity(self, conn, entity):
        table = ENTITY_TABLES[type(entity)]
        columns = """
            id, canonical_key, name, created_at, updated_at,
            first_seen, last_seen, total_sessions, total_time
        """
        placeholders = "?, ?, ?, ?, ?, ?, ?, ?, ?"
        values = self._entity_record(entity)
        update = """
            canonical_key=excluded.canonical_key,
            name=excluded.name,
            updated_at=excluded.updated_at,
            first_seen=excluded.first_seen,
            last_seen=excluded.last_seen,
            total_sessions=excluded.total_sessions,
            total_time=excluded.total_time
        """
        if isinstance(entity, Document):
            columns += ", path"
            placeholders += ", ?"
            values += (entity.path,)
            update += ", path=excluded.path"
        conn.execute(
            f"""
            INSERT INTO {table}({columns}) VALUES({placeholders})
            ON CONFLICT(id) DO UPDATE SET {update}
            """,
            values,
        )

    def load_workspace(self):
        workspace = create_workspace()
        with closing(self.connect()) as conn:
            clients = self._load_entities(conn, "domain_clients", Client)
            cases = self._load_entities(conn, "domain_cases", Case)
            organizations = self._load_entities(
                conn, "domain_organizations", Organization
            )
            persons = self._load_entities(conn, "domain_persons", Person)
            documents = self._load_entities(conn, "domain_documents", Document)

            workspace.clients.extend(clients.values())
            workspace.cases.extend(cases.values())
            workspace.organizations.extend(organizations.values())
            workspace.persons.extend(persons.values())
            workspace.documents.extend(documents.values())

            for row in conn.execute("SELECT * FROM domain_case_clients"):
                relate_client_case(clients[row["client_id"]], cases[row["case_id"]])
            self._load_many_relations(
                conn, "domain_case_organizations", cases, organizations,
                relate_case_organization,
            )
            self._load_many_relations(
                conn, "domain_case_persons", cases, persons, relate_case_person,
            )
            self._load_many_relations(
                conn, "domain_case_documents", cases, documents,
                relate_case_document,
            )

        workspace.statistics.update({
            "clients": len(workspace.clients),
            "cases": len(workspace.cases),
            "organizations": len(workspace.organizations),
            "persons": len(workspace.persons),
            "documents": len(workspace.documents),
        })
        return workspace

    @staticmethod
    def _load_entities(conn, table, entity_type):
        entities = {}
        for row in conn.execute(f"SELECT * FROM {table}"):
            kwargs = {
                "name": row["name"],
                "id": row["id"],
                "created_at": text_to_datetime(row["created_at"]),
                "updated_at": text_to_datetime(row["updated_at"]),
                "first_seen": text_to_datetime(row["first_seen"]),
                "last_seen": text_to_datetime(row["last_seen"]),
                "total_sessions": row["total_sessions"],
                "total_time": row["total_time"],
            }
            if entity_type is Document:
                kwargs["path"] = row["path"]
            entity = entity_type(**kwargs)
            entities[entity.id] = entity
        return entities

    @staticmethod
    def _load_many_relations(conn, table, cases, entities, relation):
        for row in conn.execute(f"SELECT * FROM {table}"):
            relation(cases[row["case_id"]], entities[row["entity_id"]])

    def save_candidate(self, candidate):
        with closing(self.connect()) as conn, conn:
            self._save_candidate(conn, candidate)

    @staticmethod
    def _save_candidate(conn, candidate):
        conn.execute("""
            INSERT INTO domain_learning_candidates(
                id, entity_type, canonical_name, source, confidence, metadata,
                requires_confirmation, reason, status, created_at, updated_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                entity_type=excluded.entity_type,
                canonical_name=excluded.canonical_name,
                source=excluded.source,
                confidence=excluded.confidence,
                metadata=excluded.metadata,
                requires_confirmation=excluded.requires_confirmation,
                reason=excluded.reason,
                status=excluded.status,
                updated_at=excluded.updated_at
        """, candidate_to_record(candidate))

    def load_candidates(self, status=None):
        query = "SELECT * FROM domain_learning_candidates"
        params = ()
        if status is not None:
            query += " WHERE status=?"
            params = (status,)
        query += " ORDER BY created_at, id"
        with closing(self.connect()) as conn:
            return [candidate_from_row(row) for row in conn.execute(query, params)]

    def save_learning_result(self, result, workspace, session):
        with closing(self.connect()) as conn, conn:
            self._save_workspace(conn, workspace)
            for candidate in (
                result.pending_candidates + result.accepted_candidates
            ):
                self._save_candidate(conn, candidate)
            conn.execute("""
                INSERT OR IGNORE INTO domain_learned_sessions(
                    session_id, duration
                ) VALUES(?, ?)
            """, (session.learning_id, session.duration))

    def mark_session_learned(self, session_id, duration=0):
        with closing(self.connect()) as conn, conn:
            conn.execute("""
                INSERT OR IGNORE INTO domain_learned_sessions(session_id, duration)
                VALUES(?, ?)
            """, (str(session_id), duration))

    def was_session_learned(self, session_id):
        with closing(self.connect()) as conn:
            row = conn.execute(
                "SELECT 1 FROM domain_learned_sessions WHERE session_id=?",
                (str(session_id),),
            ).fetchone()
            return row is not None

    def load_learned_session_ids(self):
        with closing(self.connect()) as conn:
            return {
                row["session_id"]
                for row in conn.execute("SELECT session_id FROM domain_learned_sessions")
            }
