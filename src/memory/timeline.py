"""
Second Chair

Módulo:
Memory

Archivo:
timeline.py

Responsabilidad:
Mantener el historial de sesiones.
"""

from src.memory.session import Session


class Timeline:

    def __init__(self):

        self.sessions = []

    def add_session(self, session: Session):

        self.sessions.append(session)

    def current_session(self):

        if not self.sessions:

            return None

        return self.sessions[-1]