"""
Second Chair

Módulo:
Models

Archivo:
event.py

Responsabilidad:
Representar un evento de actividad del usuario.
"""

from dataclasses import dataclass
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

    document: str | None = None