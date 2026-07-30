"""
Second Chair

Módulo:
Memory

Archivo:
session.py

Responsabilidad:
Representar una sesión de trabajo compuesta por múltiples eventos.
"""

from dataclasses import dataclass, field
from datetime import datetime
from src.models.event import Event


@dataclass
class Session:

    start_time: datetime

    end_time: datetime | None = None

    events: list[Event] = field(default_factory=list)

    def add_event(self, event: Event):

        self.events.append(event)

    @property
    def duration(self):

        if self.end_time is None:

            return 0

        return int(
            (self.end_time - self.start_time).total_seconds()
        )