import unittest

from src.domain.entities import Case, Client, Document, Organization, Person, Workspace
from src.domain.registry import DomainRegistry
from src.domain.relations import (
    relate_case_document,
    relate_case_organization,
    relate_case_person,
    relate_client_case,
)
from src.domain.resolver import DomainResolver
from src.domain.workspace import create_workspace


class DomainRegistryTests(unittest.TestCase):

    def test_registry_guarantees_normalized_uniqueness(self):
        registry = DomainRegistry()

        first = registry.obtener_o_crear_cliente("Client Alpha")
        second = registry.obtener_o_crear_cliente("  client   ALPHA ")

        self.assertIs(first, second)
        self.assertEqual(len(registry.workspace.clients), 1)

    def test_registry_creates_every_supported_entity(self):
        registry = DomainRegistry()
        client = registry.obtener_o_crear_cliente("Client Alpha")
        case = registry.obtener_o_crear_expediente("Case 001", client)
        organization = registry.obtener_o_crear_empresa("Organization Alpha")
        person = registry.obtener_o_crear_persona("Person Alpha")
        document = registry.obtener_o_crear_documento(
            "Document Alpha",
            path="synthetic/document.pdf",
        )

        self.assertIs(case.client, client)
        self.assertIn(case, client.cases)
        self.assertEqual(document.path, "synthetic/document.pdf")
        self.assertEqual(registry.workspace.statistics, {
            "clients": 1,
            "cases": 1,
            "organizations": 1,
            "persons": 1,
            "documents": 1,
        })
        self.assertIs(registry.find_organization("organization alpha"), organization)
        self.assertIs(registry.find_person("PERSON ALPHA"), person)

    def test_registry_rejects_duplicate_seed_workspace(self):
        workspace = Workspace(
            clients=[Client("Duplicate"), Client(" duplicate ")]
        )

        with self.assertRaises(ValueError):
            DomainRegistry(workspace)


class DomainRelationsTests(unittest.TestCase):

    def test_relations_are_bidirectional_and_idempotent(self):
        client = Client("Client Alpha")
        case = Case("Case 001")
        document = Document("Document Alpha")
        organization = Organization("Organization Alpha")
        person = Person("Person Alpha")

        relate_client_case(client, case)
        relate_client_case(client, case)
        relate_case_document(case, document)
        relate_case_document(case, document)
        relate_case_organization(case, organization)
        relate_case_organization(case, organization)
        relate_case_person(case, person)
        relate_case_person(case, person)

        self.assertEqual(client.cases, [case])
        self.assertEqual(case.documents, [document])
        self.assertEqual(document.cases, [case])
        self.assertEqual(case.organizations, [organization])
        self.assertEqual(organization.cases, [case])
        self.assertEqual(case.persons, [person])
        self.assertEqual(person.cases, [case])

    def test_case_cannot_be_assigned_to_two_clients(self):
        case = Case("Case 001")
        relate_client_case(Client("Client Alpha"), case)

        with self.assertRaises(ValueError):
            relate_client_case(Client("Client Beta"), case)


class DomainResolverTests(unittest.TestCase):

    def test_resolver_supports_parser_and_spanish_keys(self):
        resolution = DomainResolver().resolve({
            "cliente": "Client Alpha",
            "case": "Case 001",
            "empresa": "Organization Alpha",
            "document": "Document Alpha",
        })

        self.assertEqual(resolution.client.name, "Client Alpha")
        self.assertEqual(resolution.case.name, "Case 001")
        self.assertEqual(resolution.organization.name, "Organization Alpha")
        self.assertEqual(resolution.document.name, "Document Alpha")
        self.assertEqual(set(resolution.detected), {
            "client", "case", "organization", "document"
        })

    def test_resolver_does_not_mutate_registry(self):
        registry = DomainRegistry()
        known = registry.obtener_o_crear_cliente("Known Client")
        before = dict(registry.workspace.statistics)

        resolution = DomainResolver(registry).resolve({
            "client": "Known Client",
            "case": "Unregistered Case",
        })

        self.assertIs(resolution.client, known)
        self.assertEqual(resolution.case.name, "Unregistered Case")
        self.assertEqual(registry.workspace.statistics, before)
        self.assertEqual(registry.workspace.cases, [])


class WorkspaceTests(unittest.TestCase):

    def test_workspace_starts_empty_and_in_memory(self):
        workspace = create_workspace()

        self.assertEqual(workspace.clients, [])
        self.assertEqual(workspace.cases, [])
        self.assertEqual(workspace.organizations, [])
        self.assertEqual(workspace.persons, [])
        self.assertEqual(workspace.documents, [])
        self.assertTrue(all(value == 0 for value in workspace.statistics.values()))


if __name__ == "__main__":
    unittest.main()
