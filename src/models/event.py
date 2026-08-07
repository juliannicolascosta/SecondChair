"""
Second Chair

Módulo:
Models

Archivo:
event.py

Responsabilidad:
Representar un evento de actividad del usuario.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Event:

    application: str

    title: str

    start_time: datetime | None = None

    end_time: datetime | None = None

    duration: int = 0

    client: str | None = None

    case: str | None = None

    section: str | None = None

    project: str | None = None

    document: str | None = None

    activity_type: str | None = None

    context_source: str | None = None

    context_confidence: float | None = None

    context_confirmed: bool = False

    context: dict = field(default_factory=dict)
