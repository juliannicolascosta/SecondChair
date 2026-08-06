"""The only component authorized to add unique entities to a Workspace."""

import re

from src.domain.entities import Case, Client, Document, Organization, Person
from src.domain.relations import relate_client_case
from src.domain.workspace import create_workspace


def normalize_identity(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Domain entity names must be non-empty strings")

    return re.sub(r"\s+", " ", value).strip().casefold()


class DomainRegistry:
    def __init__(self, workspace=None):
        self.workspace = workspace or create_workspace()
        self._clients = self._index(self.workspace.clients)
        self._cases = self._index(self.workspace.cases)
        self._organizations = self._index(self.workspace.organizations)
        self._persons = self._index(self.workspace.persons)
        self._documents = self._index(self.workspace.documents)
        self._refresh_statistics()

    def obtener_o_crear_cliente(self, name):
        return self._get_or_create(name, self._clients, self.workspace.clients, Client)

    def obtener_o_crear_expediente(self, name, client=None):
        case = self._get_or_create(name, self._cases, self.workspace.cases, Case)

        if client is not None:
            relate_client_case(client, case)

        return case

    def obtener_o_crear_empresa(self, name):
        return self._get_or_create(
            name,
            self._organizations,
            self.workspace.organizations,
            Organization,
        )

    def obtener_o_crear_persona(self, name):
        return self._get_or_create(name, self._persons, self.workspace.persons, Person)

    def obtener_o_crear_documento(self, name, path=None):
        document = self._get_or_create(
            name,
            self._documents,
            self.workspace.documents,
            Document,
        )

        if document.path is None and path is not None:
            document.path = path

        return document

    def find_client(self, name):
        return self._find(name, self._clients)

    def find_case(self, name):
        return self._find(name, self._cases)

    def find_organization(self, name):
        return self._find(name, self._organizations)

    def find_person(self, name):
        return self._find(name, self._persons)

    def find_document(self, name):
        return self._find(name, self._documents)

    @staticmethod
    def _index(entities):
        index = {}
        for entity in entities:
            key = normalize_identity(entity.name)
            if key in index:
                raise ValueError(f"Duplicate domain entity: {entity.name}")
            index[key] = entity
        return index

    def _get_or_create(self, name, index, collection, entity_type):
        key = normalize_identity(name)
        entity = index.get(key)

        if entity is None:
            entity = entity_type(name=name.strip())
            index[key] = entity
            collection.append(entity)
            self._refresh_statistics()

        return entity

    @staticmethod
    def _find(name, index):
        if not name:
            return None
        return index.get(normalize_identity(name))

    def _refresh_statistics(self):
        self.workspace.statistics.update({
            "clients": len(self.workspace.clients),
            "cases": len(self.workspace.cases),
            "organizations": len(self.workspace.organizations),
            "persons": len(self.workspace.persons),
            "documents": len(self.workspace.documents),
        })
