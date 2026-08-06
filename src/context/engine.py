"""
Second Chair

Módulo:
Context

Archivo:
engine.py

Responsabilidad:
Enriquecer eventos con contexto.
"""

from src.context.parser import parse


def enrich(event):

    context = parse(event)

    event.context = context

    event.section = context.get("section")
    event.client = context.get("client")
    event.case = context.get("case")
    event.project = context.get("project")
    event.document = context.get("document")

    return event
