"""Domain entities. They are deliberately independent from persistence."""

from dataclasses import dataclass, field
from uuid import uuid4


def _new_id():
    return str(uuid4())


@dataclass(eq=False)
class Client:
    name: str
    id: str = field(default_factory=_new_id)
    cases: list["Case"] = field(default_factory=list, repr=False)


@dataclass(eq=False)
class Organization:
    name: str
    id: str = field(default_factory=_new_id)
    cases: list["Case"] = field(default_factory=list, repr=False)


@dataclass(eq=False)
class Person:
    name: str
    id: str = field(default_factory=_new_id)
    cases: list["Case"] = field(default_factory=list, repr=False)


@dataclass(eq=False)
class Document:
    name: str
    id: str = field(default_factory=_new_id)
    path: str | None = None
    cases: list["Case"] = field(default_factory=list, repr=False)


@dataclass(eq=False)
class Case:
    name: str
    id: str = field(default_factory=_new_id)
    client: Client | None = None
    documents: list[Document] = field(default_factory=list, repr=False)
    organizations: list[Organization] = field(default_factory=list, repr=False)
    persons: list[Person] = field(default_factory=list, repr=False)


@dataclass
class Workspace:
    clients: list[Client] = field(default_factory=list)
    cases: list[Case] = field(default_factory=list)
    organizations: list[Organization] = field(default_factory=list)
    persons: list[Person] = field(default_factory=list)
    documents: list[Document] = field(default_factory=list)
    statistics: dict[str, int] = field(default_factory=dict)
