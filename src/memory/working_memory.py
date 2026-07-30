"""
Second Chair

Módulo:
Memory

Archivo:
working_memory.py

Responsabilidad:
Mantener una memoria de trabajo de la sesión actual.
"""

from collections import deque


class WorkingMemory:

    def __init__(self, max_events=100):

        self.events = deque(maxlen=max_events)

    def register(self, event):

        self.events.append(event)

    def last(self):

        if not self.events:
            return None

        return self.events[-1]

    def all(self):

        return list(self.events)

    def finish(self):

        pass