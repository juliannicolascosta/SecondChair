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

__all__ = [
    "Case",
    "Client",
    "Document",
    "DomainRegistry",
    "DomainResolution",
    "DomainResolver",
    "Organization",
    "Person",
    "Workspace",
]
