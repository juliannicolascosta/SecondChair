"""Conservative deterministic promotion of WorkSession context to Domain."""

import re

from src.domain.candidates import LearningCandidate, LearningResult
from src.domain.registry import DomainRegistry
from src.domain.relations import (
    relate_case_document,
    relate_case_organization,
    relate_client_case,
)
from src.domain.resolver import DomainResolver
from src.domain.workspace import create_workspace
from src.domain.entities import utc_now


AUTO_PROMOTION_THRESHOLD = 0.90
HIGH_CONFIDENCE = 0.95
AMBIGUOUS_CONFIDENCE = 0.60

CASE_CAPTION_PATTERN = re.compile(
    r"^\s*(?P<claimant>.+?)\s+C/\s+(?P<counterparty>.+?)\s*$",
    re.IGNORECASE,
)

ORGANIZATION_PATTERN = re.compile(
    r"(?:\bS\.?A\.?\b|\bS\.?R\.?L\.?\b|\bA\.?R\.?T\.?\b|"
    r"\bART\b|\bmutual\b|\bbanco\b|\baseguradora\b|\borganismo\b)",
    re.IGNORECASE,
)


class DomainLearner:
    def __init__(self, workspace=None, registry=None, resolver=None):
        self.workspace = workspace or create_workspace()
        self.registry = registry or DomainRegistry(self.workspace)

        if self.registry.workspace is not self.workspace:
            raise ValueError("DomainLearner dependencies must share one Workspace")

        self.resolver = resolver or DomainResolver(self.registry)
        self.learned_session_ids = set()

    def learn_from_session(self, session):
        result = LearningResult()

        session_id = session.learning_id
        if session_id in self.learned_session_ids:
            result.warnings.append("WorkSession already learned")
            return result

        if not session.events or any(
            event.start_time is None or event.end_time is None
            for event in session.events
        ):
            result.warnings.append("WorkSession contains open or incomplete events")
            return result

        self.learned_session_ids.add(session_id)

        lex_case_event = next((
            event
            for event in session.events
            if event.application == "Lex Doctor" and event.case
        ), None)
        case_name = session.case or (
            lex_case_event.case if lex_case_event is not None else None
        )
        caption = CASE_CAPTION_PATTERN.match(case_name or "")

        document_names = list(dict.fromkeys(
            event.document.strip()
            for event in session.events
            if isinstance(event.document, str) and event.document.strip()
        ))

        observed_context = {
            "client": session.client,
            "case": case_name,
            "document": document_names[0] if document_names else None,
        }
        resolution = self.resolver.resolve(observed_context)

        resolved_case_name = (
            resolution.case.name if resolution.case is not None else case_name
        )
        resolved_client_name = (
            resolution.client.name
            if resolution.client is not None
            else session.client
        )
        case = self._learn_case(
            resolved_case_name,
            caption,
            lex_case_event,
            result,
        )
        client = self._learn_client(
            resolved_client_name,
            caption,
            lex_case_event,
            result,
        )

        if client is not None and case is not None:
            relate_client_case(client, case)
            self._mark_updated(result, client, case)

        organization = self._learn_counterparty(caption, result)
        if organization is not None and case is not None:
            relate_case_organization(case, organization)
            self._mark_updated(result, case, organization)

        for document_name in document_names:
            document = self._promote_document(document_name, result)
            if case is not None:
                relate_case_document(case, document)
                self._mark_updated(result, case, document)

        self._update_metrics(result, session)

        return result

    @staticmethod
    def _mark_updated(result, *entities):
        known_ids = {entity.id for entity in result.updated_entities}
        for entity in entities:
            if entity.id not in known_ids:
                result.updated_entities.append(entity)
                known_ids.add(entity.id)

    @staticmethod
    def _update_metrics(result, session):
        entities = []
        for collection in (
            result.created_clients,
            result.created_cases,
            result.created_organizations,
            result.created_documents,
            result.updated_entities,
        ):
            for entity in collection:
                if all(existing.id != entity.id for existing in entities):
                    entities.append(entity)

        now = utc_now()
        for entity in entities:
            entity.first_seen = entity.first_seen or session.start_time
            entity.last_seen = max(
                filter(None, (entity.last_seen, session.end_time))
            )
            entity.updated_at = now
            entity.total_sessions += 1
            entity.total_time += session.duration

    def _learn_case(self, name, caption, lex_event, result):
        if not name:
            return None

        source = "lex_doctor_title" if lex_event is not None else "work_session_context"
        confidence = HIGH_CONFIDENCE if caption else AMBIGUOUS_CONFIDENCE
        candidate = LearningCandidate(
            entity_type="case",
            canonical_name=name.strip(),
            source=source,
            confidence=confidence,
            metadata={"complete_caption": bool(caption)},
            requires_confirmation=confidence < AUTO_PROMOTION_THRESHOLD,
            reason=(
                "Complete case caption recognized"
                if caption
                else "Case context does not contain a complete caption"
            ),
            status=(
                "pending"
                if confidence < AUTO_PROMOTION_THRESHOLD
                else "accepted"
            ),
        )

        if candidate.requires_confirmation:
            result.pending_candidates.append(candidate)
            return None

        existing = self.registry.find_case(candidate.canonical_name)
        case = self.registry.obtener_o_crear_expediente(candidate.canonical_name)
        if existing is None:
            result.created_cases.append(case)
        result.accepted_candidates.append(self._with_entity_id(candidate, case))
        return case

    def _learn_client(self, observed_name, caption, lex_event, result):
        inferred_name = caption.group("claimant").strip() if caption else observed_name
        if not inferred_name:
            return None

        deterministic = caption is not None and lex_event is not None
        confidence = HIGH_CONFIDENCE if deterministic else AMBIGUOUS_CONFIDENCE
        candidate = LearningCandidate(
            entity_type="client",
            canonical_name=inferred_name,
            source="lex_doctor_title" if lex_event is not None else "parser",
            confidence=confidence,
            metadata={"complete_caption": bool(caption)},
            requires_confirmation=not deterministic,
            reason=(
                "Claimant extracted from a complete Lex Doctor caption"
                if deterministic
                else "Client context lacks deterministic Lex Doctor evidence"
            ),
            status="accepted" if deterministic else "pending",
        )

        if candidate.requires_confirmation:
            result.pending_candidates.append(candidate)
            return None

        existing = self.registry.find_client(candidate.canonical_name)
        client = self.registry.obtener_o_crear_cliente(candidate.canonical_name)
        if existing is None:
            result.created_clients.append(client)
        result.accepted_candidates.append(self._with_entity_id(candidate, client))
        return client

    def _learn_counterparty(self, caption, result):
        if caption is None:
            return None

        name = caption.group("counterparty").strip()
        organization_signal = bool(ORGANIZATION_PATTERN.search(name))
        confidence = HIGH_CONFIDENCE if organization_signal else AMBIGUOUS_CONFIDENCE
        candidate = LearningCandidate(
            entity_type="organization",
            canonical_name=name,
            source="lex_doctor_title",
            confidence=confidence,
            metadata={"organizational_signal": organization_signal},
            requires_confirmation=not organization_signal,
            reason=(
                "Explicit organizational marker recognized"
                if organization_signal
                else "Counterparty may be either a person or an organization"
            ),
            status="accepted" if organization_signal else "pending",
        )

        if candidate.requires_confirmation:
            result.pending_candidates.append(candidate)
            return None

        existing = self.registry.find_organization(candidate.canonical_name)
        organization = self.registry.obtener_o_crear_empresa(candidate.canonical_name)
        if existing is None:
            result.created_organizations.append(organization)
        result.accepted_candidates.append(
            self._with_entity_id(candidate, organization)
        )
        return organization

    def _promote_document(self, name, result):
        candidate = LearningCandidate(
            entity_type="document",
            canonical_name=name,
            source="document_title",
            confidence=HIGH_CONFIDENCE,
            metadata={},
            requires_confirmation=False,
            reason="Identifiable document name observed in a completed event",
            status="accepted",
        )
        existing = self.registry.find_document(candidate.canonical_name)
        document = self.registry.obtener_o_crear_documento(candidate.canonical_name)
        if existing is None:
            result.created_documents.append(document)
        result.accepted_candidates.append(self._with_entity_id(candidate, document))
        return document

    @staticmethod
    def _with_entity_id(candidate, entity):
        from dataclasses import replace

        metadata = dict(candidate.metadata)
        metadata["entity_id"] = entity.id
        return replace(candidate, metadata=metadata)


def learning_day_summary(results, output=print):
    output("")
    output("=" * 40)
    output("APRENDIZAJE DEL DÍA")
    output("=" * 40)
    output("")
    output(f"Nuevos clientes: {sum(len(r.created_clients) for r in results)}")
    output(f"Nuevos expedientes: {sum(len(r.created_cases) for r in results)}")
    output(f"Nuevas organizaciones: {sum(len(r.created_organizations) for r in results)}")
    output(f"Nuevos documentos: {sum(len(r.created_documents) for r in results)}")
    output(f"Candidatos pendientes: {sum(len(r.pending_candidates) for r in results)}")
    output(f"Advertencias: {sum(len(r.warnings) for r in results)}")
