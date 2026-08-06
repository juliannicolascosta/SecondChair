"""Auditable inputs and outputs of deterministic domain learning."""

from dataclasses import dataclass, field
from typing import Any

from src.domain.entities import Case, Client, Document, Organization


SUPPORTED_ENTITY_TYPES = frozenset({
    "client",
    "case",
    "organization",
    "document",
})


@dataclass(frozen=True)
class LearningCandidate:
    entity_type: str
    canonical_name: str
    source: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = True
    reason: str = ""

    def __post_init__(self):
        if self.entity_type not in SUPPORTED_ENTITY_TYPES:
            raise ValueError(f"Unsupported entity type: {self.entity_type}")
        if not self.canonical_name.strip():
            raise ValueError("Candidate canonical_name cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Candidate confidence must be between 0 and 1")


@dataclass
class LearningResult:
    created_clients: list[Client] = field(default_factory=list)
    created_cases: list[Case] = field(default_factory=list)
    created_organizations: list[Organization] = field(default_factory=list)
    created_documents: list[Document] = field(default_factory=list)
    updated_entities: list[Any] = field(default_factory=list)
    pending_candidates: list[LearningCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def created_count(self):
        return sum(len(items) for items in (
            self.created_clients,
            self.created_cases,
            self.created_organizations,
            self.created_documents,
        ))
