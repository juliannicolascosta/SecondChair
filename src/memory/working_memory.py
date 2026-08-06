"""Working memory for completed events and today's WorkSession objects."""

from collections import deque

from src.memory.session_builder import SessionBuilder


class WorkingMemory:
    def __init__(self, max_events=100, session_builder=None):
        self.events = deque(maxlen=max_events)
        self.session_builder = session_builder or SessionBuilder()
        self.sessions = []

    @property
    def current_session(self):
        return self.session_builder.current_session

    def register(self, event):
        self.events.append(event)
        closed_session = self.session_builder.add_event(event)

        if closed_session is not None:
            self.sessions.append(closed_session)

    def last(self):
        if not self.events:
            return None
        return self.events[-1]

    def all(self):
        return list(self.events)

    def finish(self):
        closed_session = self.session_builder.finish()

        if closed_session is not None:
            self.sessions.append(closed_session)

        return closed_session
