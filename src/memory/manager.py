"""
Second Chair

Módulo:
Memory

Archivo:
manager.py

Responsabilidad:
Administrar las sesiones de trabajo.
"""

from datetime import datetime

from src.memory.session import Session
from src.memory.timeline import Timeline


class MemoryManager:

    def __init__(self):

        self.timeline = Timeline()

        self.current = None

    def register(self, event):

        if self.current is None:

            self.current = Session(
                start_time=datetime.now()
            )

            self.timeline.add_session(
                self.current
            )

        self.current.add_event(event)

    def finish(self):

        if self.current:

            self.current.end_time = datetime.now()