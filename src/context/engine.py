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

    return event