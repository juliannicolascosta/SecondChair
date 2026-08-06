"""Translate observed context into detached or already-known domain entities."""

from dataclasses import dataclass

from src.domain.entities import Case, Client, Document, Organization


@dataclass(frozen=True)
class DomainResolution:
    client: Client | None = None
    case: Case | None = None
    organization: Organization | None = None
    document: Document | None = None

    @property
    def detected(self):
        return {
            name: entity
            for name, entity in (
                ("client", self.client),
                ("case", self.case),
                ("organization", self.organization),
                ("document", self.document),
            )
            if entity is not None
        }


class DomainResolver:
    def __init__(self, registry=None):
        self.registry = registry

    def resolve(self, context):
        context = context or {}
        client_name = context.get("cliente") or context.get("client")
        case_name = context.get("expediente") or context.get("case")
        organization_name = context.get("empresa") or context.get("organization")
        document_name = context.get("documento") or context.get("document")

        client = self._resolve(client_name, "find_client", Client)
        case = self._resolve(case_name, "find_case", Case)
        organization = self._resolve(
            organization_name,
            "find_organization",
            Organization,
        )
        document = self._resolve(document_name, "find_document", Document)

        return DomainResolution(
            client=client,
            case=case,
            organization=organization,
            document=document,
        )

    def _resolve(self, name, finder_name, entity_type):
        if not isinstance(name, str) or not name.strip():
            return None

        if self.registry is not None:
            existing = getattr(self.registry, finder_name)(name)
            if existing is not None:
                return existing

        return entity_type(name=name.strip())
