"""
Second Chair

Módulo:
Context

Archivo:
engine.py

Responsabilidad:
Construir el contexto de trabajo.
"""

from models.event import Event

from context.parser import (
    extract_case,
    extract_pdf
)


def enrich(event: Event):

    event.case = extract_case(event.title)

    event.document = extract_pdf(event.title)

    return event