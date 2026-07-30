"""
Second Chair

Módulo:
Context

Archivo:
engine.py

Responsabilidad:
Enriquecer eventos con información contextual.
"""

from src.models.event import Event
from src.context.parser import extract_case, extract_pdf


def enrich(event: Event):

    event.case = extract_case(event.title)

    event.document = extract_pdf(event.title)

    return event