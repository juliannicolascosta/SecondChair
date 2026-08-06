"""Explicit bidirectional relations between domain entities."""


def _append_unique(collection, entity):
    if all(existing.id != entity.id for existing in collection):
        collection.append(entity)


def relate_client_case(client, case):
    if case.client is not None and case.client.id != client.id:
        raise ValueError("A case cannot belong to two clients")

    case.client = client
    _append_unique(client.cases, case)


def relate_case_document(case, document):
    _append_unique(case.documents, document)
    _append_unique(document.cases, case)


def relate_case_organization(case, organization):
    _append_unique(case.organizations, organization)
    _append_unique(organization.cases, case)


def relate_case_person(case, person):
    _append_unique(case.persons, person)
    _append_unique(person.cases, case)
