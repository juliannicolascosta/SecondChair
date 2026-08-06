"""Public API for SecondChair's in-memory domain layer."""

from src.domain.entities import (
    Case,
    Client,
    Document,
    Organization,
    Person,
    Workspace,
)
from src.domain.registry import DomainRegistry
from src.domain.resolver import DomainResolution, DomainResolver
from src.domain.candidates import LearningCandidate, LearningResult
from src.domain.learner import DomainLearner

__all__ = [
    "Case",
    "Client",
    "Document",
    "DomainRegistry",
    "DomainResolution",
    "DomainResolver",
    "DomainLearner",
    "LearningCandidate",
    "LearningResult",
    "Organization",
    "Person",
    "Workspace",
]
